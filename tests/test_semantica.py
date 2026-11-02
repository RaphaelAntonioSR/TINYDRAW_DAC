import unittest
from tinydraw.compilador import transpilar

BASE = 'tela 10 por 8\ncor R = 255,0,0\nusar R\n'
FIM = '\nsalvar "a.ppm"'


def erros(txt):
    return [d.mensagem for d in transpilar(txt).erros]


class TestSemantica(unittest.TestCase):
    def ok(self, corpo):
        r = transpilar(BASE + corpo + FIM)
        self.assertTrue(r.sucesso, [d.mensagem for d in r.erros])
        return r

    def falha(self, texto, trecho):
        e = erros(texto)
        self.assertTrue(any(trecho in m for m in e), f"{trecho!r} não encontrado em {e}")

    def test_programa_valido(self):
        self.ok("ponto em 9, 7\nlinha de 0,0 ate 9,0\nretangulo em 0,0 tamanho 10 por 8")

    def test_tela_ausente(self):
        self.falha('cor R=1,1,1\nusar R\nsalvar "a.ppm"', "sem declaração de 'tela'")

    def test_tela_duplicada(self):
        self.falha(BASE + "tela 3 por 3" + FIM, "já foi declarada")

    def test_tela_zero(self):
        self.falha('tela 0 por 5' + FIM, "positivos")

    def test_comando_antes_da_tela(self):
        self.falha('ponto em 0,0\ntela 5 por 5' + FIM, "antes de declarar a 'tela'")

    def test_cor_repetida(self):
        self.falha(BASE + "cor R = 1,1,1" + FIM, "já declarada")

    def test_componente_fora_da_faixa(self):
        self.falha(BASE + "cor X = 256, 0, 0" + FIM, "entre 0 e 255")

    def test_usar_cor_nao_declarada(self):
        self.falha(BASE + "usar Z" + FIM, "não foi declarada")

    def test_desenhar_sem_cor(self):
        self.falha('tela 5 por 5\nponto em 1,1' + FIM, "nenhuma cor selecionada")

    def test_ponto_fora(self):
        self.falha(BASE + "ponto em 10, 0" + FIM, "fora da tela")

    def test_linha_diagonal(self):
        self.falha(BASE + "linha de 0,0 ate 3,3" + FIM, "horizontal")

    def test_linha_fora(self):
        self.falha(BASE + "linha de 0,0 ate 0,8" + FIM, "fora da tela")

    def test_retangulo_ultrapassa(self):
        self.falha(BASE + "retangulo em 5,5 tamanho 6 por 2" + FIM, "ultrapassa")

    def test_retangulo_tamanho_zero(self):
        self.falha(BASE + "retangulo em 1,1 tamanho 0 por 2" + FIM, "positivos")

    def test_extensao_invalida(self):
        self.falha(BASE + 'salvar "a.png"', "extensão .ppm")

    def test_sem_salvar(self):
        self.falha(BASE, "sem comando 'salvar'")

    def test_comando_apos_salvar(self):
        self.falha(BASE + 'salvar "a.ppm"\nponto em 1,1', "após 'salvar'")

    def test_avisos(self):
        r = transpilar('tela 5 por 5\ncor R=1,1,1\ncor N=2,2,2\nusar R\nponto em 1,1\n'
                       'linha de 2,2 ate 2,2\nsalvar "a.ppm"')
        self.assertTrue(r.sucesso)
        msgs = [a.mensagem for a in r.avisos]
        self.assertTrue(any("nunca selecionada" in m for m in msgs))
        self.assertTrue(any("degenerada" in m for m in msgs))

    def test_sem_codigo_quando_ha_erros(self):
        self.assertIsNone(transpilar("tela 0 por 0").codigo_c)


if __name__ == "__main__":
    unittest.main()


class TestSalvarSeguro(unittest.TestCase):
    def test_caminho_no_nome_do_arquivo_e_rejeitado(self):
        for nome in ("../x.ppm", "pasta/x.ppm", "C:\\\\x.ppm", "a\\\\b.ppm"):
            r = transpilar('tela 5 por 5\nsalvar "' + nome + '"')
            self.assertTrue(any("sem pastas" in d.mensagem for d in r.erros), nome)

    def test_percentual_no_nome_nao_e_duplicado_no_c(self):
        r = transpilar('tela 5 por 5\ncor A = 1,2,3\nusar A\nponto em 1,1\nsalvar "a%b.ppm"')
        self.assertTrue(r.sucesso)
        self.assertIn('td_salvar(c, "a%b.ppm")', r.codigo_c)
        self.assertNotIn("%%", r.codigo_c)
