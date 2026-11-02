"""Fachada do assistente de desenho em linguagem natural.

Regra de ouro do projeto: o assistente NUNCA desenha. Ele apenas escreve um programa-fonte
TinyDraw (.td). O desenho só existe depois que esse programa passa pelo transpilador
(léxico, sintaxe, semântica), vira C, é compilado e executado.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional

MODO_LOCAL = "local"


class ErroAssistente(Exception):
    """Pedido vazio ou não reconhecido pelo assistente local."""


@dataclass
class ResultadoGeracao:
    codigo: str                      # programa .td produzido
    valido: bool                     # aceito pelo compilador TinyDraw?
    log: List[str] = field(default_factory=list)
    modo: str = ""


def gerar(pedido: str, *,
          progresso: Optional[Callable[[str], None]] = None) -> ResultadoGeracao:
    """Gera fonte .td por regras locais e retorna código, validade e log."""
    pedido = (pedido or "").strip()
    if not pedido:
        raise ErroAssistente("Escreva primeiro o que você quer desenhar.")
    from .assistente_local import gerar_local
    return gerar_local(pedido, progresso=progresso)
