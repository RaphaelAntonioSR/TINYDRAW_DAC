"""Assistente com IA: usa a API da Anthropic (Claude) para escrever programas TinyDraw.

A IA só produz TEXTO na linguagem TinyDraw. Cada resposta passa pelo compilador do projeto;
se for rejeitada, os diagnósticos (linha, coluna, motivo) voltam para a IA corrigir.
Só usa a biblioteca padrão (urllib), então empacota fácil em .exe.
"""
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .assistente import MODO_CLAUDE, ErroAssistente, ResultadoGeracao
from .compilador import transpilar

URL_API = "https://api.anthropic.com/v1/messages"
VERSAO_API = "2023-06-01"
MODELOS_SUGERIDOS = ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"]
MAX_TENTATIVAS = 3


@dataclass
class ConfigClaude:
    chave: str = ""
    modelo: str = MODELOS_SUGERIDOS[0]
    max_tokens: int = 6000
    timeout_s: int = 120


PROMPT_SISTEMA = '''\
Você é o assistente do TinyDraw Studio. Sua única tarefa é converter pedidos de desenho, escritos
em português, em programas válidos da linguagem TinyDraw. Você NÃO desenha: você escreve o programa;
um compilador próprio o valida, gera C e produz a imagem.

FORMATO DA RESPOSTA: somente o programa, dentro de UM bloco de código ```tinydraw ... ```.
Nada de explicações fora do bloco. Comentários com # dentro do programa são permitidos.

LINGUAGEM TINYDRAW (palavras reservadas em minúsculas, sem acento):
  tela LARGURA por ALTURA                        obrigatório, uma única vez, primeiro comando
  cor NOME = R, G, B                             NOME em MAIÚSCULAS/dígitos/_, sem acento; R,G,B de 0 a 255
  usar NOME                                      seleciona a cor ativa (toda figura exige uma cor ativa)
  ponto em X, Y
  linha de X1, Y1 ate X2, Y2                     SOMENTE horizontal (Y1 = Y2) ou vertical (X1 = X2)
  retangulo em X, Y tamanho LARGURA por ALTURA   SOMENTE contorno; (X, Y) = canto superior esquerdo
  salvar "desenho.ppm"                           obrigatório, uma única vez, último comando

REGRAS:
- Origem (0,0) no canto superior esquerdo; x cresce para a direita, y cresce para baixo.
- Tudo deve caber na tela: 0 <= x < LARGURA e 0 <= y < ALTURA. Retângulo: x+LARGURA <= tela.largura
  e y+ALTURA <= tela.altura. Linhas e pontos também precisam estar dentro da tela.
- Apenas números inteiros não negativos. Não há variáveis, expressões, laços, funções nem texto.
- O fundo é branco. O último desenho sobrescreve os anteriores (a ordem dos comandos são as camadas).
- Declare todas as cores antes de usá-las; no máximo 12 cores. Não repita nomes de cores.
- O nome do arquivo deve ser exatamente "desenho.ppm".
- Tela padrão: 48 por 32. Máximo recomendado: 100 por 100. Use a tela pedida pelo usuário, se houver.
- Prefira programas com até cerca de 200 linhas.

COMO DESENHAR O QUE A LINGUAGEM NÃO TEM:
- Preencher uma região: várias linhas horizontais de 1 pixel (uma por valor de y).
- Triângulo/telhado: linhas horizontais empilhadas com larguras crescentes (use "ponto" no vértice).
- Círculo/sol: linhas horizontais empilhadas, largas no meio e estreitas nas pontas.
- Diagonais ou curvas: sequências de pontos ou degraus de linhas curtas.
- Evite linha com início igual ao fim; nesse caso use "ponto".
- Se o pedido for impossível, aproxime com os comandos existentes e explique num comentário #.

EXEMPLO
Pedido: "uma casa com telhado vermelho, porta azul e um sol"
```tinydraw
# casa com sol
tela 48 por 32
cor PAREDE  = 200, 120, 40
cor TELHADO = 220, 30, 30
cor PORTA   = 0, 0, 255
cor SOL     = 255, 200, 0

usar SOL                      # disco feito de linhas horizontais
linha de 38, 3 ate 40, 3
linha de 37, 4 ate 41, 4
linha de 37, 5 ate 41, 5
linha de 37, 6 ate 41, 6
linha de 38, 7 ate 40, 7

usar TELHADO                  # triângulo feito de linhas empilhadas
ponto em 16, 10
linha de 15, 11 ate 17, 11
linha de 14, 12 ate 18, 12
linha de 13, 13 ate 19, 13
linha de 12, 14 ate 20, 14
linha de 11, 15 ate 21, 15
linha de 10, 16 ate 22, 16

usar PAREDE
retangulo em 12, 17 tamanho 9 por 8
usar PORTA
retangulo em 15, 21 tamanho 3 por 4

salvar "desenho.ppm"
```
'''

_RE_BLOCO = re.compile(r"```[a-zA-Z0-9_-]*[ \t]*\r?\n(.*?)```", re.DOTALL)


def extrair_codigo(resposta: str) -> str:
    """Pega o primeiro bloco ``` ... ``` da resposta; se não houver, usa o texto inteiro."""
    m = _RE_BLOCO.search(resposta)
    codigo = m.group(1) if m else resposta
    return codigo.replace("\ufeff", "").strip() + "\n"


def _mensagem_inicial(pedido: str, codigo_atual: Optional[str]) -> str:
    if codigo_atual and codigo_atual.strip():
        return ("Programa TinyDraw atual:\n```tinydraw\n" + codigo_atual.strip() + "\n```\n\n"
                "Altere-o conforme o pedido abaixo e devolva o programa COMPLETO atualizado.\n"
                f"Pedido: {pedido}")
    return f"Pedido: {pedido}"


def _mensagem_correcao(erros) -> str:
    itens = "\n".join(f"- linha {d.linha}, coluna {d.coluna} (erro {d.fase}): {d.mensagem}"
                      for d in erros[:25])
    return ("O compilador TinyDraw rejeitou o programa. Diagnósticos:\n" + itens +
            "\n\nCorrija TODOS os erros e devolva o programa completo, novamente apenas em um "
            "bloco ```tinydraw.")


def _traduzir_http(codigo: int, detalhe: str) -> str:
    base = {
        401: "Chave de API inválida ou ausente (401). Confira a chave em console.anthropic.com.",
        403: "Sem permissão para usar este modelo/chave (403).",
        404: "Modelo não encontrado (404). Confira o nome do modelo.",
        413: "Pedido grande demais (413).",
        429: "Limite de uso da API atingido (429). Aguarde um pouco e tente de novo.",
    }.get(codigo)
    if base is None:
        base = ("Serviço da API indisponível/sobrecarregado; tente novamente (%d)." % codigo
                if codigo >= 500 else f"A API recusou o pedido (HTTP {codigo}).")
    return base + (f"\nDetalhe da API: {detalhe}" if detalhe else "")


def chamar_claude(cfg: ConfigClaude, mensagens: List[Dict[str, str]],
                  sistema: str = PROMPT_SISTEMA) -> str:
    if not cfg.chave:
        raise ErroAssistente("Informe a chave de API (ou defina a variável ANTHROPIC_API_KEY), "
                             "ou use o modo 'Assistente local'.")
    corpo = json.dumps({"model": cfg.modelo, "max_tokens": cfg.max_tokens,
                        "system": sistema, "messages": mensagens}).encode("utf-8")
    req = urllib.request.Request(URL_API, data=corpo, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": cfg.chave,
        "anthropic-version": VERSAO_API,
    })
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = ""
        try:
            detalhe = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            pass
        raise ErroAssistente(_traduzir_http(e.code, detalhe)) from None
    except urllib.error.URLError as e:
        raise ErroAssistente(f"Sem conexão com a API da Anthropic: {e.reason}") from None
    except TimeoutError:
        raise ErroAssistente("Tempo esgotado esperando a resposta da API.") from None

    texto = "".join(b.get("text", "") for b in dados.get("content", []) if b.get("type") == "text")
    if dados.get("stop_reason") == "max_tokens":
        raise ErroAssistente("A resposta da IA foi cortada por tamanho. Peça um desenho mais simples "
                             "ou uma tela menor.")
    if not texto.strip():
        raise ErroAssistente("A IA devolveu uma resposta vazia.")
    return texto


def gerar_com_claude(pedido: str, cfg: ConfigClaude, codigo_atual: Optional[str] = None,
                     progresso: Optional[Callable[[str], None]] = None) -> ResultadoGeracao:
    cfg.chave = cfg.chave or os.environ.get("ANTHROPIC_API_KEY", "")
    avisar = progresso or (lambda _m: None)
    log: List[str] = [f"Modo: IA Claude ({cfg.modelo})", f"Pedido: {pedido}"]
    mensagens = [{"role": "user", "content": _mensagem_inicial(pedido, codigo_atual)}]
    codigo = ""
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        avisar(f"Consultando a IA (tentativa {tentativa} de {MAX_TENTATIVAS})...")
        resposta = chamar_claude(cfg, mensagens)
        codigo = extrair_codigo(resposta)
        res = transpilar(codigo)
        if res.sucesso:
            log.append(f"Tentativa {tentativa}: programa ACEITO pelo compilador TinyDraw "
                       f"({len(res.avisos)} aviso(s)).")
            return ResultadoGeracao(codigo, True, log, MODO_CLAUDE)
        log.append(f"Tentativa {tentativa}: o compilador rejeitou o programa "
                   f"({len(res.erros)} erro(s)):")
        log += [f"    {d.linha}:{d.coluna} {d.fase}: {d.mensagem}" for d in res.erros[:8]]
        mensagens += [{"role": "assistant", "content": resposta},
                      {"role": "user", "content": _mensagem_correcao(res.erros)}]
        if tentativa < MAX_TENTATIVAS:
            log.append("    -> devolvendo os diagnósticos para a IA corrigir.")
    log.append("A IA não conseguiu um programa válido; o último código foi mantido no editor "
               "para você ajustar manualmente.")
    return ResultadoGeracao(codigo, False, log, MODO_CLAUDE)

