from ..compiler import Compiler
from ..bytecode import *

c = Compiler()

def test_simple_procedure():
    code = 'ЭТО Процедура СТОЯТЬ КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((TAG, 0x00, 0x00, RETURN))

def test_symbol_procedure_name():
    code = 'ЭТО А СТОЯТЬ КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, RETURN))

def test_commands():
    code = 'ЭТО Процедура ВПРАВО ВЛЕВО ПЛЮС МИНУС КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((TAG, 0x00, 0x00, RIGHT, LEFT, LOAD_TAPE, POP_NEXT_PUSH, POP_SET_TAPE,
                            LOAD_TAPE, POP_PREV_PUSH, POP_SET_TAPE, RETURN))

def test_box():
    code = 'ЭТО Процедура ЯЩИК+ ЯЩИК- КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_TAPE, POP_SET_BOX, LOAD_BOX, POP_SET_TAPE, RETURN))

def test_exchange():
    code = 'ЭТО Процедура ОБМЕН КОНЕЦ'

    bc = c.compile(code)
    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_BOX, LOAD_TAPE, POP_SET_BOX, POP_SET_TAPE, RETURN))

def test_if():
    code = 'ЭТО Процедура ЕСЛИ ПУСТО ТО ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_SYMBOL, 0x00, LOAD_TAPE, BIN_OP, EQUAL,
                            POP_JUMP_IF, 0x00, 0x01, RETURN, TAG, 0x00, 0x01, RIGHT, RETURN))

def test_if_not():
    code = 'ЭТО Процедура ЕСЛИ НЕ ПУСТО ТО ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_SYMBOL, 0x00, LOAD_TAPE, BIN_OP, EQUAL, BOOL_NOT,
                            POP_JUMP_IF, 0x00, 0x01, RETURN, TAG, 0x00, 0x01, RIGHT, RETURN))

def test_if_else():
    code = 'ЭТО Программа ЕСЛИ ПУСТО ТО ВПРАВО ИНАЧЕ ВЛЕВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_SYMBOL, 0x00, LOAD_TAPE, BIN_OP, EQUAL, POP_JUMP_IF_ELSE, 0x00, 0x01, 0x00, 0x02,
                            RETURN, TAG, 0x00, 0x01, RIGHT, RETURN, TAG, 0x00, 0x02, LEFT, RETURN))

def test_multiline():
    code = 'ЭТО Процедура ЕСЛИ ПУСТО ТО { ВПРАВО ВЛЕВО } КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_SYMBOL, 0x00, LOAD_TAPE, BIN_OP, EQUAL,
                            POP_JUMP_IF, 0x00, 0x01, RETURN, TAG, 0x00, 0x01, RIGHT, LEFT, RETURN))

def test_procedure_call():
    code = 'ЭТО Процедура ВПРАВО КОНЕЦ ЭТО Программа Процедура КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, RIGHT, RETURN, TAG, 0x00, 0x01, LOAD_TAG, 0x00, 0x00, POP_JUMP, RETURN))

def test_procedure_call_before_def():
    code = 'ЭТО Программа Процедура КОНЕЦ ЭТО Процедура ВПРАВО КОНЕЦ'
    bc = c.compile(code)

    assert bc == bytearray((TAG, 0x00, 0x00, LOAD_TAG, 0x00, 0x01, POP_JUMP, RETURN, TAG, 0x00, 0x01, RIGHT, RETURN))

def test_compile_one_command():
    command = 'ВПРАВО'
    bc = c.compile_one_command(command)

    assert bc == bytearray((RIGHT,))

def test_waiting():
    code = 'ЭТО Программа ВПРАВО КОНЕЦ'
    bc = c.compile(code, waiting=True)

    assert bc == bytearray((TAG, 0x00, 0x00, RIGHT, WAIT, RETURN))
