"""Fluxo completo usado pelo Studio: .td -> análise -> C -> compilação -> execução -> imagem."""
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from . import __version__, caminhos, executor
from . import ast_nodes as ast
from .compilador import Resultado, transpilar
from .imagem import fator_para_caber, ler_ppm, rgb_para_png

ETAPAS = ["Léxico", "Sintaxe", "Semântica", "Gerar C", "Compilar C", "Executar", "Imagem"]


@dataclass
class ResultadoExecucao:
    transp: Resultado
    arquivo_td: Optional[Path] = None
    arquivo_c: Optional[Path] = None
    exe: Optional[Path] = None
    log_compilacao: str = ""
    compilou: Optional[bool] = None       # None = nem tentou
    executou: Optional[bool] = None
    saida_execucao: str = ""
    ppm: Optional[Path] = None
    png: Optional[bytes] = None
    largura: int = 0
    altura: int = 0
    ampliacao: int = 1
    sem_compilador: bool = False


def executar_programa(texto: str, pasta_saida=None, nome_base: str = "desenho",
                      area: Tuple[int, int] = (720, 520)) -> ResultadoExecucao:
    """Processa texto .td até a prévia e retorna ResultadoExecucao.

    pasta_saida recebe os artefatos; nome_base nomeia fonte/C/executável.
    O nome PPM vem de salvar. area só determina a ampliação visual.
    Erros de análise ou compilação devolvem o estado parcial, sem prévia.
    """
    pasta = Path(pasta_saida) if pasta_saida else caminhos.pasta_saida_padrao()
    pasta.mkdir(parents=True, exist_ok=True)
    arq_td = pasta / f"{nome_base}.td"
    arq_td.write_text(texto, encoding="utf-8")

    t = transpilar(texto, arq_td.name)
    res = ResultadoExecucao(transp=t, arquivo_td=arq_td)
    if not t.sucesso:
        return res

    res.arquivo_c = pasta / f"{nome_base}.c"
    res.arquivo_c.write_text(t.codigo_c, encoding="utf-8")
    nome_ppm = next(c.arquivo for c in t.ast.comandos if isinstance(c, ast.Salvar))
    alvo_ppm = pasta / nome_ppm
    if alvo_ppm.exists():
        alvo_ppm.unlink()                 # nunca mostrar imagem antiga

    ok, log, exe = executor.compilar(res.arquivo_c)
    res.compilou, res.log_compilacao, res.exe = ok, log, exe
    if not ok:
        res.sem_compilador = "Nenhum compilador C" in log
        return res

    codigo, saida = executor.executar(exe, pasta)
    res.saida_execucao, res.executou = saida, codigo == 0
    if res.executou and alvo_ppm.exists():
        w, h, rgb = ler_ppm(alvo_ppm.read_bytes())
        fator = fator_para_caber(w, h, *area)
        res.png = rgb_para_png(w, h, rgb, fator)
        res.ppm, res.largura, res.altura, res.ampliacao = alvo_ppm, w, h, fator
    return res


def etapas(res: Optional[ResultadoExecucao]) -> List[Tuple[str, str]]:
    """Estado de cada etapa: 'ok', 'erro' ou 'pendente' (para a barra de progresso da interface)."""
    est = {n: "pendente" for n in ETAPAS}
    if res is None:
        return [(n, est[n]) for n in ETAPAS]
    t = res.transp
    fases = {d.fase for d in t.erros}
    analise = [("léxico", "Léxico"), ("sintático", "Sintaxe"), ("semântico", "Semântica")]
    for fase, nome in analise:
        if fase in fases:
            est[nome] = "erro"
            return [(n, est[n]) for n in ETAPAS]
        est[nome] = "ok"
    est["Gerar C"] = "ok" if t.codigo_c else "erro"
    if res.compilou is not None:
        est["Compilar C"] = "ok" if res.compilou else "erro"
        if res.compilou:
            est["Executar"] = "ok" if res.executou else "erro"
            if res.executou:
                est["Imagem"] = "ok" if res.png else "erro"
    return [(n, est[n]) for n in ETAPAS]


def diagnostico_ambiente() -> str:
    cc = executor.achar_compilador_c()
    versao_cc = ""
    if cc:
        try:
            p = subprocess.run([str(cc), "--version"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            versao_cc = (p.stdout or p.stderr).splitlines()[0] if (p.stdout or p.stderr) else ""
        except Exception:
            pass
    ok_rt = (caminhos.pasta_runtime() / "tinydraw.c").exists()
    ok_ex = caminhos.pasta_exemplos().exists()
    return "\n".join([
        f"TinyDraw Studio {__version__}",
        f"Python {sys.version.split()[0]} ({'executável empacotado' if caminhos.empacotado() else 'código-fonte'})",
        f"Recursos em: {caminhos.raiz_recursos()}",
        f"Biblioteca C (runtime/tinydraw.c): {'OK' if ok_rt else 'NÃO ENCONTRADA'}",
        f"Exemplos: {'OK' if ok_ex else 'NÃO ENCONTRADOS'}",
        f"Compilador C: {cc if cc else 'NÃO ENCONTRADO - instale o gcc (veja o README)'}",
        f"   {versao_cc}" if versao_cc else "",
        f"Pasta de saída: {caminhos.pasta_saida_padrao()}",
    ]).replace("\n\n", "\n")


def autoteste() -> Tuple[bool, str]:
    """Roda o exemplo casa.td de ponta a ponta e informa se tudo funciona neste computador."""
    partes = [diagnostico_ambiente(), ""]
    exemplo = caminhos.pasta_exemplos() / "validos" / "casa.td"
    if not exemplo.exists():
        return False, "\n".join(partes + ["FALHA: exemplo casa.td não encontrado."])
    pasta = Path(tempfile.mkdtemp(prefix="tinydraw_autoteste_"))
    try:
        res = executar_programa(exemplo.read_text(encoding="utf-8"), pasta, "autoteste")
    finally:
        shutil.rmtree(pasta, ignore_errors=True)       # não deixa lixo no computador
    for nome, estado in etapas(res):
        partes.append(f"  [{estado.upper():8}] {nome}")
    ok = res.png is not None
    partes.append("")
    partes.append("RESULTADO: tudo funcionando." if ok else "RESULTADO: FALHA (veja a etapa marcada acima).")
    if res.sem_compilador:
        partes.append("Motivo: gcc não encontrado.")
    return ok, "\n".join(partes)
