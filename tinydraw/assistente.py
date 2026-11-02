"""Fachada do assistente de desenho em linguagem natural.

Regra de ouro do projeto: o assistente NUNCA desenha. Ele apenas escreve um programa-fonte
TinyDraw (.td). O desenho só existe depois que esse programa passa pelo transpilador
(léxico, sintaxe, semântica), vira C, é compilado e executado.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional

MODO_CLAUDE = "claude"
MODO_LOCAL = "local"


class ErroAssistente(Exception):
    """Falha esperada do assistente (sem chave, sem rede, pedido não entendido...)."""


@dataclass
class ResultadoGeracao:
    codigo: str                      # programa .td produzido
    valido: bool                     # aceito pelo compilador TinyDraw?
    log: List[str] = field(default_factory=list)
    modo: str = ""


def gerar(modo: str, pedido: str, *, chave: str = "", modelo: str = "",
          codigo_atual: Optional[str] = None,
          progresso: Optional[Callable[[str], None]] = None) -> ResultadoGeracao:
    pedido = (pedido or "").strip()
    if not pedido:
        raise ErroAssistente("Escreva primeiro o que você quer desenhar.")
    if modo == MODO_CLAUDE:
        from .ia_claude import ConfigClaude, gerar_com_claude
        return gerar_com_claude(pedido, ConfigClaude(chave=chave, modelo=modelo or ConfigClaude.modelo),
                                codigo_atual=codigo_atual, progresso=progresso)
    from .ia_local import gerar_local
    return gerar_local(pedido, progresso=progresso)
