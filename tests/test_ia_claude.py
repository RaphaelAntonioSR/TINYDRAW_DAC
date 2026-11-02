import io
import json
import unittest
import urllib.error
from unittest import mock

from tinydraw import ia_claude
from tinydraw.assistente import ErroAssistente, gerar
from tinydraw.compilador import transpilar
from tinydraw.ia_claude import ConfigClaude, extrair_codigo, gerar_com_claude

VALIDO = 'tela 10 por 10\ncor R = 255,0,0\nusar R\nponto em 1, 1\nsalvar "desenho.ppm"\n'
INVALIDO = 'tela 10 por 10\ncor R = 255,0,0\nusar R\nponto em 50, 1\nsalvar "desenho.ppm"\n'


def resposta(texto, parada="end_turn"):
    corpo = json.dumps({"content": [{"type": "text", "text": texto}], "stop_reason": parada}).encode()

    class R:
        def read(self_inner): return corpo
        def __enter__(self_inner): return self_inner
        def __exit__(self_inner, *a): return False
    return R()


def bloco(codigo):
    return "```tinydraw\n" + codigo + "```"


class TestExtracao(unittest.TestCase):
    def test_bloco_cercado(self):
        self.assertEqual(extrair_codigo("Claro!\n```tinydraw\nponto em 1, 1\n```\nfim"), "ponto em 1, 1\n")

    def test_bloco_sem_linguagem(self):
        self.assertEqual(extrair_codigo("```\ntela 1 por 1\n```"), "tela 1 por 1\n")

    def test_sem_bloco_usa_o_texto_todo(self):
        self.assertEqual(extrair_codigo("tela 1 por 1"), "tela 1 por 1\n")

    def test_exemplo_do_prompt_de_sistema_e_valido_no_compilador(self):
        r = transpilar(extrair_codigo(ia_claude.PROMPT_SISTEMA))
        self.assertTrue(r.sucesso, [d.mensagem for d in r.erros])
        self.assertEqual(r.avisos, [])


class TestChamadaApi(unittest.TestCase):
    def test_requisicao_montada_corretamente(self):
        cfg = ConfigClaude(chave="sk-teste", modelo="claude-haiku-5-5")
        with mock.patch("urllib.request.urlopen", return_value=resposta(bloco(VALIDO))) as uo:
            r = gerar_com_claude("um ponto vermelho", cfg)
        req = uo.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_header("X-api-key"), "sk-teste")
        self.assertEqual(req.get_header("Anthropic-version"), "2023-06-01")
        corpo = json.loads(req.data)
        self.assertEqual(corpo["model"], "claude-haiku-5-5")
        self.assertIn("TinyDraw", corpo["system"])
        self.assertEqual(corpo["messages"][0]["content"], "Pedido: um ponto vermelho")
        self.assertTrue(r.valido)

    def test_continuar_do_desenho_atual_envia_o_codigo(self):
        with mock.patch("urllib.request.urlopen", return_value=resposta(bloco(VALIDO))) as uo:
            gerar_com_claude("deixe vermelho", ConfigClaude(chave="k"), codigo_atual=VALIDO)
        msg = json.loads(uo.call_args[0][0].data)["messages"][0]["content"]
        self.assertIn("Programa TinyDraw atual", msg)
        self.assertIn("ponto em 1, 1", msg)

    def test_laco_de_correcao_devolve_diagnosticos_do_compilador(self):
        respostas = [resposta(bloco(INVALIDO)), resposta(bloco(VALIDO))]
        with mock.patch("urllib.request.urlopen", side_effect=respostas) as uo:
            r = gerar_com_claude("ponto", ConfigClaude(chave="k"))
        self.assertTrue(r.valido)
        self.assertEqual(uo.call_count, 2)
        segunda = json.loads(uo.call_args_list[1][0][0].data)["messages"]
        self.assertEqual([m["role"] for m in segunda], ["user", "assistant", "user"])
        self.assertIn("fora da tela", segunda[2]["content"])
        self.assertTrue(any("rejeitou" in linha for linha in r.log))

    def test_desiste_depois_de_tres_tentativas_mas_mantem_o_codigo(self):
        respostas = [resposta(bloco(INVALIDO)) for _ in range(3)]
        with mock.patch("urllib.request.urlopen", side_effect=respostas) as uo:
            r = gerar_com_claude("ponto", ConfigClaude(chave="k"))
        self.assertFalse(r.valido)
        self.assertEqual(uo.call_count, 3)
        self.assertIn("ponto em 50, 1", r.codigo)

    def test_sem_chave(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ErroAssistente) as c:
                gerar_com_claude("x", ConfigClaude(chave=""))
        self.assertIn("chave", str(c.exception).lower())

    def test_chave_invalida_401(self):
        corpo = io.BytesIO(json.dumps({"error": {"type": "authentication_error",
                                                  "message": "invalid x-api-key"}}).encode())
        erro = urllib.error.HTTPError(ia_claude.URL_API, 401, "Unauthorized", {}, corpo)
        with mock.patch("urllib.request.urlopen", side_effect=erro):
            with self.assertRaises(ErroAssistente) as c:
                gerar_com_claude("x", ConfigClaude(chave="ruim"))
        self.assertIn("inválida", str(c.exception))
        self.assertIn("invalid x-api-key", str(c.exception))

    def test_sem_rede(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sem rede")):
            with self.assertRaises(ErroAssistente) as c:
                gerar_com_claude("x", ConfigClaude(chave="k"))
        self.assertIn("Sem conexão", str(c.exception))

    def test_resposta_cortada_por_tamanho(self):
        with mock.patch("urllib.request.urlopen", return_value=resposta("tela 1", "max_tokens")):
            with self.assertRaises(ErroAssistente) as c:
                gerar_com_claude("x", ConfigClaude(chave="k"))
        self.assertIn("cortada", str(c.exception))


class TestFachada(unittest.TestCase):
    def test_pedido_vazio(self):
        with self.assertRaises(ErroAssistente):
            gerar("local", "   ")

    def test_modo_local_nao_usa_rede(self):
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("não deveria usar rede")):
            r = gerar("local", "um ponto preto em 2, 2")
        self.assertTrue(r.valido)


if __name__ == "__main__":
    unittest.main()
