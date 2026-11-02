"""Preferências do Studio (modo, modelo e, se o usuário permitir, a chave de API)."""
import json
from pathlib import Path

ARQUIVO = Path.home() / ".tinydraw_studio.json"


def carregar() -> dict:
    try:
        dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def salvar(dados: dict) -> None:
    try:
        ARQUIVO.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass            # preferências são opcionais; nunca derrubar o programa por isso
