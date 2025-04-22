from enum import Enum

from parser import Parser
from errors import CorrectorSyntaxError

class WaitingFor(Enum):
    Procedure = 0
    ProcedureName = 1
    Command = 2
    Symbol = 3
    Check = 4
    Number = 5


class Compiler:
    def __init__(self):
        self.bytecode = bytearray()
        self.state = WaitingFor.Procedure

        self.procedures = {}
        self.tags = {}
        self.parser = Parser()
        self.stack = []
        self.commands = {
            'ВПРАВО': (0x05,), 'ВЛЕВО': (0x06,), 'ПИШИ': 0x09, 'ЯЩИК+': (0x0A, 0x07),  # TODO: write ПИШИ realisation
            'ЯЩИК-': (0x08, 0x09), 'ОБМЕН': (0x08, 0x0A, 0x07, 0x09), 'ПЛЮС': (0x0A, 0x0B, 0x09),
            'МИНУС': (0x0A, 0x0C, 0x09), 'СТОЯТЬ': ()
        }

    def compile(self, code):
        for tok in self.parser.parse(code):
            match self.state:
                case WaitingFor.Procedure:
                    if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                        self.state = WaitingFor.ProcedureName
                    else:
                        raise CorrectorSyntaxError('На внешнем уровне программы не должно быть команд')
                case WaitingFor.ProcedureName:
                    if tok.type == 'WORD':
                        self.handle_procedure(tok.value)
                    else:
                        raise CorrectorSyntaxError(f'Ожидалось имя процедуры, получено: {tok.type}')
                case WaitingFor.Command:
                    if tok.type == 'KEYWORD':
                        match tok.value:
                            case 'КОНЕЦ':
                                self.handle_end()
                            case _:
                                ...
                    elif tok.type == "COMMAND":
                        self.handle_command(tok.value)
                    elif tok.type == "WORD":
                        if tok.value in self.procedures.keys():
                            self.handle_procedure_call(tok.value)
                case WaitingFor.Number:
                    ...
                case WaitingFor.Symbol:
                    if tok.type == 'SYMBOL':
                        self.handle_symbol(tok.value)
                    else:
                        raise CorrectorSyntaxError('Ожидался символ')

        self.compose()
        return self.bytecode

    def handle_procedure(self, name):
        tag_id = len(self.procedures)
        self.procedures[name] = tag_id
        self.tags[tag_id] = bytearray()
        self.state = WaitingFor.Command
        self.stack.append(tag_id)

    def handle_end(self):
        self.tags[self.stack.pop()].append(0x0D)

        if len(self.stack) == 0:
            self.state = WaitingFor.Procedure
        else:
            self.state = WaitingFor.Command

    def handle_command(self, name):
        self.tags[self.stack[-1]].extend(self.commands[name])
        if name == 'ПИШИ':
            self.state = WaitingFor.Symbol

    def handle_symbol(self, symbol):
        self.tags[self.stack[-1]].extend(symbol)
        self.state = WaitingFor.Command

    def handle_procedure_call(self, name: str):
        self.tags[self.stack[-1]].append(0x02)
        self.tags[self.stack[-1]].append(self.procedures[name])
        self.tags[self.stack[-1]].append(0x0D)

    def compose(self):
        for tag_id, tag_bytecode in self.tags.items():
            self.bytecode.extend((0x00, tag_id))
            self.bytecode.extend(tag_bytecode)

c = Compiler()
bc = c.compile('ЭТО Программа ВЛЕВО ОБМЕН КОНЕЦ')
for i in bc:
    print(hex(i), end=' ')
