from parser import Parser
from errors import CorrectorSyntaxError
from stack_elements import StackElem


class Compiler:
    def __init__(self):
        self.bytecode = bytearray()

        self.procedures = {}
        self.tags = {}
        self.tags_stack = []
        self.states_stack = []

        self.commands = {
            'ВПРАВО': (0x05,), 'ВЛЕВО': (0x06,), 'ЯЩИК+': (0x0A, 0x07),
            'ЯЩИК-': (0x08, 0x09), 'ОБМЕН': (0x08, 0x0A, 0x07, 0x09), 'ПЛЮС': (0x0A, 0x0B, 0x09),
            'МИНУС': (0x0A, 0x0C, 0x09), 'СТОЯТЬ': ()
        }

        self.parser = Parser()

    def compile(self, code):
        for tok in self.parser.parse(code):
            if not self.states_stack:
                if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                    self.states_stack.append(StackElem.Procedure)
                else:
                    raise CorrectorSyntaxError('На внешнем уровне программы не должно быть команд')
            else:
                match self.states_stack[-1]:
                    case StackElem.Procedure:
                        if tok.type == 'WORD':
                            self.handle_procedure(tok.value)
                        else:
                            raise CorrectorSyntaxError(f'Ожидалось имя процедуры, получено: {tok.type}')
                    case StackElem.ProcedureName:
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
                    case StackElem.WriteCommand:
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
        self.states_stack.append(StackElem.ProcedureName)
        self.tags_stack.append(tag_id)

    def handle_end(self):
        self.tags[self.tags_stack.pop()].append(0x0D)

        self.states_stack.pop()

    def handle_command(self, name):
        if name == 'ПИШИ':
            self.states_stack.append(StackElem.WriteCommand)
        else:
            self.tags[self.tags_stack[-1]].extend(self.commands[name])

    def handle_symbol(self, symbol):
        self.tags[self.tags_stack[-1]].extend((0x03, symbol))
        self.tags[self.tags_stack[-1]].append(0x09)
        self.states_stack.pop()

    def handle_procedure_call(self, name: str):
        self.tags[self.tags_stack[-1]].append(0x02)
        self.tags[self.tags_stack[-1]].append(self.procedures[name])
        self.tags[self.tags_stack[-1]].append(0x0D)

    def compose(self):
        for tag_id, tag_bytecode in self.tags.items():
            self.bytecode.extend((0x00, tag_id))
            self.bytecode.extend(tag_bytecode)

if __name__ == '__main__':
    c = Compiler()
    bc = c.compile('ЭТО Программа ПИШИ А КОНЕЦ')
    for i in bc:
        print(hex(i), end=' ')
