from typing import NamedTuple

class Token(NamedTuple):
    type:   str
    value:  str
    line:   int
    row: int


def parse(code):
    keywords = ['ЭТО', 'ЕСЛИ', 'ПОКА', 'КОНЕЦ', 'ПОВТОРИ', 'ТО', 'НЕ']
    commands = ['ВПРАВО', 'ВЛЕВО', 'ПИШИ', 'ЯЩИК+', 'ЯЩИК-', 'ОБМЕН', 'ПЛЮС', 'МИНУС', 'СТОЯТЬ']
    symbols = ['ПУСТО', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
               'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З','И', 'Й', 'К',
               'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
               'Ц', 'Я', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я', 'ПРОБЕЛ'
               '-', '+', '/', '*', '=', '<', '>', '(', ')', '[', ']', '{', '}', '.',
               ',', '!', '?', ';', ':', '\'', '"', '#', '|', '$', '%', '~', '@']
    checks = {'Я=Л', 'Я>Л', 'Я<Л', 'Я#Л'}

    line = row = 1
    cur_token = ''

    for symbol in code.upper():
        if symbol.isspace():
            if cur_token:
                if cur_token in symbols:
                    yield Token('SYMBOL', cur_token, line, row)
                elif cur_token in keywords:
                    yield Token('KEYWORD', cur_token, line, row)
                elif cur_token in commands:
                    yield Token('COMMAND', cur_token, line, row)
                elif cur_token in checks:
                    yield Token('CHECK', cur_token, line, row)
                else:
                    yield Token('WORD', cur_token, line, row)
                cur_token = ''
            if symbol == '\n':
                row = 0
                line += 1
        else:
            cur_token += symbol
        row += 1
