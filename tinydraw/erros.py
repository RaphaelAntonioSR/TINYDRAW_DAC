"""Diagnósticos (erros e avisos) produzidos pelas fases do transpilador."""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Diagnostico:
    nivel: str      # "erro" ou "aviso"
    fase: str       # léxico, sintático ou semântico
    mensagem: str
    linha: int
    coluna: int

    def formatar(self, arquivo: str = "<fonte>") -> str:
        return (f"{arquivo}:{self.linha}:{self.coluna}: "
                f"{self.nivel} {self.fase}: {self.mensagem}")


class ErroDeCompilacao(Exception):
    """Levantada pelo analisador sintático ao encontrar o primeiro erro."""

    def __init__(self, diagnosticos: List[Diagnostico]):
        super().__init__("; ".join(d.mensagem for d in diagnosticos))
        self.diagnosticos = diagnosticos
