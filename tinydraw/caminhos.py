"""Localização de recursos (runtime C, exemplos), dentro ou fora do .exe."""
import sys
from pathlib import Path


def empacotado() -> bool:
    """True quando rodando como executável criado pelo PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def raiz_recursos() -> Path:
    """Pasta onde estão runtime/ e exemplos/ (no .exe: pasta temporária de extração)."""
    if empacotado():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def pasta_do_executavel() -> Path:
    if empacotado():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def pasta_runtime() -> Path:
    return raiz_recursos() / "runtime"


def pasta_exemplos() -> Path:
    return raiz_recursos() / "exemplos"


def pasta_saida_padrao() -> Path:
    """Onde o Studio grava .td, .c, executável e .ppm."""
    return Path.home() / "TinyDrawStudio" / "saida"
