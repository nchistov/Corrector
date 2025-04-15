"""
БАЙТКОД:
Конструкции:
0x00 <id> -- определение процедуры
0x02 <check's id> -- проверка
0x03 <check's id> -- цикл пока
0x04 <iteration number> -- цикл повтори
0x01 -- завершение блока

Команды:
0x05 -- ВПРАВО
0x06 -- ВЛЕВО
0x07 <symbol's code> -- ПИШИ <символ>
0x08 -- ЯЩИК+
0x09 -- ЯЩИК-
0x0A -- ОБМЕН
0x0B -- ПЛЮС
0x0C -- МИНУС
0x0D -- СТОЯТЬ
0x0E <id> -- вызвать процедуру <id>

Проверки:
0x00 -- Я=Л
0x01 -- Я>Л
0x02 -- Я<Л
0x03 -- Я#Л
0x04 <symbol's code> -- символ <symbol>
0x05 <symbol's code> -- не символ <symbol>
"""
from enum import Enum


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

        self.procedures = {}
        self.state = WaitingFor.Procedure
        self.position = 0

    def run(self, bytecode: bytearray, command: bytearray):
        self.startup(bytecode)

        self.run_command(command)

    def startup(self, bytecode: bytearray):
        for pos, byte in enumerate(bytecode):
            if byte == 0x00:
                self.add_procedure(bytecode[pos + 1])

            self.position += 1

    def add_procedure(self, id: int):
        self.procedures[id] = self.position + 1

    def run_command(self, command: bytearray):
        match command[0]:
            case 0x05:
                self.tape.move_right()
            case 0x06:
                self.tape.move_left()
            case 0x07:
                self.tape.set(command[1])
            case 0x08:
                self.box = self.tape.get()
            case 0x09:
                self.tape.set(self.box)
            case 0x0A:
                b = self.box
                self.box = self.tape.get()
                self.tape.set(b)
            case 0x0B:
                self.tape.set(self.tape.get() + 1)
            case 0x0C:
                self.tape.set(self.tape.get() - 1)
            case 0x0E:
                ...


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
