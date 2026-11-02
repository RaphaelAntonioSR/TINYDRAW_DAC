"""Testes de geração de C e de ponta a ponta (compila, executa e confere o PPM)."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tinydraw.compilador import transpilar

RAIZ = Path(__file__).resolve().parent.parent
CC = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")


def ler_ppm(caminho):
    dados = Path(caminho).read_bytes()
    partes = dados.split(b"\n", 3)
    assert partes[0] == b"P6"
    w, h = map(int, partes[1].split())
    assert partes[2] == b"255"
    pix = partes[3]
    assert len(pix) == w * h * 3
    return w, h, lambda x, y: tuple(pix[(y * w + x) * 3:(y * w + x) * 3 + 3])


def executar(programa: str, nome="t"):
    r = transpilar(programa)
    assert r.sucesso, [d.mensagem for d in r.erros]
    tmp = tempfile.mkdtemp()
    c = Path(tmp) / f"{nome}.c"
    c.write_text(r.codigo_c)
    exe = Path(tmp) / nome
    subprocess.run([CC, "-std=c99", "-Wall", "-Wextra", "-Werror", "-o", str(exe), str(c),
                    str(RAIZ / "runtime" / "tinydraw.c"), f"-I{RAIZ / 'runtime'}"], check=True)
    p = subprocess.run([str(exe)], cwd=tmp, capture_output=True, text=True)
    return p, tmp


class TestGeracao(unittest.TestCase):
    def test_estrutura_do_c(self):
        r = transpilar('tela 4 por 3\ncor A = 1,2,3\nusar A\nponto em 1,1\nsalvar "o.ppm"')
        self.assertIn("td_criar(4, 3)", r.codigo_c)
        self.assertIn("td_definir_cor", r.codigo_c)
        self.assertIn("td_ponto(c, 1, 1);", r.codigo_c)
        self.assertIn('td_salvar(c, "o.ppm")', r.codigo_c)

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_ponta_a_ponta_cores_e_sobreposicao(self):
        prog = ('tela 10 por 6\ncor V = 255,0,0\ncor A = 0,0,255\n'
                'usar V\nretangulo em 0,0 tamanho 6 por 4\n'
                'usar A\nponto em 0,0\nlinha de 9,0 ate 9,5\nsalvar "saida.ppm"')
        p, tmp = executar(prog)
        self.assertEqual(p.returncode, 0, p.stderr)
        w, h, px = ler_ppm(Path(tmp) / "saida.ppm")
        self.assertEqual((w, h), (10, 6))
        self.assertEqual(px(0, 0), (0, 0, 255))      # azul sobrescreveu o vermelho
        self.assertEqual(px(5, 0), (255, 0, 0))      # borda vermelha
        self.assertEqual(px(2, 2), (255, 255, 255))  # interior do retângulo = fundo
        self.assertEqual(px(9, 5), (0, 0, 255))      # linha vertical
        self.assertIn("Legenda", p.stdout)

    @unittest.skipIf(CC is None, "compilador C indisponível")
    def test_exemplos_validos_compilam_sem_warnings(self):
        for arq in sorted((RAIZ / "exemplos" / "validos").glob("*.td")):
            with self.subTest(arq=arq.name):
                p, tmp = executar(arq.read_text(encoding="utf-8"), arq.stem)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertTrue((Path(tmp) / (arq.stem + ".ppm")).exists())

    def test_exemplos_invalidos_sao_rejeitados(self):
        for arq in sorted((RAIZ / "exemplos" / "invalidos").glob("*.td")):
            with self.subTest(arq=arq.name):
                r = transpilar(arq.read_text(encoding="utf-8"))
                self.assertFalse(r.sucesso)
                self.assertIsNone(r.codigo_c)


if __name__ == "__main__":
    unittest.main()
