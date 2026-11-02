"""Verifica a UI real sem credenciais, compilador C ou escrita no perfil."""
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tinydraw import gui, imagem

def esperar(app):
    fim = time.monotonic() + 10
    while app._ocupado and time.monotonic() < fim:
        app.update()
        time.sleep(.02)
    assert not app._ocupado, 'UI não concluiu em 10 segundos'
    app.update()

with tempfile.TemporaryDirectory() as tmp:
    with patch.object(gui.caminhos, 'pasta_saida_padrao', return_value=Path(tmp)), \
         patch('tinydraw.executor.achar_compilador_c', return_value=None), \
         patch.object(gui.messagebox, 'showwarning'), \
         patch.object(gui.messagebox, 'showerror') as erros:
        app = gui.App()
        try:
            app.update()
            assert not hasattr(app, "var_chave")
            assert not hasattr(app, "var_modelo")
            assert not hasattr(app, "var_modo")
            app._inserir_pedido('um quadrado vermelho de lado 5 em 2, 2')
            app.acao_gerar()
            esperar(app)
            # _apos_gerar inicia o pipeline; esperar só sai quando ele termina.
            assert 'retangulo em 2, 2 tamanho 5 por 5' in app._texto_editor()
            assert app._res.transp.sucesso and app._res.sem_compilador
            assert 'td_retangulo' in app.t_c.get('1.0', 'end')
            # Exportação da UI com fixture declarada, sem fingir execução C.
            ppm = Path(tmp) / 'fixture.ppm'
            ppm.write_bytes(b'P6\n1 1\n255\n'+bytes([255, 0, 0]))
            app._res.ppm = ppm
            app._res.png = imagem.ppm_para_png(ppm.read_bytes(), 2)[0]
            for extensao in ('png', 'ppm'):
                destino = Path(tmp) / ('exportado.' + extensao)
                with patch.object(gui.filedialog, 'asksaveasfilename', return_value=str(destino)):
                    app.acao_salvar_imagem()
                esperado = app._res.png if extensao == 'png' else ppm.read_bytes()
                assert destino.read_bytes() == esperado
            td = Path(tmp) / 'salvo.td'
            with patch.object(gui.filedialog, 'asksaveasfilename', return_value=str(td)):
                app.acao_salvar_td()
            assert td.read_text(encoding='utf-8') == app._texto_editor()
            with patch.object(gui.filedialog, 'asksaveasfilename', return_value=str(Path(tmp)/'ausente'/'x.png')):
                app.acao_salvar_imagem()
            erros.assert_called_once()
            erros.reset_mock()
            for fonte, fase in [('tela 2 por 2 @', 'léxico'), ('tela 2 2', 'sintático'),
                                ('tela 0 por 2 salvar "x.ppm"', 'semântico')]:
                app._set_editor(fonte)
                app.acao_executar()
                esperar(app)
                assert app._res.transp.erros[0].fase == fase
                assert fase in app.t_diag.get('1.0', 'end')
                assert app.ed.tag_ranges('erro')
                assert app._foto is None
            assert not erros.called, erros.call_args_list
            print(json.dumps({'janela': 'OK', 'editor': 'OK', 'assistente_local': 'OK',
                              'C_na_aba': 'OK', 'tres_fases_de_erro': 'OK',
                              'salvar_td': 'OK', 'exportar_PNG_PPM_fixture': 'OK',
                              'falha_de_exportacao': 'OK',
                              'sem_compilador': 'OK', 'imagem_C': 'NAO_TESTADA'}, ensure_ascii=False))
        finally:
            app.destroy()
