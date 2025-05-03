from .parser import Parser
from ..errors import CorrectorSyntaxError, CorrectorMemoryError
from . import stack_elements
from .. import bytecode as bc


class Compiler:
    def __init__(self):
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
        self.checks = {'Я=Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bc.EQUAL),
                       'Я>Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bc.MORE),
                       'Я<Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bc.LESS),
                       'Я#Л': (bc.LOAD_TAPE, bc.LOAD_BOX, bc.BIN_OP, bc.NOT_EQUAL),
                       'ЦИФРА': (bc.LOAD_TAPE, bc.IS_DIGIT)}

        self.parser = Parser()

    def reset(self):
        self.procedures = {}
        self.tags = []
        self.stack = []

    def startup(self, code):
        self.reset()

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

    def compile(self, code: str) -> bytearray:
        self.startup(code)

        for tok in self.parser.parse(code):
            self.handle(tok)

        if self.stack:
            raise CorrectorSyntaxError('Незавершённый блок!')

        return self.compose()

    def compile_one_command(self, code: str) -> bytearray:
        tokens = self.parser.parse(code)
        bytecode = bytearray()

        waiting = False

        try:
            tok = next(tokens)

            if tok.type == "COMMAND":
                if tok.value == 'ПИШИ':
                    waiting = True
                    symbol = next(tokens)
                    waiting = False

                    if symbol.type == "SYMBOL":
                        bytecode.extend((bc.LOAD_SYMBOL, symbol.value, bc.POP_SET_TAPE))
                    else:
                        raise CorrectorSyntaxError('Ожидался символ')
                else:
                    bytecode.extend(self.commands[tok.value])
            elif tok.type == "WORD" or tok.type == "SYMBOL":
                if tok.value in self.procedures.keys():
                    bytecode.extend((bc.LOAD_TAG, *add_number(self.procedures[tok.value]), bc.POP_JUMP))
                else:
                    raise CorrectorSyntaxError(f'Не определена процедура с именем {tok.value}')

            if next(tokens):
                raise CorrectorSyntaxError('В строке ввода команды не должно присутствовать ничего, кроме команды')
        except StopIteration:
            if waiting:
                raise CorrectorSyntaxError('Ожидался символ')

        return bytecode

    def handle(self, tok):
        if not self.stack:
            if tok.type == 'KEYWORD' and tok.value == 'ЭТО':
                self.stack.append(stack_elements.Procedure('', -1))
            else:
                raise CorrectorSyntaxError('На внешнем уровне программы не должно быть команд')
        else:
            match self.stack[-1]:
                case stack_elements.Procedure:
                    self.handle_procedure(tok, self.stack[-1])
                case stack_elements.WriteCommand:
                    self.handle_symbol(tok, self.stack[-1])
                case stack_elements.If:
                    self.handle_if(tok, self.stack[-1])
                case stack_elements.ForLoop:
                    self.handle_for(tok, self.stack[-1])
                case stack_elements.WhileLoop:
                    self.handle_while(tok, self.stack[-1])
                case stack_elements.CodeBlock:
                    self.handle_code_block(tok, self.stack[-1])

    def _add_tag(self, name: str = None) -> int:
        tag_id = len(self.tags)
        if tag_id >= 16**4:  # Два байта
            raise CorrectorMemoryError('Слишком большое число конструкций')
        if name:
            self.procedures[name] = tag_id
        self.tags.append(bytearray())

        return tag_id

    def handle_end(self):
        self.tags[self.stack.pop().tag].append(bc.RETURN)

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
                    self.tags[state.tag].extend((bc.POP_JUMP_IF, *add_number(len(self.tags))))
                    state.code_block = True
                    self.stack.append(stack_elements.CodeBlock(False, False, self._add_tag()))
        else:
            if tok.value == 'ИНАЧЕ':
                if not state.else_check:
                    if_tag = get_number(*self.tags[state.tag][-2:])  # Последняя цифра в байт-коде
                    else_tag = self._add_tag()
                    self.tags[state.tag] = self.tags[state.tag][:-3]  # Удаление POP_JUMP_IF <tag>

                    self.tags[state.tag].extend((bc.POP_JUMP_IF_ELSE,
                                                 *add_number(if_tag),
                                                 *add_number(else_tag)))  # POP_JUMP_IF_ELSE <if_tag> <else_tag>

                    self.stack.append(stack_elements.CodeBlock(False, False, else_tag))
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
                    self.tags[state.tag].extend((bc.LOAD_TAG, *add_number(len(self.tags)), bc.POP_JUMP))
                    state.tag = self._add_tag()
                self.handle_check(tok, state)
            else:
                if state.no:
                    self.tags[state.tag].append(bc.BOOL_NOT)
                self.tags[state.tag].extend((bc.POP_JUMP_IF, *add_number(len(self.tags))))
                state.code_block = True
                self.stack.append(stack_elements.CodeBlock(False, False, self._add_tag()))
                self.handle(tok)
        else:
            self.tags[-1] = self.tags[-1][:-1]  # Удаление RETURN
            self.tags[-1].extend((bc.LOAD_TAG, *add_number(state.tag), bc.POP_JUMP, bc.RETURN))
            self.handle_end()
            self.handle(tok)

    def handle_for(self, tok, state):
        if state.iterations == -1:
            if tok.type == 'SYMBOL':
                if 0 < tok.value < 10:
                    state.iterations = tok.value - 1
                else:
                    raise CorrectorSyntaxError('Ожидалось кол-во повторений')
            elif tok.type == 'NUMBER':
                state.iterations = tok.value
            else:
                raise CorrectorSyntaxError('Ожидалось кол-во повторений')

            tag = self._add_tag()
            self.tags[state.tag].extend((bc.LOAD_TAG, *add_number(tag), bc.POP_JUMP))
            self.stack.append(stack_elements.CodeBlock(False, False, tag))
        else:
            self.tags[-1] = self.tags[-1][:-1] * state.iterations  # Удаление RETURN и "умножение" байт-кода
            self.tags[-1].append(bc.RETURN)  # и добавление RETURN в конец
            self.stack.pop()
            self.handle(tok)

    def handle_command(self, tok, state):
        if tok.type == 'KEYWORD':
            match tok.value:
                case 'КОНЕЦ':
                    if state == stack_elements.Procedure:
                        self.handle_end()
                    else:
                        raise CorrectorSyntaxError('Неожиданное ключевое слово КОНЕЦ')
                case 'ЕСЛИ':
                    self.stack.append(stack_elements.If(False, False, -1, state.tag, False, False))
                case 'ПОВТОРИ':
                    self.stack.append(stack_elements.ForLoop(state.tag, -1))
                case 'ПОКА':
                    self.stack.append(stack_elements.WhileLoop(False, False, -1, state.tag, False))
                case _:
                    raise CorrectorSyntaxError(f'Неожиданное ключевое слово {tok.value}')
        elif tok.type == "COMMAND":
            if tok.value == 'ПИШИ':
                self.stack.append(stack_elements.WriteCommand(state.tag))
            else:
                self.tags[state.tag].extend(self.commands[tok.value])
        elif tok.type == "WORD" or tok.type == "SYMBOL":
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
            self.tags[state.tag].extend((bc.LOAD_SYMBOL, tok.value, bc.LOAD_TAPE, bc.BIN_OP, bc.EQUAL))
            state.symbol_check = True
            state.check = tok.value

    def handle_symbol(self, tok, state):
        if tok.type == 'SYMBOL':
            self.tags[state.tag].extend((bc.LOAD_SYMBOL, tok.value, bc.POP_SET_TAPE))
            self.stack.pop()
        else:
            raise CorrectorSyntaxError('Ожидался символ')

    def handle_procedure_call(self, name: str):
        self.tags[self.stack[-1].tag].extend((bc.LOAD_TAG, *add_number(self.procedures[name]), bc.POP_JUMP))

    def compose(self) -> bytearray:
        bytecode = bytearray()

        for tag_id, tag_bytecode in enumerate(self.tags):
            bytecode.extend((bc.TAG, *add_number(tag_id)))
            bytecode.extend(tag_bytecode)

        return bytecode


def add_number(number: int) -> [int, int]:
    """adding a number in two bytes"""
    first_byte = number >> 8
    second_byte = number - (first_byte << 8)
    return first_byte, second_byte

def get_number(byte1: int, byte2: int) -> int:
    return (byte1 << 8) + byte2
