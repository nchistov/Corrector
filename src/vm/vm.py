"""
БАЙТКОД:
Конструкции:
TAG <id> | 0x00 <id> -- начало тега

Команды:
0x02 <tag> -- LOAD_TAG <tag>
0x03 <symbol> -- LOAD_SYMBOL <symbol>
0x04 <op> -- BIN_OP <op> | <op> ::= 0x01 -- equal, 0x02 -- more, 0x03 -- less, 0x04 -- not equal
0x05 -- RIGHT
0x06 -- LEFT
0x07 -- POP_SET_BOX
0x08 -- LOAD_BOX
0x09 -- POP_SET_TAPE
0x0A -- LOAD_TAPE
0x0B -- POP_NEXT_PUSH
0x0C -- POP_PREV_PUSH
0x0D -- POP_JUMP
0x0E <tag> -- POP_JUMP_IF <tag>
0x0F <tag> <tag> -- POP_JUMP_IF_ELSE <tag> <tag>
0x10 -- RETURN
0x11 -- BOOL_NOT
0x12 -- IS_DIGIT
"""
import time

from .. import errors
from .. import bytecode as bc

ByteCommand = tuple[int, int, tuple[int]]
args_num = {0x00: 2, 0x02: 2, 0x03: 1, 0x04: 1, 0x05: 0, 0x06: 0, 0x07: 0, 0x08: 0, 0x09: 0, 0x0A: 0, 0x0B: 0, 0x0C: 0,
        0x0D: 0, 0x0E: 2, 0x0F: 4, 0x10: 0, 0x11: 0, 0x12: 0}
WAIT_TIME = 0.5


class Vm:
    """Виртуальная машина"""
    def __init__(self):
        self.box = 0
        self.tape = Tape()
        self.stack = []
        self.call_stack = []

        self.tags = {}
        self.position = 0
        self.commands: list[ByteCommand] = []

        self.operations = {0x02: self._load_tag,
                           0x03: self._load_symbol,
                           0x04: self._bin_op,
                           0x05: self._right,
                           0x06: self._left,
                           0x07: self._pop_set_box,
                           0x08: self._load_box,
                           0x09: self._pop_set_tape,
                           0x0A: self._load_tape,
                           0x0B: self._pop_next_push,
                           0x0C: self._pop_prev_push,
                           0x0D: self._pop_jump,
                           0x0E: self._pop_jump_if,
                           0x0F: self._pop_jump_if_else,
                           0x10: self._return,
                           0x11: self._bool_not,
                           0x12: self._is_digit,
                           }

    def run(self, bytecode: bytearray, command: bytearray):
        if command:
            self.startup(bytecode, command)
        else:
            return

        while self.position < len(self.commands):
            command = self.commands[self.position]

            self._run_command(command[1], *command[2])

    def startup(self, bytecode: bytearray, command: bytearray):
        self.stack = []
        self.call_stack = []
        self.tags = {}
        self.commands = []

        bytes_iter = iter(bytecode)
        command_iter = iter(command)

        position = 0

        try:
            while True:
                byte = next(bytes_iter)
                command = (0, byte, tuple((next(bytes_iter) for _ in range(args_num[byte]))))

                if command[1] == bc.TAG:  # TAG
                    self.add_tag(_get_number(*command[2]), position)
                else:
                    self.commands.append(command)
                    position += 1
        except StopIteration:
            self.position = position
            try:
                while True:
                    byte = next(command_iter)
                    self.commands.append((0, byte, tuple([next(command_iter) for _ in range(args_num[byte])])))
            except StopIteration:
                return

    def add_tag(self, tag_id: int, pos: int):
        self.tags[tag_id] = pos

    def _run_command(self, command: int, *args):
        self.operations[command](*args)

        if command not in (bc.POP_JUMP, bc.POP_JUMP_IF, bc.POP_JUMP_IF_ELSE, bc.RETURN):  # Не произошло перехода
            self.position += 1

    def _load_tag(self, *args):
        self.stack.append(_get_number(args[0], args[1]))

    def _load_symbol(self, *args):
        self.stack.append(args[0])

    def _bin_op(self, *args):
        match args[0]:
            case bc.EQUAL:
                self.stack.append(self.stack.pop() == self.stack.pop())
            case bc.MORE:
                self.stack.append(self.stack.pop() > self.stack.pop())
            case bc.LESS:
                self.stack.append(self.stack.pop() < self.stack.pop())
            case bc.NOT_EQUAL:
                self.stack.append(self.stack.pop() != self.stack.pop())

    def _right(self):
        self.tape.move_right()

    def _left(self):
        self.tape.move_left()

    def _pop_set_box(self):
        self.box = self.stack.pop()

    def _load_box(self):
        self.stack.append(self.box)

    def _pop_set_tape(self):
        self.tape.set(self.stack.pop())

    def _load_tape(self):
        self.stack.append(self.tape.get())

    def _pop_next_push(self):
        s = self.stack.pop()
        if s == 72:
            raise errors.CorrectorCannotError('Не могу!')
        self.stack.append(s + 1)

    def _pop_prev_push(self):
        s = self.stack.pop()
        if s == 1:
            raise errors.CorrectorCannotError('Не могу!')
        self.stack.append(s - 1)

    def _pop_jump(self):
        self._jump(self.stack.pop(), self.position + 1)

    def _pop_jump_if(self, *args):
        if self.stack.pop():
            self._jump(_get_number(args[0], args[1]), self.position + 1)
        else:
            self.position += 1

    def _pop_jump_if_else(self, *args):
        if self.stack.pop():
            self._jump(_get_number(args[0], args[1]), self.position + 1)
        else:
            self._jump(_get_number(args[2], args[3]), self.position + 1)

    def _return(self):
        self.position = self.call_stack.pop()

    def _bool_not(self):
        self.stack.append(not self.stack.pop())

    def _is_digit(self):
        self.stack.append(1 < self.stack.pop() < 12)  # 0 or 1, 2, 3, 4, 5...

    def _jump(self, tag_id: int, position: int):
        self.call_stack.append(position)
        self.position = self.tags[tag_id]


def _get_number(first_byte: int, second_byte: int) -> int:
    return (first_byte << 8) + second_byte


class Tape:
    """Рабочая лента исполнителя"""
    def __init__(self):
        self.left_data = []
        self.right_data = [0]
        self.position = 0

    def set(self, symbol: int):
        if self.position >= 0:
            self.right_data[self.position] = symbol
        else:
            self.left_data[-self.position-1] = symbol

    def get(self) -> int:
        return self.right_data[self.position] if self.position >= 0 else self.left_data[-self.position-1]

    def move_left(self):
        if self.position < 0  and -self.position == len(self.left_data):
            self.left_data.append(0)
        self.position -= 1

    def move_right(self):
        if self.position == len(self.right_data) - 1:
            self.right_data.append(0)
        self.position += 1

    def get_preview(self):
        for pos in range(self.position-5, self.position+6):
            if pos < 0  and -pos > len(self.left_data):
                yield 0
            elif pos > 0 and pos > len(self.right_data) - 1:
                yield 0
            else:
                yield self.right_data[pos] if pos >= 0 else self.left_data[-pos+1]
