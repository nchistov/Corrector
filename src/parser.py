import re
from typing import NamedTuple

class Token(NamedTuple):
    type:   str | None
    value:  str
    line:   int
    symbol: int


def parse(code):
    keywords = {'ЭТО', 'ЕСЛИ', 'ПОКА', 'КОНЕЦ', 'ПОВТОРИ'}
    commands = {'ВПРАВО', 'ВЛЕВО', 'ПИШИ', 'ЯЩИК+', 'ЯЩИК-', 'ОБМЕН', 'ПЛЮС', 'МИНУС', 'СТОЯТЬ'}
    symbols = {'ПУСТО', 'ПРОБЕЛ', 'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З',
               'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
               'Ц', 'Я', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я'}
    token_specification = [
        ('KEYWORD',    r'|'.join(keywords)),
        ('COMMAND',    r'|'.join(commands)),
        ('WORD',       r'\w{2,}'),
        ('SYMBOL',     r'|'.join(symbols)),
        ('CHECK',      r'я=л|я#л|я>л|я<л'),
        ('NEWLINE',    r'\n'),
        ('SKIP',       r'[ \t]+'),
        ('MISMATCH',   r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code.upper()):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} unexpected on line {line_num}')
        yield Token(kind, value, line_num, column)
