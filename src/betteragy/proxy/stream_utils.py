"""HTTP stream reading and forwarding helpers for chunked and fixed-length bodies."""

import asyncio


async def read_chunked_payload(reader: asyncio.StreamReader) -> bytes:
    """Read full HTTP/1.1 chunked body from reader into a single bytes object."""
    chunks = []
    while True:
        size_line = await reader.readline()
        if not size_line:
            break
        size_str = size_line.split(b";")[0].strip()
        try:
            chunk_size = int(size_str, 16)
        except ValueError:
            break
        if chunk_size == 0:
            await reader.readline()  # read trailing \r\n
            break
        chunk_data = await reader.readexactly(chunk_size)
        await reader.readline()  # read \r\n
        chunks.append(chunk_data)
    return b"".join(chunks)


async def stream_chunked_response(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Stream HTTP/1.1 chunked response chunk by chunk to client without buffering."""
    while True:
        line = await reader.readline()
        if not line:
            break
        writer.write(line)
        size_str = line.split(b";")[0].strip()
        try:
            chunk_size = int(size_str, 16)
        except ValueError:
            break
        if chunk_size == 0:
            trailing = await reader.readline()
            writer.write(trailing)
            await writer.drain()
            break
        data = await reader.readexactly(chunk_size + 2)  # chunk data + \r\n
        writer.write(data)
        await writer.drain()


async def stream_fixed_response(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, length: int
) -> None:
    """Stream exactly length bytes from reader to writer without blocking past EOF."""
    remaining = length
    while remaining > 0:
        to_read = min(remaining, 16384)
        buf = await reader.read(to_read)
        if not buf:
            break
        writer.write(buf)
        await writer.drain()
        remaining -= len(buf)
