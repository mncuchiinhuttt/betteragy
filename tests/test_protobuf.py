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


def test_extract_tokens_from_gen_metadata():
    from betteragy.services.protobuf_decoder import extract_tokens_from_gen_metadata

    # Construct inner f4 message:
    # f1=1318 (0x08, 0xa6, 0x0a), f2=5580 (0x10, 0xcc, 0x2b), f3=2023 (0x18, 0xe7, 0x0f)
    # f9=110 (0x48, 0x6e), f10=1913 (0x50, 0xf9, 0x0e)
    f4_data = bytes([
        0x08, 0xa6, 0x0a,
        0x10, 0xcc, 0x2b,
        0x18, 0xe7, 0x0f,
        0x48, 0x6e,
        0x50, 0xf9, 0x0e,
    ])
    # f19 = "gemini-3.8-flash" -> tag (19<<3)|2 = 154 -> 0x9a, 0x01, len=16
    name = b"gemini-3.8-flash"
    f19_data = bytes([0x9a, 0x01, len(name)]) + name
    # f4 tag = (4<<3)|2 = 34 -> 0x22, len(f4_data)
    f4_field = bytes([0x22, len(f4_data)]) + f4_data

    # inner f1 payload
    f1_payload = f19_data + f4_field
    # outer msg: f1 tag = (1<<3)|2 = 10 -> 0x0a, len(f1_payload)
    outer_blob = bytes([0x0a, len(f1_payload)]) + f1_payload

    result = extract_tokens_from_gen_metadata(outer_blob)
    assert result is not None
    model, inp, out, cache, reas = result
    assert model == "gemini-3.8-flash"
    assert inp == 1318
    assert cache == 5580
    assert out == 110
    assert reas == 1913
