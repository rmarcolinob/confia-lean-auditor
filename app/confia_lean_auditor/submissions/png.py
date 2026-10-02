"""Bounded validation of the 8-bit RGB/RGBA, non-interlaced PNGs from Canvas.

No rendering, correction, resizing, or pixel-to-stroke comparison takes place.
Only structure, CRCs, dimensions and the compressed scanline stream are checked.
"""
import struct
import zlib


def validate_png(data: bytes, width: int, height: int) -> None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    offset = 8
    seen_header = seen_data = seen_end = data_finished = False
    compressed = []
    channels = 0
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG")
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("invalid PNG CRC")
        if not seen_header and kind != b"IHDR":
            raise ValueError("missing PNG header")
        if kind == b"IHDR":
            if seen_header or length != 13:
                raise ValueError("invalid PNG header")
            w, h, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if w != width or h != height or not w or not h:
                raise ValueError("PNG dimensions differ from capture page")
            if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
                raise ValueError("unsupported Canvas PNG format")
            channels = 3 if color == 2 else 4
            seen_header = True
        elif kind == b"IDAT":
            if data_finished:
                raise ValueError("non-contiguous PNG data")
            seen_data = True
            compressed.append(payload)
        elif kind == b"IEND":
            if length or not seen_data or end != len(data):
                raise ValueError("invalid PNG end")
            seen_end = True
            break
        else:
            if seen_data:
                data_finished = True
            if not (kind[0] & 32) and kind != b"PLTE":
                raise ValueError("unsupported critical PNG chunk")
        offset = end
    if not seen_end:
        raise ValueError("missing PNG end")

    # Inflate in bounded chunks, not into a potentially huge full image buffer.
    stride = width * channels + 1
    expected = height * stride
    decoded = 0
    stream = zlib.decompressobj()
    pending = b"".join(compressed)
    while pending:
        block = stream.decompress(pending, min(65536, expected - decoded + 1))
        pending = stream.unconsumed_tail
        if decoded + len(block) > expected:
            raise ValueError("PNG decompressed size exceeds page")
        first_filter = (-decoded) % stride
        if any(block[i] > 4 for i in range(first_filter, len(block), stride)):
            raise ValueError("invalid PNG row filter")
        decoded += len(block)
        if stream.unused_data:
            raise ValueError("trailing PNG compressed data")
    if not stream.eof or decoded != expected:
        raise ValueError("invalid PNG compressed stream")
