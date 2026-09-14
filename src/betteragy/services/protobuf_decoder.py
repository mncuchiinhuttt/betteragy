"""Zero-dependency Protobuf wire-format decoder to extract model token telemetry."""

from typing import Any, Optional


def decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Decode a varint from bytes at offset, returning (value, new_offset)."""
    val = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        offset += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        if shift > 64:
            break
    return val, offset


def decode_proto_message(data: bytes, depth: int = 0, max_depth: int = 4) -> dict[int, list[Any]]:
    """Decode raw protobuf message into field_number -> list of values."""
    fields: dict[int, list[Any]] = {}
    if depth > max_depth or not data:
        return fields

    offset = 0
    data_len = len(data)

    while offset < data_len:
        tag, offset = decode_varint(data, offset)
        if offset > data_len:
            break
        field_number = tag >> 3
        wire_type = tag & 0x7

        if wire_type == 0:  # Varint
            val, offset = decode_varint(data, offset)
            fields.setdefault(field_number, []).append(val)
        elif wire_type == 2:  # Length-delimited (string, bytes, sub-message)
            length, offset = decode_varint(data, offset)
            if offset + length > data_len:
                break
            val_bytes = data[offset : offset + length]
            offset += length

            sub = decode_proto_message(val_bytes, depth + 1, max_depth)
            if sub and any(k < 50 for k in sub.keys()):
                fields.setdefault(field_number, []).append(sub)
            else:
                try:
                    s = val_bytes.decode("utf-8")
                    if s.isprintable() and len(s) > 0:
                        fields.setdefault(field_number, []).append(s)
                    else:
                        fields.setdefault(field_number, []).append(val_bytes)
                except Exception:
                    fields.setdefault(field_number, []).append(val_bytes)
        elif wire_type == 1:  # 64-bit
            offset += 8
        elif wire_type == 5:  # 32-bit
            offset += 4
        else:
            break

    return fields


def extract_tokens_from_gen_metadata(blob: bytes) -> Optional[tuple[str, int, int, int, int]]:
    """Extract (model_name, input_tokens, output_tokens, cache_tokens, reasoning_tokens)."""
    try:
        msg = decode_proto_message(blob)
        # Check field 1
        f1_list = msg.get(1, [])
        for f1 in f1_list:
            if not isinstance(f1, dict):
                continue
            # Model name is in field 19 or within field 20
            model_name = "Unknown"
            model_candidates = f1.get(19, []) or f1.get(20, [])
            if model_candidates and isinstance(model_candidates[0], str):
                model_name = model_candidates[0]

            # Token usage is in field 4
            f4_list = f1.get(4, [])
            for f4 in f4_list:
                if not isinstance(f4, dict):
                    continue
                inp = f4.get(1, [0])[0] if 1 in f4 else 0
                cache = f4.get(2, [0])[0] if 2 in f4 else 0
                reas = f4.get(10, [0])[0] if 10 in f4 else 0
                if 9 in f4:
                    out = f4.get(9, [0])[0]
                else:
                    total_out = f4.get(3, [0])[0] if 3 in f4 else 0
                    out = max(0, total_out - reas)

                if any((inp, out, cache, reas)):
                    return (
                        model_name,
                        int(inp) if isinstance(inp, int) else 0,
                        int(out) if isinstance(out, int) else 0,
                        int(cache) if isinstance(cache, int) else 0,
                        int(reas) if isinstance(reas, int) else 0,
                    )
    except Exception:
        pass
    return None
