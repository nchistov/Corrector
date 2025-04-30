from .parser import Parser
from ..errors import CorrectorSyntaxError
from . import stack_elements as stackelems
from ..bytecode import ByteCommand as bc, BinOp as bo


class Compiler:
    def __init__(self):
        self.bytecode = bytearray()

        self.procedures = {}
        self.tags = []
        self.stack = []

        self.commands = {
            'ВПРАВО': (bc.RIGHT,), 'ВЛЕВО': (bc.LEFT,), 'ЯЩИК+': (bc.LOAD_TAPE, bc.POP_SET_BOX),
            'ЯЩИК-': (bc.LOAD_BOX, bc.POP_SET_TAPE),
            'ОБМЕН': (bc.LOAD_BOX, bc.LOAD_TAPE, bc.POP_SET_BOX, bc.POP_SET_TAPE),
            'ПЛЮС': (bc.LOAD_TAPE, bc.POP_NEXT_PUSH, bc.POP_SET_TAPE),
            'МИНУС': (bc.LOAD_TAPE, bc.POP_PREV_PUSH, bc.POP_SET_TAPE), 'СТОЯТЬ': ()
        }
        self.checks = {'Я=Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bo.EQUAL),
                       'Я>Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bo.MORE),
                       'Я<Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bo.LESS),
                       'Я#Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bo.NOT_EQUAL),
                       'ЦИФРА': (bc.LOAD_TAPE, bc.IS_DIGIT)}

        self.parser = Parser()

    def startup(self, code):
        # Reset
        self.bytecode = bytearray()
        self.procedures = {}
        self.tags = []
        self.stack = []

        tokens = self.parser.parse(code)

        try:
            while True:
                tok = next(tokens)
                if tok.value == 'ЭТО':
                    tok = next(tokens)
                    if tok.type == 'WORD' or tok.type == 'SYMBOL':
                        self._add_tag(tok.value)
                    else:
                        raise CorrectorSyntaxError('Ожидалось имя процедуры')
        except StopIteration:
            return

    def compile(self, code):
        self.startup(code)

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
        self.tags[self.stack.pop().tag].append(bc.POP_JUMP)

    def handle_procedure(self, tok, state):
        if not state.name:
            if tok.type == 'WORD' or tok.type == 'SYMBOL':
                state.name = tok.value
                state.tag = self.procedures[state.name]
            else:
                raise CorrectorSyntaxError('Ожидалось имя процедуры')
        else:
            self.handle_command(tok, state)

    def handle_if(self, tok, state):
        if not state.code_block:
            if state.check == -1:
                self.handle_check(tok, state)
            else:
                if tok.value == 'ТО':
                    if state.no:
                        self.tags[state.tag].append(bc.BOOL_NOT)
                    self.tags[state.tag].extend((bc.POP_JUMP_IF, len(self.tags)))  # len(self.tags), but not - 1 -- new tag.
                    state.code_block = True
                    self.stack.append(stackelems.CodeBlock(False, False, self._add_tag()))
        else:
            if tok.value == 'ИНАЧЕ':
                if not state.else_check:
                    if_tag = self.tags[state.tag][-1]  # Last element of a bytecode
                    else_tag = self._add_tag()
                    self.tags[state.tag] = self.tags[state.tag][:-2]  # Removing POP_JUMP_IF <tag>
                    self.tags[state.tag].extend((bc.POP_JUMP_IF_ELSE, if_tag, else_tag))  # POP_JUMP_IF_ELSE <if_tag> <else_tag>
                    self.stack.append(stackelems.CodeBlock(False, False, else_tag))
                    state.else_check = True
                else:
                    raise CorrectorSyntaxError('Недопустимые два блока ИНАЧЕ')
            else:
                self.stack.pop()
                self.handle(tok)

    def handle_while(self, tok, state):
        if not state.code_block:
            if state.check == -1:
                if not state.no:  # On start
                    self.tags[state.tag].extend((bc.LOAD_TAG, len(self.tags), bc.POP_JUMP))
                    state.tag = self._add_tag()
                self.handle_check(tok, state)
            else:
                if state.no:
                    self.tags[state.tag].append(bc.BOOL_NOT)
                self.tags[state.tag].extend((bc.POP_JUMP_IF, len(self.tags)))  # len(self.tags), but not - 1 -- new tag.
                state.code_block = True
                self.stack.append(stackelems.CodeBlock(False, False, self._add_tag()))
                self.handle(tok)
        else:
            self.tags[-1] = self.tags[-1][:-1]  # Removing ending POP_JUMP
            self.tags[-1].extend((bc.LOAD_TAG, state.tag, bc.POP_JUMP, bc.POP_JUMP))  # Double POP_JUMP: first for while jump, second -- end of block
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
            self.tags[state.tag].extend((bc.LOAD_TAG, tag, bc.POP_JUMP))
            self.stack.append(stackelems.CodeBlock(False, False, tag))
        else:
            self.tags[-1] = self.tags[-1][:-1] * state.iterations  # Remove POP_JUMP and multiply bytecode
            self.tags[-1].append(bc.POP_JUMP)  # and add POP_JUMP after multiplying
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
            elif tok.type == 'SYMBOL' and tok.value == 57:  # {
                state.multiline = True
            else:
                raise CorrectorSyntaxError(f'Неожиданный токен {tok.value}')
            state.started = True
        else:
            if state.multiline:
                if tok.type in ('COMMAND', 'WORD'):
                    self.handle_command(tok, state)
                elif tok.type == 'SYMBOL' and tok.value == 58:  # }
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
            self.tags[state.tag].extend((bc.LOAD_SYMBOL, tok.value, bc.LOAD_TAPE, bc.BIN_OP, bo.EQUAL))
            state.symbol_check = True
            state.check = tok.value

    def handle_symbol(self, tok, state):
        if tok.type == 'SYMBOL':
            self.tags[state.tag].extend((bc.LOAD_SYMBOL, tok.value))
            self.tags[state.tag].append(bc.POP_SET_TAPE)
            self.stack.pop()
        else:
            raise CorrectorSyntaxError('Ожидался символ')

    def handle_procedure_call(self, name: str):
        self.tags[self.stack[-1].tag].append(bc.LOAD_TAG)
        self.tags[self.stack[-1].tag].append(self.procedures[name])
        self.tags[self.stack[-1].tag].append(bc.POP_JUMP)

    def compose(self):
        for tag_id, tag_bytecode in enumerate(self.tags):
            self.bytecode.extend((bc.TAG, tag_id))
            self.bytecode.extend(tag_bytecode)
