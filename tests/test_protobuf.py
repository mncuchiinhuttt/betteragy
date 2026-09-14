"""Unit tests for protobuf wire decoder."""

from betteragy.services.protobuf_decoder import decode_varint, decode_proto_message


def test_decode_varint():
    # 150 -> 0x96 0x01
    data = bytes([0x96, 0x01])
    val, offset = decode_varint(data, 0)
    assert val == 150
    assert offset == 2


def test_decode_proto_message_simple():
    # Field 1 (varint) = 42 -> tag = (1 << 3) | 0 = 8 -> 0x08, val = 42 -> 0x2A
    # Field 2 (string) = "test" -> tag = (2 << 3) | 2 = 18 -> 0x12, len = 4 -> 0x04, "test"
    data = bytes([0x08, 0x2A, 0x12, 0x04, ord('t'), ord('e'), ord('s'), ord('t')])
    msg = decode_proto_message(data)
    assert msg[1] == [42]
    assert msg[2] == ["test"]
