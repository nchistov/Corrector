from parser import Parser
from errors import CorrectorSyntaxError
import stack_elements as stackelems


class Compiler:
    def __init__(self):
        self.bytecode = bytearray()

        self.procedures = {}
        self.tags = []
        self.tags_stack = []
        self.states_stack = []

        self.commands = {
            'ВПРАВО': (0x05,), 'ВЛЕВО': (0x06,), 'ЯЩИК+': (0x0A, 0x07),
            'ЯЩИК-': (0x08, 0x09), 'ОБМЕН': (0x08, 0x0A, 0x07, 0x09), 'ПЛЮС': (0x0A, 0x0B, 0x09),
            'МИНУС': (0x0A, 0x0C, 0x09), 'СТОЯТЬ': ()
        }
        self.checks = {'Я=Л': (0x0A, 0x08, 0x04, 0x01), 'Я>Л': (0x0A, 0x08, 0x04, 0x02),
                       'Я<Л': (0x0A, 0x08, 0x04, 0x03), 'Я#Л': (0x0A, 0x08, 0x04, 0x04)}

        self.parser = Parser()

    def compile(self, code):
        for tok in self.parser.parse(code):
            if not self.states_stack:
                if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                    self.states_stack.append(stackelems.Procedure('', -1))
                else:
                    raise CorrectorSyntaxError('На внешнем уровне программы не должно быть команд')
            else:
                match self.states_stack[-1]:
                    case stackelems.Procedure:
                        self.handle_procedure(tok)
                    case stackelems.WriteCommand:
                        self.handle_symbol(tok)
                    case stackelems.If:
                        self.handle_if(tok)

        if self.states_stack:
            raise CorrectorSyntaxError('Незавершённый блок!')

        self.compose()
        return self.bytecode

    def _add_tag(self, name: str = None) -> int:
        tag_id = len(self.procedures)
        if name:
            self.procedures[name] = tag_id
        self.tags.append(bytearray())

        return tag_id

    def handle_procedure(self, tok):
        if not self.states_stack[-1].name:
            if tok.type == 'WORD':
                self.states_stack[-1].name = tok.value
                tag = self._add_tag(tok.value)
                self.tags_stack.append(tag)
                self.states_stack[-1].tag = tag
            else:
                raise CorrectorSyntaxError(f'Ожидалось имя процедуры, получено: {tok.type}')
        else:
            self.handle_command(tok)

    def handle_if(self, tok):
        if self.states_stack[-1].tag == -1:
            if self.states_stack[-1].check == -1:
                if not self.states_stack[-1].no:
                    if tok.value == 'НЕ':
                        self.states_stack[-1].no = True
                if tok.type == 'CHECK':
                    self.handle_check(tok.value)
                    self.states_stack[-1].check = tok.value
                elif tok.type == 'SYMBOL':
                    self.handle_symbol_check(tok.value)
                    self.states_stack[-1].symbol_check = True
                    self.states_stack[-1].check = tok.value
            else:
                if tok.value == 'ТО':
                    self.tags[self.tags_stack[-1]].extend((0x0E, len(self.tags)-1))
                    self.tags_stack.append(len(self.tags)-1)
                    if self.states_stack[-1].no:
                        self.tags[self.tags_stack[-1]].append(0x11)  # BOOL_NOT
                    self.states_stack[-1].tag = self.tags_stack[-1]
        else:
            if self.states_stack[-1].oneline_end:
                self.handle_end()

            self.states_stack[-1].oneline_end = True
            self.handle_command(tok)

    def handle_end(self):
        self.tags[self.tags_stack.pop()].append(0x0D)

        self.states_stack.pop()

    def handle_command(self, tok):
        if tok.type == 'KEYWORD':
            match tok.value:
                case 'КОНЕЦ':
                    if stackelems.Procedure == self.states_stack[-1]:
                        self.handle_end()
                    else:
                        raise CorrectorSyntaxError('Неожиданное ключевое слово КОНЕЦ')
                case 'ЕСЛИ':
                    self.states_stack.append(stackelems.If(False, False, -1, False, False, -1, False, -1))
                case _:
                    raise CorrectorSyntaxError(f'Неожиданное ключевое слово {tok.value}')
        elif tok.type == "COMMAND":
            if tok.value == 'ПИШИ':
                self.states_stack.append(stackelems.WriteCommand)
            else:
                self.tags[self.tags_stack[-1]].extend(self.commands[tok.value])
        elif tok.type == "WORD":
            if tok.value in self.procedures.keys():
                self.handle_procedure_call(tok.value)
            else:
                raise CorrectorSyntaxError(f'Не определена процедура с именем {tok.value}')

    def handle_symbol(self, tok):
        if tok.type == 'SYMBOL':
            self.tags[self.tags_stack[-1]].extend((0x03, tok.value))
            self.tags[self.tags_stack[-1]].append(0x09)
            self.states_stack.pop()
        else:
            raise CorrectorSyntaxError('Ожидался символ')

    def handle_procedure_call(self, name: str):
        self.tags[self.tags_stack[-1]].append(0x02)
        self.tags[self.tags_stack[-1]].append(self.procedures[name])
        self.tags[self.tags_stack[-1]].append(0x0D)

    def handle_check(self, name):
        self.tags[self.tags_stack[-1]].extend(self.checks[name])
        self._add_tag()

    def handle_symbol_check(self, symbol):
        self.tags[self.tags_stack[-1]].extend((0x03, symbol, 0x0A, 0x04, 0x01))
        self._add_tag()

    def compose(self):
        for tag_id, tag_bytecode in enumerate(self.tags):
            self.bytecode.extend((0x00, tag_id))
            self.bytecode.extend(tag_bytecode)

if __name__ == '__main__':
    c = Compiler()
    bc = c.compile('ЭТО Программа ЕСЛИ А ТО ВЛЕВО КОНЕЦ')
    for i in bc:
        print(hex(i), end=' ')
