"""Analisador sintático descendente recursivo (gramática LL(1))."""
from typing import List

from . import ast_nodes as ast
from .erros import Diagnostico, ErroDeCompilacao
from .lexer import Token

COMANDOS = ["tela", "cor", "usar", "ponto", "linha", "retangulo", "salvar"]


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    # --- utilitários ---------------------------------------------------
    def _atual(self) -> Token:
        return self.tokens[self.i]

    @staticmethod
    def _descrever(tok: Token) -> str:
        return "fim do arquivo" if tok.tipo == "EOF" else f"'{tok.lexema}'"

    def _erro(self, esperado: str) -> ErroDeCompilacao:
        tok = self._atual()
        msg = f"esperado {esperado}, encontrado {self._descrever(tok)}"
        return ErroDeCompilacao([Diagnostico("erro", "sintático", msg,
                                             tok.linha, tok.coluna)])

    def _consumir(self, tipo: str, descricao: str) -> Token:
        if self._atual().tipo != tipo:
            raise self._erro(descricao)
        tok = self._atual()
        self.i += 1
        return tok

    def _inteiro(self) -> int:
        return self._consumir("INT", "um número inteiro").valor

    def _par(self):
        x = self._inteiro()
        self._consumir("VIRGULA", "','")
        return x, self._inteiro()

    # --- regras da gramática ------------------------------------------
    def analisar(self) -> ast.Programa:
        """programa = { comando } EOF"""
        prog = ast.Programa()
        while self._atual().tipo != "EOF":
            prog.comandos.append(self._comando())
        return prog

    def _comando(self) -> ast.Comando:
        # Inícios distintos permitem escolher a produção com um token de
        # antecipação, sem tentar e desfazer alternativas.
        tok = self._atual()
        metodo = {
            "TELA": self._tela, "COR": self._cor, "USAR": self._usar,
            "PONTO": self._ponto, "LINHA": self._linha,
            "RETANGULO": self._retangulo, "SALVAR": self._salvar,
        }.get(tok.tipo)
        if metodo is None:
            raise self._erro("um comando (" + ", ".join(COMANDOS) + ")")
        self.i += 1
        return metodo(tok)

    def _tela(self, t):
        l = self._inteiro()
        self._consumir("POR", "'por'")
        return ast.Tela(t.linha, t.coluna, l, self._inteiro())

    def _cor(self, t):
        nome = self._consumir("ID", "o nome da cor").valor
        self._consumir("IGUAL", "'='")
        r = self._inteiro(); self._consumir("VIRGULA", "','")
        g = self._inteiro(); self._consumir("VIRGULA", "','")
        return ast.DefCor(t.linha, t.coluna, nome, r, g, self._inteiro())

    def _usar(self, t):
        return ast.Usar(t.linha, t.coluna,
                        self._consumir("ID", "o nome da cor").valor)

    def _ponto(self, t):
        self._consumir("EM", "'em'")
        x, y = self._par()
        return ast.Ponto(t.linha, t.coluna, x, y)

    def _linha(self, t):
        self._consumir("DE", "'de'")
        x1, y1 = self._par()
        self._consumir("ATE", "'ate'")
        x2, y2 = self._par()
        return ast.Linha(t.linha, t.coluna, x1, y1, x2, y2)

    def _retangulo(self, t):
        self._consumir("EM", "'em'")
        x, y = self._par()
        self._consumir("TAMANHO", "'tamanho'")
        w = self._inteiro()
        self._consumir("POR", "'por'")
        return ast.Retangulo(t.linha, t.coluna, x, y, w, self._inteiro())

    def _salvar(self, t):
        return ast.Salvar(t.linha, t.coluna,
                          self._consumir("STRING", "um nome de arquivo entre aspas").valor)
