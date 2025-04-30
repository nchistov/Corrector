from ..vm import Vm
from ..bytecode import byte_commands as bc

v = Vm()


def test_bin_equal():
    v.run(bytearray(), bytearray((bc.LOAD_SYMBOL, 0x01, bc.LOAD_SYMBOL, 0x01, bc.BIN_OP, bc.EQUAL)))

    assert v.stack[0] is True

def test_bin_less():
    v.run(bytearray(), bytearray((bc.LOAD_SYMBOL, 0x02, bc.LOAD_SYMBOL, 0x01, bc.BIN_OP, bc.LESS)))

    assert v.stack[0] is True

def test_tags():
    v.run(bytearray((bc.TAG, 0x01, bc.LOAD_SYMBOL, 0x01, bc.POP_SET_TAPE, bc.RETURN)), bytearray((bc.LOAD_TAG, 0x01, bc.POP_JUMP)))

    assert v.tape.get() == 1
