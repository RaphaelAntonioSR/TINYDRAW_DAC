"""Interface de linha de comando: python -m tinydraw arquivo.td [opções]."""
import argparse
import sys
from pathlib import Path

from . import executor
from .ast_nodes import descrever
from .compilador import transpilar


def compilar_e_executar(arq_c: Path, saida: Path, executar_exe: bool) -> int:
    ok, log, exe = executor.compilar(arq_c)
    print(log.rstrip())
    if not ok:
        print("erro: falha ao compilar o C gerado.", file=sys.stderr)
        return 2
    print(f"executável gerado: {exe}")
    if executar_exe:
        print(f"$ {exe}\n")
        codigo, saida_txt = executor.executar(exe, saida)
        print(saida_txt, end="")
        return codigo
    return 0


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tinydraw",
                                 description="Transpilador TinyDraw (.td) -> C")
    ap.add_argument("arquivo", help="programa-fonte na DSL (.td)")
    ap.add_argument("-o", "--saida", default="build", help="diretório de saída (padrão: build)")
    ap.add_argument("--tokens", action="store_true", help="mostra a lista de tokens")
    ap.add_argument("--ast", action="store_true", help="mostra a árvore sintática")
    ap.add_argument("--so-c", action="store_true", help="só gera o .c (não compila)")
    ap.add_argument("--executar", action="store_true", help="compila e executa o programa gerado")
    args = ap.parse_args(argv)

    fonte = Path(args.arquivo)
    try:
        texto = fonte.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as e:
        print(f"erro: não foi possível ler '{fonte}': {e}", file=sys.stderr)
        return 1

    res = transpilar(texto, fonte.name)

    if args.tokens:
        print("== TOKENS ==")
        for t in res.tokens:
            print(f"{t.linha:>3}:{t.coluna:<3} {t.tipo:<10} {t.lexema!r}")
    if args.ast and res.ast is not None:
        print("== AST ==")
        print(descrever(res.ast))

    for d in res.diagnosticos:
        print(d.formatar(fonte.name), file=sys.stderr)
    if not res.sucesso:
        print(f"\nfalha: {len(res.erros)} erro(s), {len(res.avisos)} aviso(s). "
              f"Nenhum código foi gerado.", file=sys.stderr)
        return 1

    saida = Path(args.saida).resolve()
    arq_c = saida / (fonte.stem + ".c")
    try:
        saida.mkdir(parents=True, exist_ok=True)
        arq_c.write_text(res.codigo_c, encoding="utf-8")
    except OSError as e:
        print(f"erro: não foi possível gravar o C gerado: {e}", file=sys.stderr)
        return 1
    print(f"análise concluída ({len(res.avisos)} aviso(s)); C gerado em: {arq_c}")
    if args.so_c:
        return 0
    return compilar_e_executar(arq_c, saida, args.executar)
