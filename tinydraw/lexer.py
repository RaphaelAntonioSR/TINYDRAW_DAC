"""Análise léxica da TinyDraw, baseada em expressões regulares."""
import re
from dataclasses import dataclass
from typing import Any, List, Tuple

from .erros import Diagnostico

PALAVRAS_RESERVADAS = {
    "tela", "cor", "usar", "ponto", "linha", "retangulo",
    "salvar", "em", "de", "ate", "tamanho", "por",
}
# Grafias acentuadas aceitas como sinônimos.
SINONIMOS = {"até": "ate", "retângulo": "retangulo"}

# Especificação léxica: a ordem importa (primeira alternativa que casar vence).
ESPECIFICACAO = [
    ("COMENTARIO",    r"\#[^\n]*"),
    ("ESPACO",        r"[ \t\r]+"),
    ("NOVA_LINHA",    r"\n"),
    ("STRING",        r'"[^"\n]*"'),
    ("STRING_ABERTA", r'"[^\n]*'),
    ("INT",           r"[0-9]+"),
    ("ID",            r"[^\W\d]\w*"),
    ("VIRGULA",       r","),
    ("IGUAL",         r"="),
    ("DESCONHECIDO",  r"."),
]
_REGEX = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPECIFICACAO))


@dataclass(frozen=True)
class Token:
    tipo: str        # TELA, COR, ..., INT, ID, STRING, VIRGULA, IGUAL, EOF
    lexema: str
    valor: Any
    linha: int
    coluna: int


def tokenizar(texto: str) -> Tuple[List[Token], List[Diagnostico]]:
    """Retorna (tokens posicionados, diagnósticos), sempre incluindo EOF.

    Limites de coordenadas são regras semânticas, não regras do scanner.
    """
    # Editores Windows podem acrescentar BOM ao UTF-8. Ele não faz parte da DSL
    # e só é ignorado no início, preservando a coluna 1 do primeiro comando.
    if texto.startswith("\ufeff"):
        texto = texto[1:]
    tokens: List[Token] = []
    diags: List[Diagnostico] = []
    linha, inicio_linha = 1, 0

    for m in _REGEX.finditer(texto):
        tipo, lex = m.lastgroup, m.group()
        coluna = m.start() - inicio_linha + 1

        if tipo == "NOVA_LINHA":
            linha += 1
            inicio_linha = m.end()
        elif tipo in ("ESPACO", "COMENTARIO"):
            continue
        elif tipo == "INT":
            try:
                valor = int(lex)
            except ValueError:
                # Python limita conversões decimais longas; a fonte deve gerar
                # diagnóstico em vez de encerrar o Studio com uma exceção.
                diags.append(Diagnostico("erro", "léxico",
                                         "literal inteiro longo demais", linha, coluna))
                continue
            tokens.append(Token("INT", lex, valor, linha, coluna))
        elif tipo == "ID":
            normal = SINONIMOS.get(lex, lex)
            if normal in PALAVRAS_RESERVADAS:
                tokens.append(Token(normal.upper(), lex, normal, linha, coluna))
            else:
                tokens.append(Token("ID", lex, lex, linha, coluna))
        elif tipo == "STRING":
            tokens.append(Token("STRING", lex, lex[1:-1], linha, coluna))
        elif tipo == "VIRGULA":
            tokens.append(Token("VIRGULA", lex, lex, linha, coluna))
        elif tipo == "IGUAL":
            tokens.append(Token("IGUAL", lex, lex, linha, coluna))
        elif tipo == "STRING_ABERTA":
            diags.append(Diagnostico("erro", "léxico",
                                     "string não terminada (faltou fechar aspas)",
                                     linha, coluna))
        else:
            diags.append(Diagnostico("erro", "léxico",
                                     f"caractere inesperado {lex!r}", linha, coluna))

    tokens.append(Token("EOF", "", None, linha, len(texto) - inicio_linha + 1))
    return tokens, diags
