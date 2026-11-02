"""Contrato do assistente local após a remoção do serviço externo."""
import importlib.util
import unittest
from unittest.mock import patch
from tinydraw.assistente import gerar, ErroAssistente
from tinydraw.compilador import transpilar

class TestAssistente(unittest.TestCase):
    def test_pedido_vazio(self):
        with self.assertRaises(ErroAssistente):
            gerar("   ")

    def test_gerar_sem_rede(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Rede indevida")):
            r = gerar("um quadrado vermelho de lado 5 em 2, 2")
        self.assertTrue(r.valido)
        self.assertEqual(r.modo, "local")
        self.assertTrue(transpilar(r.codigo).sucesso)

    def test_cliente_externo_removido(self):
        self.assertIsNone(importlib.util.find_spec("tinydraw.ia_claude"))
