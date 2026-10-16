"""Mega Drive vector table and cartridge header parsing (stdlib only).

Layout (md-spec): vectors 0x000000-0x0000FF = 64 big-endian longs ([0]=SSP, [1]=reset PC);
header 0x000100-0x0001FF; checksum = sum of BE words 0x200..ROM end, mod 2^16.
"""
import struct


def parse_vectors(rom: bytes) -> list[int]:
    """The 64 BE longs at 0x000000."""
    return list(struct.unpack(">64L", rom[0x000:0x100]))


def _text(rom: bytes, start: int, end: int) -> str:
    return rom[start:end].decode("latin-1").strip()


def parse_header(rom: bytes) -> dict:
    """Header facts (text fields stripped; numbers as int)."""
    (checksum,) = struct.unpack(">H", rom[0x18E:0x190])
    rom_start, rom_end, ram_start, ram_end = struct.unpack(">4L", rom[0x1A0:0x1B0])
    return {
        "console": _text(rom, 0x100, 0x110),
        "copyright": _text(rom, 0x110, 0x120),
        "name_domestic": _text(rom, 0x120, 0x150),
        "name_overseas": _text(rom, 0x150, 0x180),
        "serial": _text(rom, 0x180, 0x18E),
        "checksum": checksum,
        "io": _text(rom, 0x190, 0x1A0),
        "rom_start": rom_start,
        "rom_end": rom_end,
        "ram_start": ram_start,
        "ram_end": ram_end,
        "region": _text(rom, 0x1F0, 0x200),
    }


def header_checksum(rom: bytes) -> int:
    """Sum of BE words from 0x200 to the header's ROM end (inclusive), clipped to the image, mod 2^16."""
    end = min(parse_header(rom)["rom_end"] + 1, len(rom))
    end -= (end - 0x200) % 2
    words = struct.unpack(">%dH" % ((end - 0x200) // 2), rom[0x200:end])
    return sum(words) & 0xFFFF
