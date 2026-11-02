"""Leitura de PPM (P6) e conversão para PNG usando apenas a biblioteca padrão."""
import struct
import zlib
from pathlib import Path
from typing import Tuple


def ler_ppm(dados: bytes) -> Tuple[int, int, bytes]:
    partes = dados.split(b"\n", 3)
    if len(partes) < 4 or partes[0] != b"P6":
        raise ValueError("arquivo não é um PPM P6 válido")
    w, h = map(int, partes[1].split())
    # Leitor do subconjunto P6 emitido pelo runtime, não de todo PPM possível.
    if w <= 0 or h <= 0 or partes[2] != b"255":
        raise ValueError("PPM deve ter dimensões positivas e máximo RGB 255")
    pixels = partes[3]
    if len(pixels) != w * h * 3:
        raise ValueError("tamanho de pixels inconsistente no PPM")
    return w, h, pixels


def rgb_para_png(w: int, h: int, rgb: bytes, fator: int = 1) -> bytes:
    """PNG RGB 8 bits; `fator` amplia cada pixel (vizinho mais próximo, visual 'pixel art')."""
    if w <= 0 or h <= 0 or len(rgb) != w * h * 3:
        raise ValueError("dimensões ou dados RGB inválidos")
    if not isinstance(fator, int) or fator < 1:
        raise ValueError("fator de ampliação deve ser um inteiro positivo")
    linhas = []
    for y in range(h):
        linha = rgb[y * w * 3:(y + 1) * w * 3]
        ampliada = b"".join(linha[i:i + 3] * fator for i in range(0, len(linha), 3))
        linhas += [b"\x00" + ampliada] * fator

    def bloco(tipo: bytes, corpo: bytes) -> bytes:
        c = struct.pack(">I", len(corpo)) + tipo + corpo
        return c + struct.pack(">I", zlib.crc32(tipo + corpo) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", w * fator, h * fator, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(b"".join(linhas)))
            + bloco(b"IEND", b""))


def ppm_para_png(dados_ppm: bytes, fator: int = 1) -> Tuple[bytes, int, int]:
    w, h, rgb = ler_ppm(dados_ppm)
    return rgb_para_png(w, h, rgb, fator), w, h


def fator_para_caber(w: int, h: int, max_w: int = 720, max_h: int = 520) -> int:
    return max(1, min(max_w // max(w, 1), max_h // max(h, 1)))


def converter_arquivo(origem: Path, destino: Path, fator: int) -> Tuple[int, int]:
    png, w, h = ppm_para_png(Path(origem).read_bytes(), fator)
    Path(destino).write_bytes(png)
    return w, h
