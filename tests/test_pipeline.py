import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tinydraw import caminhos, imagem, pipeline

CC = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
OK = 'tela 8 por 6\ncor A = 0,0,255\nusar A\nretangulo em 1, 1 tamanho 4 por 3\nsalvar "o.ppm"\n'


def estados(res):
    return dict(pipeline.etapas(res))


class TestEtapas(unittest.TestCase):
    def rodar(self, texto):
        return pipeline.executar_programa(texto, tempfile.mkdtemp(), "t")

    def test_erro_lexico_so_marca_lexico(self):
        e = estados(self.rodar("tela 8 por 6 @"))
        self.assertEqual(e["Léxico"], "erro")
        self.assertEqual(e["Sintaxe"], "pendente")

    def test_erro_sintatico(self):
        e = estados(self.rodar("tela 8 6"))
        self.assertEqual((e["Léxico"], e["Sintaxe"], e["Semântica"]), ("ok", "erro", "pendente"))

    def test_erro_semantico(self):
        e = estados(self.rodar("tela 0 por 0"))
        self.assertEqual((e["Léxico"], e["Sintaxe"], e["Semântica"], e["Gerar C"]),
                         ("ok", "ok", "erro", "pendente"))

    def test_nenhum_c_e_gerado_quando_ha_erro(self):
        pasta = Path(tempfile.mkdtemp())
        res = pipeline.executar_programa("tela 0 por 0", pasta, "t")
        self.assertFalse((pasta / "t.c").exists())
        self.assertIsNone(res.png)

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_sucesso_marca_tudo_ok(self):
        res = self.rodar(OK)
        self.assertTrue(all(s == "ok" for _, s in pipeline.etapas(res)), pipeline.etapas(res))
        self.assertTrue(res.png.startswith(b"\x89PNG"))
        self.assertEqual((res.largura, res.altura), (8, 6))

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_imagem_antiga_nao_e_reaproveitada(self):
        pasta = Path(tempfile.mkdtemp())
        (pasta / "o.ppm").write_bytes(b"lixo")
        res = pipeline.executar_programa(OK, pasta, "t")
        self.assertEqual((res.largura, res.altura), (8, 6))

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_autoteste(self):
        ok, texto = pipeline.autoteste()
        self.assertTrue(ok, texto)
        self.assertIn("tudo funcionando", texto)

    def test_sem_compilador_c_e_informado(self):
        with unittest.mock.patch("tinydraw.executor.achar_compilador_c", return_value=None):
            res = self.rodar(OK)
        self.assertTrue(res.sem_compilador)
        self.assertEqual(estados(res)["Compilar C"], "erro")


class TestImagem(unittest.TestCase):
    def test_png_tem_assinatura_e_dimensoes(self):
        rgb = bytes([255, 0, 0] * 6)                  # 3x2 vermelho
        png = imagem.rgb_para_png(3, 2, rgb, fator=4)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(png[16:20], "big"), 12)
        self.assertEqual(int.from_bytes(png[20:24], "big"), 8)

    def test_ppm_invalido(self):
        with self.assertRaises(ValueError):
            imagem.ler_ppm(b"P3\n1 1\n255\n")

    def test_fator_para_caber(self):
        self.assertEqual(imagem.fator_para_caber(47, 24, 940, 480), 20)
        self.assertEqual(imagem.fator_para_caber(2000, 10, 700, 500), 1)


class TestCaminhos(unittest.TestCase):
    def test_recursos_existem(self):
        self.assertTrue((caminhos.pasta_runtime() / "tinydraw.c").exists())
        self.assertTrue((caminhos.pasta_exemplos() / "validos" / "casa.td").exists())


import unittest.mock  # noqa: E402  (usado em test_sem_compilador_c_e_informado)

if __name__ == "__main__":
    unittest.main()
