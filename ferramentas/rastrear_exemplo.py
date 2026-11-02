"""Grava tokens, AST, tabela e C reais para estudo, sem simular a execução C.

Uso: py ferramentas/rastrear_exemplo.py
Depois: py -m tinydraw exemplos/validos/estudo.td --executar -o build/estudo
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from tinydraw.ast_nodes import descrever
from tinydraw.compilador import transpilar


def main():
    fonte = RAIZ / 'exemplos/validos/estudo.td'
    res = transpilar(fonte.read_text(encoding='utf-8'), fonte.name)
    if not res.sucesso:
        for d in res.diagnosticos:
            print(d.formatar(fonte.name))
        return 1
    pasta = RAIZ / 'build/estudo'
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / 'tokens.txt').write_text('\n'.join(
        f'{t.linha}:{t.coluna} {t.tipo} lexema={t.lexema!r} valor={t.valor!r}'
        for t in res.tokens) + '\n', encoding='utf-8')
    (pasta / 'ast.txt').write_text(descrever(res.ast) + '\n', encoding='utf-8')
    (pasta / 'tabela.txt').write_text('\n'.join(repr(s) for s in res.tabela.todas()) + '\n', encoding='utf-8')
    (pasta / 'estudo.c').write_text(res.codigo_c, encoding='utf-8')
    print(f'Tokens, AST, tabela e C gravados em {pasta}. GCC não foi chamado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
