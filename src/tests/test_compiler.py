from ..compiler import Compiler

def test_simple_procedure():
    c = Compiler()
    code = 'ЭТО Процедура СТОЯТЬ КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x00, 0x0D))

def test_commands():
    c = Compiler()
    code = 'ЭТО Процедура ВПРАВО ВЛЕВО ПЛЮС МИНУС КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x00, 0x05, 0x06, 0x0A, 0x0B, 0x09, 0x0A, 0x0C, 0x09, 0x0D))

def test_box():
    c = Compiler()
    code = 'ЭТО Процедура ЯЩИК+ ЯЩИК- КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x00, 0x0A, 0x07, 0x08, 0x09, 0x0D))

def test_exchange():
    c = Compiler()
    code = 'ЭТО Процедура ОБМЕН КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x00, 0x08, 0x0A, 0x07, 0x09, 0x0D))
