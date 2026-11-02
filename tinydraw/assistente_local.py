"""Assistente local (offline): interpreta pedidos simples em português, por regras, e escreve
um programa TinyDraw. Não usa internet nem modelos de linguagem.

Entende: tela, retângulo/quadrado (contorno ou preenchido), moldura, linha, ponto, círculo,
triângulo, sol, casa e árvore; cores; medidas ("10 por 5", "lado 6", "raio 4"); posições
("em 3, 4", "no centro", "no canto superior direito"...). Convenção: (x, y) é sempre o canto
superior esquerdo da caixa que envolve a figura. Sem posição, as figuras são distribuídas
automaticamente da esquerda para a direita.

O resultado é TEXTO .td: ele ainda passa por todo o compilador (léxico, sintaxe, semântica).
"""
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .assistente import MODO_LOCAL, ErroAssistente, ResultadoGeracao
from .compilador import transpilar

MAX_TELA = 200
LARGURA_MIN, ALTURA_MIN = 40, 24
MARGEM, ESPACO = 2, 3

# nome -> (rgb, expressão regular em texto normalizado)
CORES: Dict[str, Tuple[Tuple[int, int, int], str]] = {
    "VERMELHO": ((255, 0, 0), r"vermelh[oa]s?"),
    "VERDE": ((0, 160, 0), r"verdes?"),
    "AZUL": ((0, 0, 255), r"azul|azuis"),
    "AMARELO": ((255, 200, 0), r"amarel[oa]s?"),
    "LARANJA": ((255, 140, 0), r"laranjas?"),
    "ROXO": ((120, 0, 160), r"rox[oa]s?|violeta|lilas"),
    "ROSA": ((255, 105, 180), r"rosas?"),
    "MARROM": ((139, 69, 19), r"marrons?"),
    "PRETO": ((0, 0, 0), r"pret[oa]s?"),
    "BRANCO": ((255, 255, 255), r"branc[oa]s?"),
    "CINZA": ((128, 128, 128), r"cinzas?"),
}
_RE_CORES = {n: re.compile(rf"\b(?:{p})\b") for n, (_, p) in CORES.items()}

PALAVRAS_FORMA = {
    "retangulo": "retangulo", "retangulos": "retangulo",
    "quadrado": "retangulo", "quadrados": "retangulo",
    "moldura": "moldura", "molduras": "moldura",
    "linha": "linha", "linhas": "linha",
    "ponto": "ponto", "pontos": "ponto", "pixel": "ponto", "pixels": "ponto",
    "circulo": "circulo", "circulos": "circulo", "bola": "circulo", "bolas": "circulo",
    "triangulo": "triangulo", "triangulos": "triangulo",
    "sol": "sol", "sois": "sol",
    "casa": "casa", "casas": "casa",
    "arvore": "arvore", "arvores": "arvore",
}
_RE_FORMA = re.compile(r"\b(" + "|".join(sorted(PALAVRAS_FORMA, key=len, reverse=True)) + r")\b")
_RE_TELA = re.compile(r"\b(?:tela|canvas|imagem|quadro)\s*(?:de|com|:)?\s*(\d+)\s*(?:x|por)\s*(\d+)")
_RE_CHEIO = re.compile(r"\b(?:preenchid[oa]s?|cheio|cheia|solid[oa]|macic[oa])\b")
_RE_LINHA_PTS = re.compile(r"de\s*\(?\s*(\d+)\s*[,;]\s*(\d+)\s*\)?\s*(?:ate|a)\s*\(?\s*(\d+)\s*[,;]\s*(\d+)\s*\)?")
_RE_POS_XY = re.compile(r"\bx\s*=?\s*(\d+)\s*(?:[,;]|e)?\s*y\s*=?\s*(\d+)")
_RE_POS_EM = re.compile(r"(?:\bem|\bna posicao|\bposicao|\bpos|\ba partir de|\borigem|\bno ponto|\bcoordenadas?)"
                        r"\s*(?:de\s*)?\(?\s*(\d+)\s*[,;]\s*(\d+)\s*\)?")
_RE_POS_PAR = re.compile(r"\(\s*(\d+)\s*[,;]\s*(\d+)\s*\)")
_POS_NOMES = [
    (re.compile(r"canto superior esquerd[oa]"), "sup_esq"),
    (re.compile(r"canto superior direit[oa]"), "sup_dir"),
    (re.compile(r"canto inferior esquerd[oa]"), "inf_esq"),
    (re.compile(r"canto inferior direit[oa]"), "inf_dir"),
    (re.compile(r"\bcentro\b|\bmeio\b"), "centro"),
    (re.compile(r"\btopo\b|\bem cima\b|parte superior"), "topo"),
    (re.compile(r"\bembaixo\b|\bem baixo\b|parte inferior|\bchao\b|\bbase da tela\b"), "base"),
    (re.compile(r"\besquerd[oa]\b"), "esq"),
    (re.compile(r"\bdireit[oa]\b"), "dir"),
]
_RE_PAR_TAM = re.compile(r"(\d+)\s*(?:x|por)\s*(\d+)")
_MEDIDAS = {k: re.compile(rf"\b{k}\s*(?:de\s*)?(\d+)") for k in
            ("largura", "altura", "lado", "raio", "diametro", "base", "comprimento", "tamanho")}

FLUXO = {"retangulo", "casa", "arvore", "triangulo", "circulo", "sol"}


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip()


@dataclass
class Figura:
    tipo: str
    palavra: str
    cor: Optional[str] = None
    cheio: bool = False
    largura: int = 1
    altura: int = 1
    pos: Optional[Tuple] = None            # ("abs", x, y) | ("nome", chave)
    vertical: bool = False                 # só para linhas
    x: int = 0
    y: int = 0
    descartada: bool = False
    redimensionavel: bool = True


def _inteiro(v: int) -> int:
    return max(1, min(int(v), MAX_TELA))


def _impar(d: int) -> int:
    return d if d % 2 == 1 else d + 1


# ------------------------------------------------------------------ leitura do pedido
def _primeira_cor(trecho: str) -> Optional[str]:
    melhor = None
    for nome, rx in _RE_CORES.items():
        m = rx.search(trecho)
        if m and (melhor is None or m.start() < melhor[0]):
            melhor = (m.start(), nome)
    return melhor[1] if melhor else None


def _posicao(trecho: str) -> Optional[Tuple]:
    for rx in (_RE_POS_XY, _RE_POS_EM, _RE_POS_PAR):
        m = rx.search(trecho)
        if m:
            return ("abs", int(m.group(1)), int(m.group(2)))
    for rx, chave in _POS_NOMES:
        if rx.search(trecho):
            return ("nome", chave)
    return None


def _medidas(trecho: str) -> Dict:
    med: Dict = {}
    m = _RE_PAR_TAM.search(trecho)
    if m:
        med["par"] = (int(m.group(1)), int(m.group(2)))
    for k, rx in _MEDIDAS.items():
        m = rx.search(trecho)
        if m:
            med[k] = int(m.group(1))
    return med


def _criar_figura(tipo: str, palavra: str, trecho: str) -> Figura:
    f = Figura(tipo, palavra, cor=_primeira_cor(trecho), cheio=bool(_RE_CHEIO.search(trecho)))
    med = _medidas(trecho)
    quadrado = palavra.startswith("quadrad")

    if tipo == "linha":
        m = _RE_LINHA_PTS.search(trecho)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            if x1 != x2 and y1 != y2:
                raise ErroAssistente("A TinyDraw só tem linhas horizontais ou verticais; "
                                     "diagonais não são suportadas.")
            f.vertical = (x1 == x2 and y1 != y2)
            f.pos = ("abs", min(x1, x2), min(y1, y2))
            comp = abs(x1 - x2) + abs(y1 - y2) + 1
        else:
            f.vertical = "vertical" in trecho
            comp = med.get("comprimento") or med.get("tamanho") or (
                med.get("altura") if f.vertical else med.get("largura")) or 10
            f.pos = _posicao(trecho)
        comp = _inteiro(comp)
        f.largura, f.altura = (1, comp) if f.vertical else (comp, 1)
        return f

    f.pos = _posicao(trecho)
    if tipo == "retangulo":
        if "par" in med:
            f.largura, f.altura = med["par"]
        else:
            lado = med.get("lado") or med.get("tamanho")
            if lado:
                f.largura = f.altura = lado
            else:
                f.largura = med.get("largura") or (8 if quadrado else 12)
                f.altura = med.get("altura") or (8 if quadrado else 6)
    elif tipo == "moldura":
        f.largura = f.altura = 0                      # resolvido com o tamanho da tela
        if "par" in med:
            f.largura, f.altura = med["par"]
    elif tipo in ("circulo", "sol"):
        d = (med.get("diametro") or (2 * med["raio"] + 1 if "raio" in med else None)
             or med.get("lado") or med.get("tamanho") or (7 if tipo == "sol" else 11))
        f.largura = f.altura = _impar(_inteiro(d))
    elif tipo == "triangulo":
        if "par" in med:
            f.largura, f.altura = med["par"]
        else:
            base = med.get("base") or med.get("lado") or med.get("largura") or med.get("tamanho") or 11
            f.largura, f.altura = base, med.get("altura") or (base + 1) // 2
    elif tipo == "casa":
        f.largura, f.altura, f.redimensionavel = 21, 17, False
    elif tipo == "arvore":
        f.largura, f.altura, f.redimensionavel = 9, 14, False
    elif tipo == "ponto":
        f.largura = f.altura = 1
    if tipo != "moldura":
        f.largura, f.altura = _inteiro(f.largura), _inteiro(f.altura)
    else:
        f.largura, f.altura = (_inteiro(f.largura) if f.largura else 0,
                               _inteiro(f.altura) if f.altura else 0)
    return f


# ------------------------------------------------------------------ layout
def _clamp(f: Figura, W: int, H: int) -> bool:
    nx, ny = max(0, min(f.x, W - f.largura)), max(0, min(f.y, H - f.altura))
    mudou = (nx, ny) != (f.x, f.y)
    f.x, f.y = nx, ny
    return mudou


def _posicao_nomeada(chave: str, f: Figura, W: int, H: int) -> Tuple[int, int]:
    cx, cy = (W - f.largura) // 2, (H - f.altura) // 2
    return {
        "centro": (cx, cy), "topo": (cx, 1), "base": (cx, H - f.altura - 1),
        "esq": (1, cy), "dir": (W - f.largura - 1, cy),
        "sup_esq": (1, 1), "sup_dir": (W - f.largura - 1, 1),
        "inf_esq": (1, H - f.altura - 1), "inf_dir": (W - f.largura - 1, H - f.altura - 1),
    }[chave]


def _layout(figs: List[Figura], tela: Optional[Tuple[int, int]], notas: List[str]) -> Tuple[int, int]:
    fluxo = [f for f in figs if f.pos is None and f.tipo in FLUXO]
    if tela:
        W, H = tela
    else:
        soma = sum(f.largura for f in fluxo) + ESPACO * max(len(fluxo) - 1, 0)
        W = max(LARGURA_MIN, soma + 2 * MARGEM)
        H = max(ALTURA_MIN, max([f.altura for f in figs] + [0]) + 2 * MARGEM)
        for f in figs:
            if f.pos and f.pos[0] == "abs":
                W, H = max(W, f.pos[1] + f.largura + 1), max(H, f.pos[2] + f.altura + 1)
        W, H = min(W, MAX_TELA), min(H, MAX_TELA)

    for f in figs:                                    # ajusta ao tamanho da tela
        if f.tipo == "moldura":
            f.largura, f.altura = f.largura or W, f.altura or H
        if f.largura > W or f.altura > H:
            if f.redimensionavel:
                f.largura, f.altura = min(f.largura, W), min(f.altura, H)
                if f.tipo in ("circulo", "sol"):          # disco: quadrado de lado ímpar
                    d = min(f.largura, f.altura)
                    f.largura = f.altura = max(1, d if d % 2 else d - 1)
                notas.append(f"{f.tipo}: reduzido para caber na tela {W}x{H}.")
            else:
                f.descartada = True
                notas.append(f"{f.tipo}: não coube na tela {W}x{H} e foi ignorado.")

    ativos = [f for f in fluxo if not f.descartada]
    total = sum(f.largura for f in ativos) + ESPACO * max(len(ativos) - 1, 0)
    cursor = max(0, (W - total) // 2)
    for f in ativos:
        f.x = cursor
        f.y = MARGEM if f.tipo == "sol" else H - f.altura - MARGEM
        cursor += f.largura + ESPACO
        _clamp(f, W, H)

    ids_fluxo = {id(a) for a in ativos}
    for f in figs:
        if f.descartada or id(f) in ids_fluxo:
            continue
        if f.pos is None:
            f.x, f.y = ((0, 0) if f.tipo == "moldura" else _posicao_nomeada("centro", f, W, H))
        elif f.pos[0] == "abs":
            f.x, f.y = f.pos[1], f.pos[2]
            if _clamp(f, W, H):
                notas.append(f"{f.tipo}: posição ajustada para caber na tela {W}x{H}.")
        else:
            f.x, f.y = _posicao_nomeada(f.pos[1], f, W, H)
            _clamp(f, W, H)
    return W, H


# ------------------------------------------------------------------ emissão do .td
class Emissor:
    def __init__(self):
        self.cores: Dict[str, Tuple[int, int, int]] = {}
        self.corpo: List[str] = []
        self.ativa: Optional[str] = None

    def usar(self, nome: str):
        self.cores.setdefault(nome, CORES[nome][0])
        if self.ativa != nome:
            self.corpo.append(f"usar {nome}")
            self.ativa = nome

    def ponto(self, x, y):
        self.corpo.append(f"ponto em {x}, {y}")

    def linha(self, x1, y1, x2, y2):
        if (x1, y1) == (x2, y2):
            self.ponto(x1, y1)
        else:
            self.corpo.append(f"linha de {x1}, {y1} ate {x2}, {y2}")

    def retangulo(self, x, y, w, h):
        self.corpo.append(f"retangulo em {x}, {y} tamanho {w} por {h}")

    def cheio(self, x, y, w, h):
        """Emite segmentos na direção que exige menos comandos .td."""
        if w >= h:
            for i in range(h):
                self.linha(x, y + i, x + w - 1, y + i)
        else:
            for j in range(w):
                self.linha(x + j, y, x + j, y + h - 1)

    def disco(self, x, y, d):
        # Cada altura recebe uma corda horizontal aproximada do disco.
        # Isso compõe comandos da DSL; não desenha pixels em Python.
        r, c = d / 2, (d - 1) / 2
        for i in range(d):
            meio = int(math.floor(math.sqrt(max(r * r - (i - c) ** 2, 0))))
            self.linha(x + int(c) - meio, y + i, x + int(c) + meio, y + i)

    def triangulo(self, x, y, w, h):
        """Aumenta a meia largura por altura e emite linhas horizontais."""
        cx, meia = x + (w - 1) // 2, (w - 1) // 2
        for i in range(h):
            k = int(round(meia * i / max(h - 1, 1)))
            self.linha(cx - k, y + i, cx + k, y + i)


def _desenhar(e: Emissor, f: Figura):
    t = f.tipo
    e.corpo.append(f"# {t}" + (f" {f.cor.lower()}" if f.cor else ""))
    if t == "casa":
        parede = f.cor or "MARROM"
        e.usar("MARROM" if parede == "VERMELHO" else "VERMELHO"); e.triangulo(f.x, f.y, 21, 7)
        e.usar(parede); e.retangulo(f.x + 2, f.y + 7, 17, 10)
        e.usar("MARROM" if parede == "AZUL" else "AZUL"); e.retangulo(f.x + 9, f.y + 12, 4, 5)
    elif t == "arvore":
        e.usar(f.cor or "VERDE"); e.disco(f.x, f.y, 9)
        e.usar("PRETO" if f.cor == "MARROM" else "MARROM"); e.cheio(f.x + 3, f.y + 9, 3, 5)
    elif t == "sol":
        e.usar(f.cor or "AMARELO"); e.disco(f.x, f.y, f.largura)
    elif t == "circulo":
        e.usar(f.cor or "PRETO"); e.disco(f.x, f.y, f.largura)
    elif t == "triangulo":
        e.usar(f.cor or "PRETO"); e.triangulo(f.x, f.y, f.largura, f.altura)
    elif t == "retangulo":
        e.usar(f.cor or "PRETO")
        (e.cheio if f.cheio else e.retangulo)(f.x, f.y, f.largura, f.altura)
    elif t == "moldura":
        e.usar(f.cor or "PRETO"); e.retangulo(f.x, f.y, f.largura, f.altura)
    elif t == "linha":
        e.usar(f.cor or "PRETO")
        e.linha(f.x, f.y, f.x + f.largura - 1, f.y + f.altura - 1)
    elif t == "ponto":
        e.usar(f.cor or "PRETO"); e.ponto(f.x, f.y)


def interpretar(pedido: str):
    """Devolve (programa_td, notas). Levanta ErroAssistente se não entender."""
    t = normalizar(pedido)
    tela = None
    m = _RE_TELA.search(t)
    if m:
        tela = (_inteiro(m.group(1)), _inteiro(m.group(2)))
        t = t[:m.start()] + " " + t[m.end():]
    achados = list(_RE_FORMA.finditer(t))
    if not achados:
        raise ErroAssistente(
            "Não entendi o pedido. O assistente local reconhece: retângulo, quadrado, moldura, linha, "
            "ponto, círculo, triângulo, sol, casa e árvore.\n"
            "Exemplos:\n  uma casa vermelha, uma árvore e um sol\n"
            "  retângulo azul de 20 por 8 em 5, 4\n  tela 60 por 30, círculo amarelo de raio 6 no centro")
    figs = []
    for i, m in enumerate(achados):
        fim = achados[i + 1].start() if i + 1 < len(achados) else len(t)
        figs.append(_criar_figura(PALAVRAS_FORMA[m.group(1)], m.group(1), t[m.end():fim]))

    notas: List[str] = []
    W, H = _layout(figs, tela, notas)
    notas.insert(0, f"Tela: {W} por {H} ({'definida no pedido' if tela else 'automática'}).")
    e = Emissor()
    for f in figs:
        if not f.descartada:
            _desenhar(e, f)
            notas.append(f"Figura: {f.tipo}{' ' + f.cor.lower() if f.cor else ''} "
                         f"{f.largura}x{f.altura} em ({f.x}, {f.y}).")
    resumo = re.sub(r"\s+", " ", pedido).strip()[:90]
    linhas = [f"# Programa gerado pelo assistente local a partir do pedido: {resumo}",
              f"tela {W} por {H}"]
    linhas += [f"cor {n} = {r}, {g}, {b}" for n, (r, g, b) in e.cores.items()]
    linhas += [""] + e.corpo + ["", 'salvar "desenho.ppm"']
    return "\n".join(linhas) + "\n", notas


def gerar_local(pedido: str, progresso: Optional[Callable[[str], None]] = None) -> ResultadoGeracao:
    (progresso or (lambda _m: None))("Interpretando o pedido (assistente local)...")
    codigo, notas = interpretar(pedido)
    log = ["Modo: assistente local (regras, sem internet)", f"Pedido: {pedido}"] + notas
    res = transpilar(codigo)
    log.append("Compilador TinyDraw: programa ACEITO." if res.sucesso else
               "Compilador TinyDraw: programa REJEITADO (veja Diagnósticos).")
    return ResultadoGeracao(codigo, res.sucesso, log, MODO_LOCAL)
