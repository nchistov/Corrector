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
from .. import errors


class Vm:
    """Виртуальная машина"""
    def __init__(self):
        self.box = 0
        self.tape = Tape()
        self.stack = []
        self.call_stack = []

        self.tags = {}
        self.position = 0

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
        self.startup(bytecode)

        if command:
            self.position = len(bytecode)
            bytecode.extend(command)
        else:
            return

        while self.position < len(bytecode):
            byte = bytecode[self.position]

            if byte in (0x02, 0x03, 0x04, 0x0E):
                self._run_command(byte, bytecode[self.position+1])
                if byte != 0x0E: self.position += 2  # Если не произошло перехода
            elif byte == 0x0F:
                self._run_command(byte, bytecode[self.position+1], bytecode[self.position+2])
            else:
                self._run_command(byte)
                if byte != 0x0D: self.position += 1  # Если не произошло перехода

    def startup(self, bytecode: bytearray):
        for pos, byte in enumerate(bytecode):
            if byte == 0x00:
                self.add_tag(bytecode[pos + 1], pos + 2)

    def add_tag(self, tag_id: int, pos: int):
        self.tags[tag_id] = pos

    def _run_command(self, command: int, *args):
        self.operations[command](*args)

    def _load_tag(self, *args):
        self.stack.append(self.tags[args[0]])

    def _load_symbol(self, *args):
        self.stack.append(args[0])

    def _bin_op(self, *args):
        match args[0]:
            case 0x01:
                self.stack.append(self.stack.pop() == self.stack.pop())
            case 0x02:
                self.stack.append(self.stack.pop() > self.stack.pop())
            case 0x03:
                self.stack.append(self.stack.pop() < self.stack.pop())
            case 0x04:
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
            self._jump(args[0], self.position + len(args) + 1)
        else:
            self.position += 2

    def _pop_jump_if_else(self, *args):
        if self.stack.pop():
            self._jump(args[0], self.position + len(args) + 1)
        else:
            self._jump(args[1], self.position + len(args) + 1)

    def _return(self):
        self.position = self.call_stack.pop()

    def _bool_not(self):
        self.stack.append(not self.stack.pop())

    def _is_digit(self):
        self.stack.append(1 < self.stack.pop() < 12)  # 0 or 1, 2, 3, 4, 5...

    def _jump(self, tag_id: int, position: int):
        self.call_stack.append(position)
        self.position = self.tags[tag_id]


class Tape:
    """Рабочая лента исполнителя"""
    def __init__(self):
        self.left_data = []
        self.right_data = [1]
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
            self.left_data.append(1)
        self.position -= 1

    def move_right(self):
        if self.position == len(self.right_data) - 1:
            self.right_data.append(1)
        self.position += 1

    def get_preview(self):
        for pos in range(self.position-5, self.position+6):
            if pos < 0  and -pos > len(self.left_data):
                yield 1
            elif pos > 0 and pos > len(self.right_data) - 1:
                yield 1
            else:
                yield self.right_data[pos] if pos >= 0 else self.left_data[-pos+1]
