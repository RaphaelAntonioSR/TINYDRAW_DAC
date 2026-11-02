"""Compilação do C gerado e execução do programa resultante."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from .caminhos import pasta_do_executavel, pasta_runtime

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # evita piscar console no Windows


def achar_compilador_c() -> Optional[Path]:
    """Procura gcc/cc/clang: variável CC, pasta 'gcc' ao lado do .exe e depois o PATH."""
    candidatos = []
    if os.environ.get("CC"):
        candidatos.append(os.environ["CC"])
    portatil = pasta_do_executavel() / "gcc" / "bin" / ("gcc.exe" if os.name == "nt" else "gcc")
    if portatil.exists():
        candidatos.append(str(portatil))
    candidatos += ["gcc", "cc", "clang"]
    for nome in candidatos:
        achado = shutil.which(nome)
        if achado:
            return Path(achado)
    return None


def _ambiente(cc: Path) -> Dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(cc.parent) + os.pathsep + env.get("PATH", "")
    return env


def nome_executavel(arq_c: Path) -> Path:
    return arq_c.with_suffix(".exe" if os.name == "nt" else "")


def compilar(arq_c: Path) -> Tuple[bool, str, Optional[Path]]:
    """Compila arq_c junto da biblioteca runtime. Devolve (ok, log, caminho_do_exe)."""
    cc = achar_compilador_c()
    if cc is None:
        return False, ("Nenhum compilador C (gcc/cc/clang) foi encontrado.\n"
                       "Instale o gcc (ex.: winget install -e --id BrechtSanders.WinLibs.POSIX.UCRT) "
                       "e reabra o programa."), None
    runtime = pasta_runtime()
    exe = nome_executavel(arq_c)
    cmd = [str(cc), "-std=c99", "-Wall", "-Wextra", "-o", str(exe), str(arq_c),
           str(runtime / "tinydraw.c"), f"-I{runtime}"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=_ambiente(cc), creationflags=_SEM_JANELA,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Falha ao iniciar ou concluir a compilação C: {e}", None
    log = "$ " + " ".join(cmd) + "\n" + (p.stdout or "") + (p.stderr or "")
    return p.returncode == 0, log, (exe if p.returncode == 0 else None)


def executar(exe: Path, cwd: Path, limite_s: int = 20) -> Tuple[int, str]:
    """Roda o executável gerado; devolve (código_de_saída, stdout+stderr)."""
    try:
        p = subprocess.run([str(exe)], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=limite_s,
                           creationflags=_SEM_JANELA)
    except OSError as e:
        return 126, f"erro: não foi possível iniciar o executável: {e}"
    except subprocess.TimeoutExpired:
        return 124, f"erro: a execução passou de {limite_s} s e foi interrompida."
    return p.returncode, (p.stdout or "") + (p.stderr or "")
