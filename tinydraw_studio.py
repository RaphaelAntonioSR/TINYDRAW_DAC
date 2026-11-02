"""Ponto de entrada do TinyDraw Studio (também é o arquivo usado para gerar o .exe)."""
import sys
from pathlib import Path


def main() -> int:
    if "--autoteste" in sys.argv:                      # verificação sem abrir janela
        from tinydraw import pipeline
        ok, texto = pipeline.autoteste()
        # Em --windowed, sys.stdout pode ser None. O arquivo é o resultado
        # consultável do autoteste mesmo quando não existe console.
        if sys.stdout is not None:
            print(texto)
        try:                                           # o .exe "windowed" não tem console: grava em arquivo
            destino = Path.cwd() / "autoteste.txt"
            destino.write_text(texto + "\n", encoding="utf-8")
        except OSError:
            pass
        return 0 if ok else 1
    from tinydraw.gui import iniciar
    iniciar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
