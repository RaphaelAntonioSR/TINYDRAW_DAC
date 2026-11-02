"""Orquestra o fluxo: léxica -> sintática -> semântica -> geração de C."""
from dataclasses import dataclass, field
from typing import List, Optional

from .ast_nodes import Programa
from .codegen import Gerador
from .erros import Diagnostico, ErroDeCompilacao
from .lexer import Token, tokenizar
from .parser import Parser
from .semantica import Analisador, TabelaDeSimbolos


@dataclass
class Resultado:
    tokens: List[Token] = field(default_factory=list)
    ast: Optional[Programa] = None
    tabela: Optional[TabelaDeSimbolos] = None
    diagnosticos: List[Diagnostico] = field(default_factory=list)
    codigo_c: Optional[str] = None

    @property
    def erros(self):
        return [d for d in self.diagnosticos if d.nivel == "erro"]

    @property
    def avisos(self):
        return [d for d in self.diagnosticos if d.nivel == "aviso"]

    @property
    def sucesso(self) -> bool:
        return not self.erros


def transpilar(texto: str, origem: str = "programa.td") -> Resultado:
    """Retorna Resultado da fonte; somente programas válidos recebem codigo_c.

    origem identifica o arquivo no C. Esta API não grava nem executa arquivos;
    CLI e pipeline cuidam das operações externas.
    """
    tokens, diags = tokenizar(texto)
    res = Resultado(tokens=tokens, diagnosticos=list(diags))
    if res.erros:                      # erros léxicos interrompem o fluxo
        return res
    try:
        res.ast = Parser(tokens).analisar()
    except ErroDeCompilacao as e:
        res.diagnosticos += e.diagnosticos
        return res
    res.tabela, sem = Analisador().analisar(res.ast)
    res.diagnosticos += sem
    if res.sucesso:
        res.codigo_c = Gerador(res.ast, res.tabela).gerar(origem)
    return res
