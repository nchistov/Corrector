from typing import NamedTuple

class Token(NamedTuple):
    type:   str
    value:  str | int
    line:   int
    row: int


class Parser:
    def __init__(self):
        self.keywords = ['ЭТО', 'ЕСЛИ', 'ПОКА', 'КОНЕЦ', 'ПОВТОРИ', 'ТО', 'НЕ']
        self.commands = ['ВПРАВО', 'ВЛЕВО', 'ПИШИ', 'ЯЩИК+', 'ЯЩИК-', 'ОБМЕН', 'ПЛЮС', 'МИНУС', 'СТОЯТЬ']
        self.symbols = ['ПУСТО', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                   'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З','И', 'Й', 'К',
                   'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
                   'Ц', 'Я', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я', 'ПРОБЕЛ'
                                                                     '-', '+', '/', '*', '=', '<', '>', '(', ')', '[', ']', '{', '}', '.',
                   ',', '!', '?', ';', ':', '\'', '"', '#', '|', '$', '%', '~', '@']
        self.checks = ['Я=Л', 'Я>Л', 'Я<Л', 'Я#Л']

        self.line = self.row = 1
        self.cur_token = ''

    def parse(self, code):
        for symbol in code.upper():
            if symbol.isspace():
                if self.cur_token:
                    yield self._get_tok()
                    self.cur_token = ''
                if symbol == '\n':
                    self.row = 0
                    self.line += 1
            else:
                self.cur_token += symbol
            self.row += 1
        if self.cur_token:
            yield self._get_tok()

    def _get_tok(self) -> Token:
        if self.cur_token in self.symbols:
            return Token('SYMBOL', self.cur_token, self.line, self.row)
        elif self.cur_token in self.keywords:
            return Token('KEYWORD', self.cur_token, self.line, self.row)
        elif self.cur_token in self.commands:
            return Token('COMMAND', self.cur_token, self.line, self.row)
        elif self.cur_token in self.checks:
            return Token('CHECK', self.cur_token, self.line, self.row)
        elif self.cur_token.isdigit():
            return Token('NUMBER', int(self.cur_token), self.line, self.row)
        else:
            return Token('WORD', self.cur_token, self.line, self.row)
