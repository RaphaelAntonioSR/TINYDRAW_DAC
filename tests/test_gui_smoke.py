"""Teste de fumaça da interface. Opt-in: abre uma janela de verdade.

Rode com:  set TINYDRAW_TESTE_GUI=1  (Windows)   |   TINYDRAW_TESTE_GUI=1 python -m unittest ...
"""
import os
import shutil
import tempfile
import time
import unittest

CC = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
ATIVO = bool(os.environ.get("TINYDRAW_TESTE_GUI"))


@unittest.skipUnless(ATIVO, "defina TINYDRAW_TESTE_GUI=1 para testar a interface")
@unittest.skipIf(CC is None, "compilador C indisponível")
class TestGuiFumaca(unittest.TestCase):
    def test_gerar_com_assistente_local_ate_a_imagem(self):
        os.environ["HOME"] = os.environ["USERPROFILE"] = tempfile.mkdtemp()
        from tinydraw import gui
        app = gui.App()
        try:
            app.var_modo.set("Assistente local (offline)")
            app._atualizar_modo()
            app._inserir_pedido("um quadrado vermelho de lado 5 em 2, 2")
            app.acao_gerar()
            limite = time.time() + 60
            while time.time() < limite and (app._ocupado or app._res is None):
                app.update()
                time.sleep(0.03)
            self.assertIsNotNone(app._res)
            self.assertIsNotNone(app._res.png)
            self.assertIn("retangulo em 2, 2 tamanho 5 por 5", app._texto_editor())
            self.assertTrue(all(s == "ok" for _, s in gui.pipeline.etapas(app._res)))
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
