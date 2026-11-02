"""Árvore sintática abstrata (AST) da TinyDraw."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Comando:
    linha: int
    coluna: int


@dataclass
class Tela(Comando):
    largura: int = 0
    altura: int = 0


@dataclass
class DefCor(Comando):
    nome: str = ""
    r: int = 0
    g: int = 0
    b: int = 0


@dataclass
class Usar(Comando):
    nome: str = ""


@dataclass
class Ponto(Comando):
    x: int = 0
    y: int = 0


@dataclass
class Linha(Comando):
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0


@dataclass
class Retangulo(Comando):
    x: int = 0
    y: int = 0
    largura: int = 0
    altura: int = 0


@dataclass
class Salvar(Comando):
    arquivo: str = ""


@dataclass
class Programa:
    comandos: List[Comando] = field(default_factory=list)


def descrever(prog: Programa) -> str:
    """Representação textual da AST (usada por --ast)."""
    linhas = ["Programa"]
    for c in prog.comandos:
        campos = ", ".join(f"{k}={v!r}" for k, v in vars(c).items()
                           if k not in ("linha", "coluna"))
        # ASCII também funciona quando stdout é redirecionado em CP1252 no Windows.
        linhas.append(f"  +- {type(c).__name__}({campos})  @ {c.linha}:{c.coluna}")
    return "\n".join(linhas)
