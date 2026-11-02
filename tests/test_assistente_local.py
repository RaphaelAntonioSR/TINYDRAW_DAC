import random
import shutil
import tempfile
import unittest
from pathlib import Path

from tinydraw.assistente import ErroAssistente
from tinydraw.compilador import transpilar
from tinydraw.assistente_local import gerar_local, interpretar
from tinydraw.imagem import ler_ppm
from tinydraw.pipeline import executar_programa

CC = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")


class TestAssistenteLocal(unittest.TestCase):
    def valido(self, pedido):
        codigo, notas = interpretar(pedido)
        r = transpilar(codigo)
        self.assertTrue(r.sucesso, [d.mensagem for d in r.erros] + [codigo])
        return codigo, notas

    def test_cena_casa_arvore_sol(self):
        codigo, notas = self.valido("uma casa azul, uma árvore e um sol")
        self.assertIn("tela 47 por 24", codigo)
        self.assertIn("cor AZUL = 0, 0, 255", codigo)
        self.assertEqual(sum(n.startswith("Figura:") for n in notas), 3)

    def test_retangulo_com_cor_medidas_e_posicao(self):
        codigo, _ = self.valido("Retângulo azul de 20 por 8 em 5, 4")
        self.assertIn("usar AZUL", codigo)
        self.assertIn("retangulo em 5, 4 tamanho 20 por 8", codigo)

    def test_retangulo_preenchido_vira_linhas(self):
        codigo, _ = self.valido("retângulo preenchido vermelho de 4 por 3 em 1, 1")
        self.assertEqual(codigo.count("linha de"), 3)
        self.assertIn("linha de 1, 1 ate 4, 1", codigo)
        self.assertNotIn("retangulo em", codigo)

    def test_tela_explicita_e_posicao_nomeada(self):
        codigo, _ = self.valido("tela 60 por 30, círculo amarelo de raio 6 no centro")
        self.assertIn("tela 60 por 30", codigo)

    def test_linha_vertical_com_extremos(self):
        codigo, _ = self.valido("linha vertical verde de 10,2 até 10,25")
        self.assertIn("linha de 10, 2 ate 10, 25", codigo)

    def test_posicao_nomeada_canto(self):
        codigo, _ = self.valido("tela 20 por 10 ponto preto no canto inferior direito")
        self.assertIn("ponto em 18, 8", codigo)

    def test_diagonal_e_rejeitada_com_motivo(self):
        with self.assertRaises(ErroAssistente) as c:
            interpretar("linha de 0,0 até 5,5")
        self.assertIn("diagonais", str(c.exception))

    def test_pedido_nao_entendido(self):
        with self.assertRaises(ErroAssistente) as c:
            interpretar("bom dia, tudo bem?")
        self.assertIn("Não entendi", str(c.exception))

    def test_valores_enormes_sao_ajustados_e_continuam_validos(self):
        self.valido("tela 20 por 10 retângulo de 500 por 500 em 900, 900")
        self.valido("casa em 500, 500")

    def test_figura_que_nao_cabe_e_descartada_com_nota(self):
        codigo, notas = self.valido("tela 10 por 10 uma casa")
        self.assertTrue(any("não coube" in n for n in notas))

    def test_gerar_local_devolve_resultado_validado(self):
        r = gerar_local("um sol")
        self.assertTrue(r.valido)
        self.assertEqual(r.modo, "local")
        self.assertTrue(any("ACEITO" in linha for linha in r.log))

    def test_fuzz_sempre_gera_programa_valido(self):
        rnd = random.Random(2026)
        formas = ["retângulo", "quadrado", "moldura", "linha", "ponto", "círculo", "triângulo",
                  "sol", "casa", "árvore"]
        cores = ["vermelho", "azul", "verde", "amarela", "preto", "roxo", "marrom", "cinza", ""]
        extras = ["preenchido", "de {a} por {b}", "lado {a}", "raio {a}", "base {a}", "em {a}, {b}",
                  "no centro", "no canto superior direito", "na base", "à esquerda", "vertical",
                  "de {a},{b} até {a},{c}", "comprimento {a}", ""]
        for _ in range(400):
            partes = []
            if rnd.random() < 0.4:
                partes.append(f"tela {rnd.randint(0, 90)} por {rnd.randint(0, 90)}")
            for _ in range(rnd.randint(1, 4)):
                extra = rnd.choice(extras).format(a=rnd.randint(0, 300), b=rnd.randint(0, 300),
                                                  c=rnd.randint(0, 300))
                partes.append(f"um {rnd.choice(formas)} {rnd.choice(cores)} {extra}")
            pedido = ", ".join(partes)
            try:
                codigo, _ = interpretar(pedido)
            except ErroAssistente:
                continue
            r = transpilar(codigo)
            self.assertTrue(r.sucesso, f"{pedido!r} -> {[d.mensagem for d in r.erros]}")

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_ponta_a_ponta_pixel_vermelho_no_lugar_certo(self):
        codigo, _ = interpretar("tela 10 por 10 ponto vermelho em 3, 4")
        pasta = Path(tempfile.mkdtemp())
        res = executar_programa(codigo, pasta, "t")
        self.assertIsNotNone(res.png, res.saida_execucao + res.log_compilacao)
        w, h, rgb = ler_ppm(res.ppm.read_bytes())
        i = (4 * w + 3) * 3
        self.assertEqual(tuple(rgb[i:i + 3]), (255, 0, 0))
        self.assertEqual(tuple(rgb[0:3]), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
