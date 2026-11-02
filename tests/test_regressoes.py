"""Regressões de entradas e falhas externas encontradas na revisão."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tinydraw import config, executor, imagem
from tinydraw.cli import principal
from tinydraw.compilador import transpilar


class TestRegressoes(unittest.TestCase):
    def test_cli_ast_redirecionada_cp1252(self):
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'cp1252'
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, '-m', 'tinydraw',
                                'exemplos/validos/estudo.td', '--ast', '--so-c', '-o', tmp],
                               env=env, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b'Ponto(x=1, y=1)', r.stdout)

    def test_inteiro_muito_longo_vira_diagnostico(self):
        if not hasattr(sys, 'get_int_max_str_digits') or sys.get_int_max_str_digits() == 0:
            self.skipTest('Python sem limite ativo de conversão decimal')
        r = transpilar('tela ' + '9' * (sys.get_int_max_str_digits() + 1) + ' por 1')
        self.assertFalse(r.sucesso)
        self.assertEqual(r.erros[0].fase, 'léxico')
        self.assertIsNone(r.codigo_c)

    def test_config_json_que_nao_e_objeto(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'config.json'
            with mock.patch.object(config, 'ARQUIVO', p):
                for texto in ('[]', 'null', '42', '"texto"', '{'):
                    p.write_text(texto, encoding='utf-8')
                    self.assertEqual(config.carregar(), {})

    def test_arquivo_incompativel_windows(self):
        for nome in ('NUL.ppm', 'con.ppm', 'COM1.ppm', 'a?.ppm', 'a*.ppm', 'a|b.ppm', 'a\x00.ppm'):
            with self.subTest(nome=nome):
                r = transpilar('tela 2 por 2\nsalvar "' + nome + '"')
                self.assertTrue(any('Windows' in d.mensagem for d in r.erros))
                self.assertIsNone(r.codigo_c)

    def test_compilador_que_nao_inicia_ou_expira(self):
        with mock.patch.object(executor, 'achar_compilador_c', return_value=Path('gcc.exe')):
            for erro in (OSError('acesso negado'), subprocess.TimeoutExpired('gcc', 60)):
                with mock.patch.object(executor.subprocess, 'run', side_effect=erro):
                    ok, log, exe = executor.compilar(Path('x.c'))
                    self.assertFalse(ok)
                    self.assertIsNone(exe)
                    self.assertIn('compilação C', log)

    def test_executavel_ausente(self):
        with mock.patch.object(executor.subprocess, 'run', side_effect=FileNotFoundError('ausente')):
            codigo, log = executor.executar(Path('ausente.exe'), Path('.'))
        self.assertEqual(codigo, 126)
        self.assertIn('iniciar', log)

    def test_ppm_dimensoes_e_maximo_invalidos(self):
        for dados in (b'P6\n0 1\n255\n', b'P6\n1 1\n100\nabc', b'P6\n-1 -1\n255\nabc'):
            with self.assertRaises(ValueError):
                imagem.ler_ppm(dados)

    def test_png_parametros_invalidos(self):
        for fator in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                imagem.rgb_para_png(1, 1, b'abc', fator)
        with self.assertRaises(ValueError):
            imagem.rgb_para_png(1, 1, b'ab')

    def test_cli_fonte_nao_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fonte.td'
            p.write_bytes(b'\xff')
            with contextlib.redirect_stderr(io.StringIO()) as log:
                self.assertEqual(principal([str(p), '--so-c']), 1)
            self.assertIn('ler', log.getvalue())

    def test_cli_falha_gravando_saida(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fonte.td'
            p.write_text('tela 1 por 1 salvar "x.ppm"', encoding='utf-8')
            destino = Path(tmp) / 'arquivo'
            destino.write_text('impede criar pasta', encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()) as log:
                self.assertEqual(principal([str(p), '--so-c', '-o', str(destino)]), 1)
            self.assertIn('gravar', log.getvalue())

    def test_origem_multilinha_nao_quebra_comentario_c(self):
        r = transpilar('tela 1 por 1 salvar "x.ppm"', 'nome\n*/arquivo.td')
        self.assertIn('Origem: nome * /arquivo.td --', r.codigo_c)

