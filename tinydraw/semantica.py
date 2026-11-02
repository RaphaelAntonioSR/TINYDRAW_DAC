"""Análise semântica: tabela de símbolos e regras de contexto do domínio."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import ast_nodes as ast
from .erros import Diagnostico

MAX_DIMENSAO = 1000
MAX_CORES = 255          # índice 0 da paleta é reservado ao fundo
EXTENSAO_PERMITIDA = ".ppm"


@dataclass
class Simbolo:
    nome: str
    r: int
    g: int
    b: int
    linha: int
    indice: int          # posição na paleta (1..n); 0 = fundo
    usada: bool = False


class TabelaDeSimbolos:
    """Mapeia nomes a RGB e metadados; buscar retorna None para nome ausente."""
    def __init__(self):
        self._cores: Dict[str, Simbolo] = {}

    def declarar(self, nome, r, g, b, linha) -> Optional[Simbolo]:
        if nome in self._cores:
            return None
        s = Simbolo(nome, r, g, b, linha, len(self._cores) + 1)
        self._cores[nome] = s
        return s

    def buscar(self, nome) -> Optional[Simbolo]:
        return self._cores.get(nome)

    def todas(self) -> List[Simbolo]:
        return list(self._cores.values())


class Analisador:
    def __init__(self):
        self.tabela = TabelaDeSimbolos()
        self.diags: List[Diagnostico] = []
        self.tela_declarada = False
        self.dim: Optional[Tuple[int, int]] = None   # só se válida
        self.cor_ativa: Optional[Simbolo] = None
        self.salvo = False

    # --- emissão ---------------------------------------------------------
    def _erro(self, c, msg):
        self.diags.append(Diagnostico("erro", "semântico", msg, c.linha, c.coluna))

    def _aviso(self, c, msg):
        self.diags.append(Diagnostico("aviso", "semântico", msg, c.linha, c.coluna))

    # --- verificações auxiliares --------------------------------------------
    def _exige_tela(self, c, nome_cmd) -> bool:
        if not self.tela_declarada:
            self._erro(c, f"'{nome_cmd}' usado antes de declarar a 'tela'")
            return False
        return self.dim is not None

    def _exige_cor(self, c, nome_cmd) -> bool:
        if self.cor_ativa is None:
            self._erro(c, f"nenhuma cor selecionada para '{nome_cmd}'; use 'usar NOME' antes")
            return False
        return True

    def _dentro(self, c, x, y, rotulo) -> bool:
        w, h = self.dim
        if not (0 <= x < w and 0 <= y < h):
            self._erro(c, f"{rotulo} ({x}, {y}) fora da tela {w}x{h} "
                          f"(x deve estar em 0..{w-1} e y em 0..{h-1})")
            return False
        return True

    # --- ponto de entrada --------------------------------------------------
    def analisar(self, prog: ast.Programa):
        """Retorna (tabela, diagnósticos), respeitando a ordem dos comandos.

        O estado registra declaração antes do uso e cor ativa. Acumular erros
        ajuda a corrigir a fonte; o orquestrador bloqueia a geração de C.
        """
        for c in prog.comandos:
            if self.salvo:
                self._erro(c, "comando após 'salvar' (o desenho já foi gravado)")
                if isinstance(c, ast.Salvar):
                    continue
            handler = {
                ast.Tela: self._tela, ast.DefCor: self._cor, ast.Usar: self._usar,
                ast.Ponto: self._ponto, ast.Linha: self._linha,
                ast.Retangulo: self._retangulo, ast.Salvar: self._salvar,
            }[type(c)]
            handler(c)

        fim = prog.comandos[-1] if prog.comandos else ast.Comando(1, 1)
        if not self.tela_declarada:
            self._erro(fim, "programa sem declaração de 'tela'")
        if not self.salvo:
            self._erro(fim, "programa sem comando 'salvar'")
        for s in self.tabela.todas():
            if not s.usada:
                self.diags.append(Diagnostico(
                    "aviso", "semântico",
                    f"cor '{s.nome}' declarada mas nunca selecionada com 'usar'",
                    s.linha, 1))
        self.diags.sort(key=lambda d: (d.linha, d.coluna))
        return self.tabela, self.diags

    # --- regras por comando ---------------------------------------------------
    def _tela(self, c: ast.Tela):
        if self.tela_declarada:
            self._erro(c, "a 'tela' já foi declarada (só é permitida uma)")
            return
        self.tela_declarada = True
        if c.largura <= 0 or c.altura <= 0:
            self._erro(c, "dimensões da tela devem ser inteiros positivos")
        elif c.largura > MAX_DIMENSAO or c.altura > MAX_DIMENSAO:
            self._erro(c, f"dimensões da tela excedem o máximo de {MAX_DIMENSAO}")
        else:
            self.dim = (c.largura, c.altura)

    def _cor(self, c: ast.DefCor):
        for rotulo, v in (("R", c.r), ("G", c.g), ("B", c.b)):
            if not 0 <= v <= 255:
                self._erro(c, f"componente {rotulo} da cor '{c.nome}' vale {v}; "
                              f"deve estar entre 0 e 255")
        if len(self.tabela.todas()) >= MAX_CORES:
            self._erro(c, f"limite de {MAX_CORES} cores excedido")
            return
        if self.tabela.declarar(c.nome, c.r, c.g, c.b, c.linha) is None:
            anterior = self.tabela.buscar(c.nome)
            self._erro(c, f"cor '{c.nome}' já declarada na linha {anterior.linha}")

    def _usar(self, c: ast.Usar):
        s = self.tabela.buscar(c.nome)
        if s is None:
            self._erro(c, f"cor '{c.nome}' não foi declarada")
            return
        s.usada = True
        self.cor_ativa = s

    def _ponto(self, c: ast.Ponto):
        if self._exige_tela(c, "ponto") and self._exige_cor(c, "ponto"):
            self._dentro(c, c.x, c.y, "ponto")

    def _linha(self, c: ast.Linha):
        if not (self._exige_tela(c, "linha") and self._exige_cor(c, "linha")):
            return
        ok1 = self._dentro(c, c.x1, c.y1, "início da linha")
        ok2 = self._dentro(c, c.x2, c.y2, "fim da linha")
        if c.x1 != c.x2 and c.y1 != c.y2:
            self._erro(c, "linha deve ser horizontal (mesmo y) ou vertical (mesmo x); "
                          "diagonais não são suportadas")
        elif ok1 and ok2 and (c.x1, c.y1) == (c.x2, c.y2):
            self._aviso(c, "linha degenerada (início = fim); equivale a um 'ponto'")

    def _retangulo(self, c: ast.Retangulo):
        if not (self._exige_tela(c, "retangulo") and self._exige_cor(c, "retangulo")):
            return
        if c.largura <= 0 or c.altura <= 0:
            self._erro(c, "largura e altura do retângulo devem ser inteiros positivos")
            return
        if self._dentro(c, c.x, c.y, "canto do retângulo"):
            w, h = self.dim
            fx, fy = c.x + c.largura - 1, c.y + c.altura - 1
            if fx >= w or fy >= h:
                self._erro(c, f"retângulo ultrapassa a tela {w}x{h} "
                              f"(canto oposto seria ({fx}, {fy}))")

    def _salvar(self, c: ast.Salvar):
        nome = c.arquivo
        if not nome.lower().endswith(EXTENSAO_PERMITIDA) or len(nome) <= len(EXTENSAO_PERMITIDA):
            self._erro(c, f"arquivo '{nome}' inválido: use nome não vazio com "
                          f"extensão {EXTENSAO_PERMITIDA}")
        if any(ch in nome for ch in '/\\:'):
            self._erro(c, f"arquivo '{nome}' inválido: informe apenas o nome, "
                          f"sem pastas (não use / \\ ou :)")
        # Nomes aceitos no Linux também precisam ser graváveis no Windows.
        base = nome.split(".", 1)[0].upper()
        reservados = {"CON", "PRN", "AUX", "NUL"} | {
            f"{prefixo}{n}" for prefixo in ("COM", "LPT") for n in range(1, 10)
        }
        if (any(ord(ch) < 32 or ch in '<>"|?*' for ch in nome)
                or nome.endswith((" ", ".")) or base in reservados):
            self._erro(c, "nome de arquivo incompatível com Windows")
        if not self.tela_declarada:
            self._erro(c, "'salvar' usado antes de declarar a 'tela'")
        self.salvo = True
