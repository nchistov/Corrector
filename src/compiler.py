from parser import Parser
from errors import CorrectorSyntaxError
import stack_elements as stackelems


class Compiler:
    def __init__(self):
        self.bytecode = bytearray()

        self.procedures = {}
        self.tags = []
        self.stack = []

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
            self.handle(tok)

        if self.stack:
            raise CorrectorSyntaxError('Незавершённый блок!')

        self.compose()
        return self.bytecode

    def handle(self, tok):
        if not self.stack:
            if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                self.stack.append(stackelems.Procedure('', -1))
            else:
                raise CorrectorSyntaxError('На внешнем уровне программы не должно быть команд')
        else:
            match self.stack[-1]:
                case stackelems.Procedure:
                    self.handle_procedure(tok, self.stack[-1])
                case stackelems.WriteCommand:
                    self.handle_symbol(tok, self.stack[-1])
                case stackelems.If:
                    self.handle_if(tok, self.stack[-1])
                case stackelems.CodeBlock:
                    self.handle_code_block(tok, self.stack[-1])

    def _add_tag(self, name: str = None) -> int:
        tag_id = len(self.procedures)
        if name:
            self.procedures[name] = tag_id
        self.tags.append(bytearray())

        return tag_id

    def handle_end(self):
        self.tags[self.stack.pop().tag].append(0x0D)

    def handle_procedure(self, tok, state):
        if not state.name:
            if tok.type == 'WORD':
                state.name = tok.value
                tag = self._add_tag(tok.value)
                state.tag = tag
            else:
                raise CorrectorSyntaxError(f'Ожидалось имя процедуры, получено: {tok.type}')
        else:
            self.handle_command(tok, state)

    def handle_if(self, tok, state):
        if not state.code_block:
            if state.check == -1:
                if not state.no:
                    if tok.value == 'НЕ':
                        state.no = True
                if tok.type == 'CHECK':
                    self.handle_check(tok.value)
                    state.check = tok.value
                elif tok.type == 'SYMBOL':
                    self.handle_symbol_check(tok.value)
                    state.symbol_check = True
                    state.check = tok.value
            else:
                if tok.value == 'ТО':
                    if state.no:
                        self.tags[state.tag].append(0x11)  # BOOL_NOT
                    self.tags[state.tag].extend((0x0E, len(self.tags)))  # len(self.tags), but not - 1 -- new tag.
                    state.code_block = True
                    self.stack.append(stackelems.CodeBlock(False, False, self._add_tag()))
        else:
            self.stack.pop()
            self.handle(tok)

    def handle_command(self, tok, state):
        if tok.type == 'KEYWORD':
            match tok.value:
                case 'КОНЕЦ':
                    if state == stackelems.Procedure:
                        self.handle_end()
                    else:
                        raise CorrectorSyntaxError('Неожиданное ключевое слово КОНЕЦ')
                case 'ЕСЛИ':
                    self.stack.append(stackelems.If(False, False, -1, state.tag, False, False, -1))
                case _:
                    raise CorrectorSyntaxError(f'Неожиданное ключевое слово {tok.value}')
        elif tok.type == "COMMAND":
            if tok.value == 'ПИШИ':
                self.stack.append(stackelems.WriteCommand(state.tag))
            else:
                self.tags[state.tag].extend(self.commands[tok.value])
        elif tok.type == "WORD":
            if tok.value in self.procedures.keys():
                self.handle_procedure_call(tok.value)
            else:
                raise CorrectorSyntaxError(f'Не определена процедура с именем {tok.value}')

    def handle_code_block(self, tok, state):
        if not state.started:
            if tok.type in ('COMMAND', 'WORD'):
                self.handle_command(tok, state)
            elif tok.type == 'SYMBOL' and tok.value == 56:  # {
                state.multiline = True
            else:
                raise CorrectorSyntaxError(f'Неожиданный токен {tok.value}')
            state.started = True
        else:
            if state.multiline:
                if tok.type in ('COMMAND', 'WORD'):
                    self.handle_command(tok, state)
                elif tok.type == 'SYMBOL' and tok.value == 57:  # }
                    self.handle_end()
                else:
                    raise CorrectorSyntaxError(f'Неожиданный токен {tok.value}')
            else:
                self.handle_end()
                self.handle(tok)

    def handle_symbol(self, tok, state):
        if tok.type == 'SYMBOL':
            self.tags[state.tag].extend((0x03, tok.value))
            self.tags[state.tag].append(0x09)
            self.stack.pop()
        else:
            raise CorrectorSyntaxError('Ожидался символ')

    def handle_procedure_call(self, name: str):
        self.tags[self.stack[-1].tag].append(0x02)
        self.tags[self.stack[-1].tag].append(self.procedures[name])
        self.tags[self.stack[-1].tag].append(0x0D)

    def handle_check(self, name):
        self.tags[self.stack[-1].tag].extend(self.checks[name])

    def handle_symbol_check(self, symbol):
        self.tags[self.stack[-1].tag].extend((0x03, symbol, 0x0A, 0x04, 0x01))

    def compose(self):
        for tag_id, tag_bytecode in enumerate(self.tags):
            self.bytecode.extend((0x00, tag_id))
            self.bytecode.extend(tag_bytecode)

if __name__ == '__main__':
    c = Compiler()
    bc = c.compile('ЭТО Программа ЕСЛИ НЕ А ТО ВЛЕВО КОНЕЦ')
    for i in bc:
        print(hex(i), end=' ')
