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

from src import errors


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

    def run(self, bytecode: bytearray, command: bytearray):
        self.startup(bytecode)

        if command:
            self.position = len(bytecode)
            command.append(0x0D)
            bytecode.extend(command)
        else:
            return
        self.running = True
        while self.running:
            print(hex(bytecode[self.position]))
            if bytecode[self.position] in (0x02, 0x03, 0x04, 0x0E):
                self._run_command(bytecode[self.position], bytecode[self.position+1])
                self.position += 2
            elif bytecode[self.position] == 0x0F:
                self._run_command(bytecode[self.position], bytecode[self.position+1], bytecode[self.position+2])
                self.position += 3
            else:
                self._run_command(bytecode[self.position])
                self.position += 1

    def startup(self, bytecode: bytearray):
        for pos, byte in enumerate(bytecode):
            if byte == 0x00:
                self.add_tag(bytecode[pos + 1], pos + 2)

    def add_tag(self, tag_id: int, pos: int):
        self.tags[tag_id] = pos

    def _run_command(self, command: int, *args):
        match command:
            case 0x02:
                self.stack.append(self.tags[args[0]])
            case 0x03:
                self.stack.append(args[0])
            case 0x04:
                match args[0]:
                    case 0x01:
                        self.stack.append(self.stack.pop() == self.stack.pop())
                    case 0x02:
                        self.stack.append(self.stack.pop() > self.stack.pop())
                    case 0x03:
                        self.stack.append(self.stack.pop() < self.stack.pop())
                    case 0x04:
                        self.stack.append(self.stack.pop() != self.stack.pop())
            case 0x05:
                self.tape.move_right()
            case 0x06:
                self.tape.move_left()
            case 0x07:
                self.box = self.stack.pop()
            case 0x08:
                self.stack.append(self.box)
            case 0x09:
                self.tape.set(self.stack.pop())
            case 0x0A:
                self.stack.append(self.tape.get())
            case 0x0B:
                s = self.stack.pop()
                if s == 71:
                    raise errors.CorrectorCannotError('Не могу!')
                self.stack.append(s + 1)
            case 0x0C:
                s = self.stack.pop()
                if s == 0:
                    raise errors.CorrectorCannotError('Не могу!')
                self.stack.append(s - 1)
            case 0x0D:
                self._pop_jump()
            case 0x0E:
                if self.stack.pop():
                    self._jump(args[0], self.position + len(args) + 1)
            case 0x0F:
                if self.stack.pop():
                    self._jump(args[0], self.position + len(args) + 1)
                else:
                    self._jump(args[1], self.position + len(args) + 1)

    def _jump(self, tag_id: int, position: int):
        self.stack.append(position)
        self.position = self.tags[tag_id]

    def _pop_jump(self):
        if self.stack:
            self.position = self.stack.pop()
        else:
            self.running = False


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

vm = Vm()
bc = bytearray(bytes((0x00, 0x00, 0x03, 0x04, 0x09, 0x0D)))
command = bytearray(bytes((0x02, 0x00, 0x0D)))

vm.run(bc, command)
print(vm.stack)
print(vm.tape.get())
