from ..vm import Vm

def test_bin_equal():
    v = Vm()

    v.run(bytearray(), bytearray((0x03, 0x00, 0x03, 0x00, 0x04, 0x01)))

    assert v.stack[0] is True

def test_bin_less():
    v = Vm()

    v.run(bytearray(), bytearray((0x03, 0x01, 0x03, 0x00, 0x04, 0x03)))

    assert v.stack[0] is True
