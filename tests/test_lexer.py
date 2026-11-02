import unittest
from tinydraw.lexer import tokenizar


def tipos(txt):
    toks, d = tokenizar(txt)
    return [t.tipo for t in toks], d


class TestLexer(unittest.TestCase):
    def test_bom_inicial_preserva_tokens_e_colunas(self):
        esperado, _ = tokenizar('tela 6 por 4')
        recebido, diags = tokenizar('\ufefftela 6 por 4')
        self.assertEqual(diags, [])
        self.assertEqual(recebido, esperado)

    def test_bom_no_meio_continua_invalido(self):
        _, diags = tokenizar('tela 6 \ufeffpor 4')
        self.assertTrue(diags)

    def test_palavras_reservadas_e_literais(self):
        t, d = tipos('tela 40 por 20 cor AZUL = 0, 0, 255 salvar "a.ppm"')
        self.assertEqual(d, [])
        self.assertEqual(t, ["TELA", "INT", "POR", "INT", "COR", "ID", "IGUAL", "INT",
                             "VIRGULA", "INT", "VIRGULA", "INT", "SALVAR", "STRING", "EOF"])

    def test_sinonimos_acentuados(self):
        t, d = tipos("retângulo até")
        self.assertEqual(t, ["RETANGULO", "ATE", "EOF"])

    def test_comentario_e_posicao(self):
        toks, _ = tokenizar("# nada\n  ponto")
        self.assertEqual((toks[0].tipo, toks[0].linha, toks[0].coluna), ("PONTO", 2, 3))

    def test_palavra_reservada_e_case_sensitive(self):
        t, _ = tipos("TELA")
        self.assertEqual(t, ["ID", "EOF"])

    def test_caractere_invalido(self):
        _, d = tipos("ponto em 1, @")
        self.assertEqual(len(d), 1)
        self.assertIn("caractere inesperado", d[0].mensagem)

    def test_numero_negativo_e_lexicamente_invalido(self):
        _, d = tipos("-5")
        self.assertEqual(len(d), 1)

    def test_string_nao_terminada(self):
        _, d = tipos('salvar "abc')
        self.assertIn("string não terminada", d[0].mensagem)


if __name__ == "__main__":
    unittest.main()
