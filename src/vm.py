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
0x10 -- END
0x11 -- BOOL_NOT
0x12 -- IS_DIGIT
...

Проверки:
0x00 -- Я=Л
0x01 -- Я>Л
0x02 -- Я<Л
0x03 -- Я#Л
0x04 <symbol's code> -- символ <symbol>
0x05 <symbol's code> -- не символ <symbol>
"""
from enum import Enum

from . import errors


class WaitingFor(Enum):
    Procedure = 0
    ProcedureId = 1
    Command = 2
    Symbol = 3
    Check = 4
    Number = 5


class Vm:
    """Виртуальная машина"""
    def __init__(self):
        self.box = 0
        self.tape = Tape()
        self.stack = []

        self.tags = {}
        self.state = WaitingFor.Procedure
        self.position = 0
        self.running = False

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
                           0x10: self._end,
                           0x11: self._bool_not,
                           0x12: self._is_digit,
                           }

    def run(self, bytecode: bytearray, command: bytearray):
        self.startup(bytecode)

        if command:
            self.position = len(bytecode)
            command.append(0x10)
            bytecode.extend(command)
        else:
            return
        self.running = True
        while self.running:
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

    def _right(self, *args):
        self.tape.move_right()

    def _left(self, *args):
        self.tape.move_left()

    def _pop_set_box(self, *args):
        self.box = self.stack.pop()

    def _load_box(self, *args):
        self.stack.append(self.box)

    def _pop_set_tape(self, *args):
        self.tape.set(self.stack.pop())

    def _load_tape(self, *args):
        self.stack.append(self.tape.get())

    def _pop_next_push(self, *args):
        s = self.stack.pop()
        if s == 71:
            raise errors.CorrectorCannotError('Не могу!')
        self.stack.append(s + 1)

    def _pop_prev_push(self, *args):
        s = self.stack.pop()
        if s == 0:
            raise errors.CorrectorCannotError('Не могу!')
        self.stack.append(s - 1)

    def _pop_jump(self):
        if self.stack:
            self.position = self.stack.pop()
        else:
            self.running = False

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

    def _end(self, *args):
        self.running = False

    def _bool_not(self, *args):
        self.stack.append(not self.stack.pop())

    def _is_digit(self, *args):
        self.stack.append(0 < self.stack.pop() < 11)  # 0 or 1, 2, 3, 4, 5...

    def _jump(self, tag_id: int, position: int):
        self.stack.append(position)
        self.position = self.tags[tag_id]


class Tape:
    """Рабочая лента исполнителя"""
    def __init__(self):
        self.data = [0]
        self.position = 0

    def set(self, symbol: int):
        self.data[self.position] = symbol

    def get(self) -> int:
        return self.data[self.position]

    def move_left(self):
        if self.position == 0:
            self.data.insert(0, 0)
        else:
            self.position -= 1

    def move_right(self):
        if self.position == len(self.data) - 1:
            self.data.append(0)
        self.position += 1
