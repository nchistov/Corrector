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
        self.indent = 0

        self.procedures = {}
        self.commands = {'ВПРАВО': 0x05,
                         'ВЛЕВО': 0x06,
                         'ПИШИ': 0x07,
                         'ЯЩИК+': 0x08,
                         'ЯЩИК-': 0x09,
                         'ОБМЕН': 0x0A,
                         'ПЛЮС': 0x0B,
                         'МИНУС': 0x0C,
                         'СТОЯТЬ': 0x0D
        }
        self.parser = Parser()

    def compile(self, code) -> bytearray:
        for tok in self.parser.parse(code):
            match self.state:
                case WaitingFor.Procedure:
                    if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                        self.state = WaitingFor.ProcedureName
                    else:
                        raise CorrectorSyntaxError('На внешнем уровне программы не должно быть комманд')
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

        return self.bytecode

    def handle_procedure(self, name):
        self.procedures[name] = len(self.procedures)
        self.bytecode.append(0x00)
        self.bytecode.append(self.procedures[name])
        self.state = WaitingFor.Command
        self.indent += 1

    def handle_end(self):
        self.indent -= 1
        self.bytecode.append(0x01)

        if self.indent == 0:
            self.state = WaitingFor.Procedure
        else:
            self.state = WaitingFor.Command

    def handle_command(self, name):
        self.bytecode.append(self.commands[name])
        if name == 'ПИШИ':
            self.state = WaitingFor.Symbol

    def handle_symbol(self, symbol):
        self.bytecode.append(symbol)
        self.state = WaitingFor.Command

    def handle_procedure_call(self, name: str):
        self.bytecode.append(0x0E)
        self.bytecode.append(self.procedures[name])
