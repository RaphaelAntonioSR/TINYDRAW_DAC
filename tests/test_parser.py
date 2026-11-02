import unittest
from tinydraw import ast_nodes as ast
from tinydraw.compilador import transpilar


class TestParser(unittest.TestCase):
    def test_todos_os_comandos(self):
        r = transpilar('tela 5 por 5\ncor A = 1,2,3\nusar A\nponto em 1,1\n'
                       'linha de 0,0 ate 4,0\nretangulo em 0,0 tamanho 2 por 2\nsalvar "a.ppm"')
        self.assertIsNotNone(r.ast)
        self.assertEqual([type(c) for c in r.ast.comandos],
                         [ast.Tela, ast.DefCor, ast.Usar, ast.Ponto, ast.Linha,
                          ast.Retangulo, ast.Salvar])
        self.assertEqual(r.ast.comandos[4].x2, 4)

    def test_faltando_por(self):
        r = transpilar("tela 5 20")
        self.assertIn("esperado 'por'", r.erros[0].mensagem)
        self.assertEqual(r.erros[0].fase, "sintático")

    def test_comando_invalido(self):
        r = transpilar("desenhar 1")
        self.assertIn("esperado um comando", r.erros[0].mensagem)

    def test_fim_inesperado(self):
        r = transpilar("ponto em 1,")
        self.assertIn("fim do arquivo", r.erros[0].mensagem)

    def test_virgula_faltando(self):
        r = transpilar("ponto em 1 2")
        self.assertIn("esperado ','", r.erros[0].mensagem)

    def test_nome_de_cor_nao_pode_ser_reservada(self):
        r = transpilar("cor ponto = 1,2,3")
        self.assertIn("nome da cor", r.erros[0].mensagem)

    def test_erro_lexico_interrompe_antes_do_parser(self):
        r = transpilar("tela 5 por 5 $")
        self.assertIsNone(r.ast)
        self.assertEqual(r.erros[0].fase, "léxico")


if __name__ == "__main__":
    unittest.main()
