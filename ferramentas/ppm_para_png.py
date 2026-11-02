"""Converte um PPM (P6) em PNG, usando só a biblioteca padrão do Python.

Uso: py ferramentas/ppm_para_png.py build/casa.ppm [fator_de_ampliacao]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tinydraw.imagem import converter_arquivo  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    origem = Path(sys.argv[1])
    fator = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    destino = origem.with_suffix(".png")
    w, h = converter_arquivo(origem, destino, fator)
    print(f"gerado: {destino} ({w * fator}x{h * fator})")
