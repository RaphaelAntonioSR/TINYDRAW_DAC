"""Geração de código C a partir da AST validada."""
from typing import Dict

from . import ast_nodes as ast
from .semantica import TabelaDeSimbolos

_RESERVA = "#%@*+&$=?!"


def _escapar_c(s: str) -> str:
    """Escapa um texto para literal de string em C (usado só como argumento de %s)."""
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("?", "\\?"))


def atribuir_simbolos(tabela: TabelaDeSimbolos) -> Dict[str, str]:
    """Escolhe um caractere ASCII por cor (inicial do nome, sem repetição)."""
    usados, resultado = {"."}, {}
    for s in tabela.todas():
        candidatos = [ch.upper() for ch in s.nome if ch.isascii() and ch.isalnum()]
        candidatos += list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + list(_RESERVA)
        for ch in candidatos:
            if ch not in usados:
                usados.add(ch)
                resultado[s.nome] = ch
                break
        else:                       # esgotou: reaproveita (apenas visual)
            resultado[s.nome] = "?"
    return resultado


class Gerador:
    def __init__(self, programa: ast.Programa, tabela: TabelaDeSimbolos):
        self.prog = programa
        self.tabela = tabela
        self.simbolos = atribuir_simbolos(tabela)
        self.saida = []

    def _e(self, texto=""):
        self.saida.append(texto)

    def gerar(self, origem: str = "programa.td") -> str:
        tela = next(c for c in self.prog.comandos if isinstance(c, ast.Tela))
        self._e(f"/* Código gerado automaticamente pelo transpilador TinyDraw. */")
        self._e(f"/* Origem: {origem.replace('*/', '* /').replace(chr(10), ' ').replace(chr(13), ' ')} -- não edite manualmente. */")
        self._e('#include <stdio.h>')
        self._e('#include "tinydraw.h"')
        self._e()
        self._e("int main(void) {")
        self._e(f"    TDCanvas *c = td_criar({tela.largura}, {tela.altura});")
        self._e('    if (!c) { fprintf(stderr, "erro: memoria insuficiente\\n"); return 1; }')
        self._e(f'    printf("[linha {tela.linha}] tela {tela.largura} por {tela.altura}\\n");')
        # O identificador C é numérico: nomes Unicode da DSL ficam em strings,
        # sem depender das regras de identificadores do compilador C.
        cores: Dict[str, str] = {}
        for c in self.prog.comandos:
            if isinstance(c, ast.Tela):
                continue
            self._e(f"    /* linha {c.linha} */")
            if isinstance(c, ast.DefCor):
                ident = f"cor_{len(cores) + 1}"
                cores[c.nome] = ident
                self._e(f'    int {ident} = td_definir_cor(c, "{_escapar_c(c.nome)}", '
                        f"{c.r}, {c.g}, {c.b}, '{self.simbolos[c.nome]}');")
                self._e(f'    printf("[linha {c.linha}] cor %s = ({c.r}, {c.g}, {c.b}) '
                        f'simbolo %c\\n", "{_escapar_c(c.nome)}", \'{self.simbolos[c.nome]}\');')
            elif isinstance(c, ast.Usar):
                self._e(f"    td_usar(c, {cores[c.nome]});")
                self._e(f'    printf("[linha {c.linha}] usar %s\\n", "{_escapar_c(c.nome)}");')
            elif isinstance(c, ast.Ponto):
                self._e(f"    td_ponto(c, {c.x}, {c.y});")
                self._e(f'    printf("[linha {c.linha}] ponto em ({c.x}, {c.y})\\n");')
            elif isinstance(c, ast.Linha):
                self._e(f"    td_linha(c, {c.x1}, {c.y1}, {c.x2}, {c.y2});")
                self._e(f'    printf("[linha {c.linha}] linha ({c.x1}, {c.y1}) -> ({c.x2}, {c.y2})\\n");')
            elif isinstance(c, ast.Retangulo):
                self._e(f"    td_retangulo(c, {c.x}, {c.y}, {c.largura}, {c.altura});")
                self._e(f'    printf("[linha {c.linha}] retangulo em ({c.x}, {c.y}) '
                        f'tamanho {c.largura} x {c.altura}\\n");')
            elif isinstance(c, ast.Salvar):
                arq = _escapar_c(c.arquivo)
                self._e(f'    if (td_salvar(c, "{arq}") != 0) {{')
                self._e('        td_liberar(c);')
                self._e('        return 1;')
                self._e('    }')
                self._e(f'    printf("[linha {c.linha}] salvar %s\\n", "{arq}");')
        self._e("    td_imprimir_ascii(c);")
        self._e("    td_liberar(c);")
        self._e("    return 0;")
        self._e("}")
        return "\n".join(self.saida) + "\n"
