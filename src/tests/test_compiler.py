from ..compiler import Compiler

c = Compiler()

def test_simple_procedure():
    code = 'ЭТО Процедура СТОЯТЬ КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x01, 0x10))

def test_symbol_procedure_name():
    code = 'ЭТО А СТОЯТЬ КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x10))

def test_commands():
    code = 'ЭТО Процедура ВПРАВО ВЛЕВО ПЛЮС МИНУС КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x01, 0x05, 0x06, 0x0A, 0x0B, 0x09, 0x0A, 0x0C, 0x09, 0x10))

def test_box():
    code = 'ЭТО Процедура ЯЩИК+ ЯЩИК- КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x01, 0x0A, 0x07, 0x08, 0x09, 0x10))

def test_exchange():
    code = 'ЭТО Процедура ОБМЕН КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((0x00, 0x01, 0x08, 0x0A, 0x07, 0x09, 0x10))

def test_if():
    code = 'ЭТО Процедура ЕСЛИ ПУСТО ТО ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x03, 0x01, 0x0A, 0x04, 0x01, 0x0E, 0x02, 0x10, 0x00, 0x02, 0x05, 0x10))

def test_if_not():
    code = 'ЭТО Процедура ЕСЛИ НЕ ПУСТО ТО ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x03, 0x01, 0x0A, 0x04, 0x01, 0x11, 0x0E, 0x02, 0x10, 0x00, 0x02, 0x05, 0x10))

def test_multiline():
    code = 'ЭТО Процедура ЕСЛИ ПУСТО ТО { ВПРАВО ВЛЕВО } КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x03, 0x01, 0x0A, 0x04, 0x01, 0x0E, 0x02, 0x10, 0x00, 0x02, 0x05, 0x06, 0x10))

def test_procedure_call():
    code = 'ЭТО Процедура ВПРАВО КОНЕЦ ЭТО Программа Процедура КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x05, 0x10, 0x00, 0x02, 0x02, 0x01, 0x0D, 0x10))

def test_procedure_call_before_def():
    code = 'ЭТО Программа Процедура КОНЕЦ ЭТО Процедура ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((0x00, 0x01, 0x02, 0x02, 0x0D, 0x10, 0x00, 0x02, 0x05, 0x10))
