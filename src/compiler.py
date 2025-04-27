from .parser import Parser
from .errors import CorrectorSyntaxError
from . import stack_elements as stackelems


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
                       'Я<Л': (0x0A, 0x08, 0x04, 0x03), 'Я#Л': (0x0A, 0x08, 0x04, 0x04),
                       'ЦИФРА': (0x0A, 0x12)}

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
                case stackelems.ForLoop:
                    self.handle_for(tok, self.stack[-1])
                case stackelems.WhileLoop:
                    self.handle_while(tok, self.stack[-1])
                case stackelems.CodeBlock:
                    self.handle_code_block(tok, self.stack[-1])

    def _add_tag(self, name: str = None) -> int:
        tag_id = len(self.tags)
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
                self.handle_check(tok, state)
            else:
                if tok.value == 'ТО':
                    if state.no:
                        self.tags[state.tag].append(0x11)  # BOOL_NOT
                    self.tags[state.tag].extend((0x0E, len(self.tags)))  # len(self.tags), but not - 1 -- new tag.
                    state.code_block = True
                    self.stack.append(stackelems.CodeBlock(False, False, self._add_tag()))
        else:
            if tok.value == 'ИНАЧЕ':
                if not state.else_check:
                    if_tag = self.tags[state.tag][-1]  # Last element of a bytecode
                    else_tag = self._add_tag()
                    self.tags[state.tag] = self.tags[state.tag][:-2]  # Removing POP_JUMP_IF <tag>
                    self.tags[state.tag].extend((0x0F, if_tag, else_tag))  # POP_JUMP_IF_ELSE <if_tag> <else_tag>
                    self.stack.append(stackelems.CodeBlock(False, False, else_tag))
                    state.else_check = True
                else:
                    raise CorrectorSyntaxError('Недопустимые два блока ИНАЧЕ')
            else:
                self.stack.pop()
                self.handle(tok)

    def handle_while(self, tok, state):
        # LOAD_TAG 1
        # POP_JUMP
        # TAG 1
        # <CHECK> THEN JUMP 2
        # POP_JUMP
        # TAG 2
        # <BODY>
        # JUMP 1
        if not state.code_block:
            if state.check == -1:
                if not state.no:  # On start
                    self.tags[state.tag].extend((0x02, len(self.tags), 0x0D))
                    state.tag = self._add_tag()
                self.handle_check(tok, state)
            else:
                if state.no:
                    self.tags[state.tag].append(0x11)  # BOOL_NOT
                self.tags[state.tag].extend((0x0E, len(self.tags)))  # len(self.tags), but not - 1 -- new tag.
                state.code_block = True
                self.stack.append(stackelems.CodeBlock(False, False, self._add_tag()))
                self.handle(tok)
        else:
            self.tags[-1] = self.tags[-1][:-1]  # Removing ending POP_JUMP
            self.tags[-1].extend((0x02, state.tag, 0x0D, 0x0D))  # Double POP_JUMP: first for while jump, second -- end of block
            self.handle_end()
            self.handle(tok)

    def handle_for(self, tok, state):
        if state.iterations == -1:
            if tok.type == 'SYMBOL':
                if 1 < tok.value < 11:  # No 0 iterations!
                    state.iterations = tok.value - 1
                else:
                    raise CorrectorSyntaxError('Ожидалось кол-во повторений')
            elif tok.type == 'NUMBER':
                state.iterations = tok.value
            else:
                raise CorrectorSyntaxError('Ожидалось кол-во повторений')

            tag = self._add_tag()
            self.tags[state.tag].extend((0x02, tag, 0x0D))
            self.stack.append(stackelems.CodeBlock(False, False, tag))
        else:
            self.tags[-1] = self.tags[-1][:-1] * state.iterations  # Remove POP_JUMP and multiply bytecode
            self.tags[-1].append(0x0D)  # and add POP_JUMP after multiplying
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
                    self.stack.append(stackelems.If(False, False, -1, state.tag, False, False))
                case 'ПОВТОРИ':
                    self.stack.append(stackelems.ForLoop(state.tag, -1))
                case 'ПОКА':
                    self.stack.append(stackelems.WhileLoop(False, False, -1, state.tag, False))
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

    def handle_check(self, tok, state):
        if not state.no:
            if tok.value == 'НЕ':
                state.no = True
        if tok.type == 'CHECK':
            self.tags[state.tag].extend(self.checks[tok.value])
            state.check = tok.value
        elif tok.type == 'SYMBOL':
            self.tags[state.tag].extend((0x03, tok.value, 0x0A, 0x04, 0x01))
            state.symbol_check = True
            state.check = tok.value

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

    def compose(self):
        for tag_id, tag_bytecode in enumerate(self.tags):
            self.bytecode.extend((0x00, tag_id))
            self.bytecode.extend(tag_bytecode)
