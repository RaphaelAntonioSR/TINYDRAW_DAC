"""TinyDraw Studio: interface gráfica (tkinter) do projeto.

Fluxo mostrado na tela:
  pedido -> assistente local por regras -> programa .td -> léxico -> sintaxe
  -> semântica -> C -> compilador C -> executável -> imagem
O assistente só escreve o programa .td; o desenho vem sempre do C gerado pelo transpilador.
"""
import base64
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__, assistente, caminhos, pipeline
PEDIDOS_EXEMPLO = [
    "uma casa azul, uma árvore e um sol",
    "tela 60 por 30, retângulo preenchido azul de 20 por 8 em 5, 4 e círculo amarelo de raio 6 em 40, 8",
    "uma moldura laranja e um quadrado preenchido roxo de lado 6 no centro",
    "triângulo verde de base 15 no centro e um sol no canto superior direito",
]

COR_ETAPA = {"pendente": "#9aa0a6", "ok": "#188038", "erro": "#d93025"}
MONO = ("Consolas", 10) if sys.platform.startswith("win") else ("DejaVu Sans Mono", 10)

REFERENCIA = """\
LINGUAGEM TINYDRAW (palavras reservadas em português)

  tela 40 por 20                          declara a tela (antes de desenhar, uma vez)
  cor NOME = R, G, B                      cor nomeada (0 a 255)
  usar NOME                               seleciona a cor ativa
  ponto em X, Y
  linha de X1, Y1 ate X2, Y2              só horizontal ou vertical
  retangulo em X, Y tamanho L por A       só contorno
  salvar "desenho.ppm"                    grava o arquivo (último comando, uma vez)

Coordenadas: origem (0,0) no canto superior esquerdo; x para a direita, y para baixo.
O último desenho sobrescreve os anteriores. Comentários começam com #.

ASSISTENTE LOCAL (modo offline) entende, por exemplo:
  uma casa azul, uma árvore e um sol
  retângulo preenchido vermelho de 20 por 8 em 5, 4
  tela 60 por 30, círculo amarelo de raio 6 no centro
  moldura laranja | quadrado roxo de lado 6 | triângulo verde de base 15
  linha vertical verde de 10,2 até 10,25 | ponto preto em 5, 5
Figuras: retângulo, quadrado, moldura, linha, ponto, círculo, triângulo, sol, casa, árvore.
Medidas: "10 por 5", lado, raio, diametro, base, largura, altura. (x, y) = canto superior
esquerdo da figura. Posições nomeadas: centro, topo, base, esquerda, direita e os 4 cantos.
Sem posição, as figuras são distribuídas automaticamente.

"""


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"TinyDraw Studio {__version__} — pedido → programa .td → C → imagem")
        self.geometry("1340x840")
        self.minsize(1080, 700)
        self.fila: "queue.Queue" = queue.Queue()
        self._ocupado = False
        self._foto = None
        self._res = None
        self._estado_assist = "pendente"
        self._montar_estilo()
        self._montar_menu()
        self._montar_assistente()
        self._montar_etapas()
        self._montar_centro()
        self._montar_rodape()
        self._carregar_inicial()
        self.bind("<F5>", lambda _e: self.acao_executar())
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.after(80, self._poll)

    # ------------------------------------------------------------------ montagem
    def _montar_estilo(self):
        st = ttk.Style(self)
        for tema in ("vista", "clam"):
            if tema in st.theme_names():
                st.theme_use(tema)
                break
        st.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _montar_menu(self):
        barra = tk.Menu(self)
        m_arq = tk.Menu(barra, tearoff=0)
        m_arq.add_command(label="Abrir programa .td...", command=self.acao_abrir)
        m_arq.add_command(label="Salvar programa .td...", command=self.acao_salvar_td)
        m_arq.add_command(label="Salvar imagem (PNG/PPM)...", command=self.acao_salvar_imagem)
        m_arq.add_command(label="Abrir pasta de saída", command=self.acao_abrir_pasta)
        m_arq.add_separator()
        m_arq.add_command(label="Sair", command=self._fechar)
        barra.add_cascade(label="Arquivo", menu=m_arq)

        m_ex = tk.Menu(barra, tearoff=0)
        base = caminhos.pasta_exemplos()
        for sub, titulo in (("validos", "Programas válidos"), ("invalidos", "Programas inválidos (mostram erros)")):
            sm = tk.Menu(m_ex, tearoff=0)
            for arq in sorted((base / sub).glob("*.td")):
                sm.add_command(label=arq.name, command=lambda a=arq: self._carregar_arquivo(a))
            m_ex.add_cascade(label=titulo, menu=sm)
        sp = tk.Menu(m_ex, tearoff=0)
        for pedido in PEDIDOS_EXEMPLO:
            sp.add_command(label=pedido[:70], command=lambda p=pedido: self._inserir_pedido(p))
        m_ex.add_cascade(label="Pedidos de exemplo", menu=sp)
        barra.add_cascade(label="Exemplos", menu=m_ex)

        m_aj = tk.Menu(barra, tearoff=0)
        m_aj.add_command(label="Referência da linguagem e do assistente", command=self._ver_referencia)
        m_aj.add_command(label="Diagnóstico do ambiente (gcc, pastas)...", command=self.acao_diagnostico)
        m_aj.add_command(label="Sobre", command=lambda: messagebox.showinfo(
            "Sobre", f"TinyDraw Studio {__version__}\nDSL em português → transpilador Python → C → imagem.\n\n"
                     "DAC – Engenharia de Computação, 8º semestre."))
        barra.add_cascade(label="Ajuda", menu=m_aj)
        self.config(menu=barra)

    def _montar_assistente(self):
        caixa = ttk.LabelFrame(self, text=" Assistente: descreva o desenho em português ", padding=8)
        caixa.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Label(caixa, text="Assistente local por regras, sem conexão com serviços externos.").pack(anchor="w")

        l2 = ttk.Frame(caixa)
        l2.pack(fill="x", pady=(8, 0))
        self.txt_pedido = tk.Text(l2, height=3, wrap="word", font=("Segoe UI", 11), undo=True)
        self.txt_pedido.pack(side="left", fill="x", expand=True)
        self.txt_pedido.bind("<Control-Return>", lambda _e: (self.acao_gerar(), "break")[1])
        botoes = ttk.Frame(l2)
        botoes.pack(side="left", padx=(8, 0))
        self.bt_gerar = ttk.Button(botoes, text="Gerar desenho  (Ctrl+Enter)", style="Primary.TButton",
                                   command=self.acao_gerar)
        self.bt_gerar.pack(fill="x")
        self.bt_exec = ttk.Button(botoes, text="Executar código  (F5)", command=self.acao_executar)
        self.bt_exec.pack(fill="x", pady=(4, 0))

        ttk.Label(caixa, text="O assistente escreve .td; o C gerado pelo transpilador produz a imagem.",
                  foreground="#5f6368").pack(anchor="w", pady=(4, 0))

    def _montar_etapas(self):
        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=8, pady=2)
        self.etapas_lbl = {}
        nomes = ["Pedido", "Assistente"] + pipeline.ETAPAS
        for i, nome in enumerate(nomes):
            lb = tk.Label(barra, text=f" {nome} ", fg="white", bg=COR_ETAPA["pendente"],
                          font=("Segoe UI", 9, "bold"), padx=4, pady=2)
            lb.pack(side="left")
            self.etapas_lbl[nome] = lb
            if i < len(nomes) - 1:
                ttk.Label(barra, text="→").pack(side="left", padx=2)

    def _montar_centro(self):
        pan = ttk.PanedWindow(self, orient="horizontal")
        pan.pack(fill="both", expand=True, padx=8, pady=4)

        esq = ttk.LabelFrame(pan, text=" Programa TinyDraw (.td) — editável ", padding=4)
        self.ed = tk.Text(esq, wrap="none", font=MONO, undo=True)
        sy = ttk.Scrollbar(esq, orient="vertical", command=self.ed.yview)
        sx = ttk.Scrollbar(esq, orient="horizontal", command=self.ed.xview)
        self.ed.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.ed.pack(fill="both", expand=True)
        self.ed.tag_configure("aviso", background="#feefc3")
        self.ed.tag_configure("erro", background="#fad2cf")      # criado depois = prioridade maior
        pan.add(esq, weight=1)

        dir_ = ttk.Frame(pan)
        self.nb = ttk.Notebook(dir_)
        self.nb.pack(fill="both", expand=True)

        aba_img = ttk.Frame(self.nb)
        self.cv = tk.Canvas(aba_img, bg="#e8eaed", highlightthickness=0)
        sy2 = ttk.Scrollbar(aba_img, orient="vertical", command=self.cv.yview)
        sx2 = ttk.Scrollbar(aba_img, orient="horizontal", command=self.cv.xview)
        self.cv.configure(yscrollcommand=sy2.set, xscrollcommand=sx2.set)
        self.lbl_img = ttk.Label(aba_img, text="Nenhuma imagem ainda.", foreground="#5f6368")
        self.lbl_img.pack(side="bottom", anchor="w", padx=4)
        sy2.pack(side="right", fill="y")
        sx2.pack(side="bottom", fill="x")
        self.cv.pack(fill="both", expand=True)
        self.nb.add(aba_img, text=" Imagem ")

        self.t_exec = self._aba_texto(" Execução (log + ASCII) ")
        self.t_diag = self._aba_texto(" Diagnósticos ", quebra="word")
        self.t_c = self._aba_texto(" C gerado ")
        self.t_assist = self._aba_texto(" Assistente ")
        pan.add(dir_, weight=2)

    def _aba_texto(self, titulo, quebra="none"):
        quadro = ttk.Frame(self.nb)
        t = tk.Text(quadro, wrap=quebra, font=MONO, state="disabled", bg="#fafafa")
        sy = ttk.Scrollbar(quadro, orient="vertical", command=t.yview)
        sx = ttk.Scrollbar(quadro, orient="horizontal", command=t.xview)
        t.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        t.pack(fill="both", expand=True)
        self.nb.add(quadro, text=titulo)
        return t

    def _montar_rodape(self):
        rod = ttk.Frame(self)
        rod.pack(fill="x", padx=8, pady=(0, 6))
        self.var_status = tk.StringVar(value="Pronto.")
        ttk.Label(rod, textvariable=self.var_status).pack(side="left")
        self.barra = ttk.Progressbar(rod, mode="indeterminate", length=140)
        self.barra.pack(side="right")
        for texto, cmd in (("Abrir pasta de saída", self.acao_abrir_pasta),
                           ("Salvar imagem", self.acao_salvar_imagem),
                           ("Salvar .td", self.acao_salvar_td), ("Abrir .td", self.acao_abrir)):
            ttk.Button(rod, text=texto, command=cmd).pack(side="right", padx=3)

    # ------------------------------------------------------------------ utilidades de UI
    def _escrever(self, widget, texto):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", texto)
        widget.configure(state="disabled")

    def _anexar(self, widget, texto):
        widget.configure(state="normal")
        widget.insert("end", texto + "\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _set_editor(self, codigo):
        self.ed.delete("1.0", "end")
        self.ed.insert("1.0", codigo.rstrip("\n") + "\n")
        self.ed.tag_remove("erro", "1.0", "end")
        self.ed.tag_remove("aviso", "1.0", "end")

    def _texto_editor(self):
        return self.ed.get("1.0", "end-1c")

    def _inserir_pedido(self, pedido):
        self.txt_pedido.delete("1.0", "end")
        self.txt_pedido.insert("1.0", pedido)

    def _pintar_etapas(self, res):
        estados = dict(pipeline.etapas(res))
        estados["Pedido"] = "ok" if self._estado_assist != "pendente" else "pendente"
        estados["Assistente"] = self._estado_assist
        for nome, lb in self.etapas_lbl.items():
            lb.configure(bg=COR_ETAPA[estados.get(nome, "pendente")])

    def _status(self, texto):
        self.var_status.set(texto)

    def _carregar_inicial(self):
        casa = caminhos.pasta_exemplos() / "validos" / "casa.td"
        if casa.exists():
            self._set_editor(casa.read_text(encoding="utf-8"))
        self._inserir_pedido(PEDIDOS_EXEMPLO[0])
        self._pintar_etapas(None)

    # ------------------------------------------------------------------ trabalho em segundo plano
    def _rodar(self, rotulo, funcao, ao_terminar):
        """Executa trabalho lento fora da UI; a fila devolve dados à thread Tk.

        funcao não deve acessar widgets. ao_terminar recebe seu retorno em _poll.
        """
        if self._ocupado:
            return
        self._ocupado = True
        for b in (self.bt_gerar, self.bt_exec):
            b.state(["disabled"])
        self.barra.start(12)
        self._status(rotulo)

        def alvo():
            try:
                self.fila.put(("ok", ao_terminar, funcao()))
            except Exception as e:                               # noqa: BLE001 - repassa à UI
                self.fila.put(("erro", ao_terminar, e))
        threading.Thread(target=alvo, daemon=True).start()

    def _poll(self):
        try:
            while True:
                tipo, cb, dado = self.fila.get_nowait()
                if tipo == "log":
                    self._anexar(self.t_assist, dado)
                    self._status(dado)
                    continue
                self._ocupado = False
                self.barra.stop()
                for b in (self.bt_gerar, self.bt_exec):
                    b.state(["!disabled"])
                try:
                    if tipo == "ok":
                        cb(dado)
                    else:
                        self._tratar_erro(cb, dado)
                except Exception as e:                           # noqa: BLE001
                    messagebox.showerror("Erro inesperado", f"{type(e).__name__}: {e}")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _tratar_erro(self, cb, erro):
        self._status("Falhou.")
        if isinstance(erro, assistente.ErroAssistente):
            self._estado_assist = "erro"
            self._pintar_etapas(self._res)
            self._anexar(self.t_assist, f"ERRO: {erro}")
            self.nb.select(self.t_assist.master)
            messagebox.showwarning("Assistente", str(erro))
        else:
            messagebox.showerror("Erro inesperado", f"{type(erro).__name__}: {erro}")

    # ------------------------------------------------------------------ ações
    def acao_gerar(self):
        if self._ocupado:
            return
        pedido = self.txt_pedido.get("1.0", "end").strip()
        if not pedido:
            messagebox.showinfo("Pedido vazio", "Escreva o que você quer desenhar.")
            return
        self._escrever(self.t_assist, "")
        self._estado_assist = "pendente"
        self._pintar_etapas(None)

        def trabalho():
            return assistente.gerar(pedido,
                                    progresso=lambda m: self.fila.put(("log", None, m)))
        self._rodar("Gerando o programa .td...", trabalho, self._apos_gerar)

    def _apos_gerar(self, r):
        self._estado_assist = "ok" if r.valido else "erro"
        self._set_editor(r.codigo)
        self._escrever(self.t_assist, "\n".join(r.log))
        self.acao_executar()

    def acao_executar(self):
        if self._ocupado:
            return
        texto = self._texto_editor()
        if not texto.strip():
            return
        area = (max(320, self.cv.winfo_width() - 24), max(240, self.cv.winfo_height() - 24))
        self._rodar("Analisando, gerando C, compilando e executando...",
                    lambda: pipeline.executar_programa(texto, area=area), self._mostrar_resultado)

    def _mostrar_resultado(self, res):
        self._res = res
        t = res.transp
        self._pintar_etapas(res)
        self._escrever(self.t_diag, "\n".join(d.formatar("desenho.td") for d in t.diagnosticos)
                       or "Nenhum erro ou aviso.")
        self.ed.tag_remove("erro", "1.0", "end")
        self.ed.tag_remove("aviso", "1.0", "end")
        for d in t.diagnosticos:
            self.ed.tag_add("erro" if d.nivel == "erro" else "aviso", f"{d.linha}.0", f"{d.linha}.end+1c")
        self._escrever(self.t_c, t.codigo_c or "(nenhum código C foi gerado: o programa tem erros)")
        self.cv.delete("all")
        self._foto = None

        if not t.sucesso:
            self.lbl_img.configure(text="Sem imagem: corrija os erros marcados no editor.")
            self._escrever(self.t_exec, "")
            self.nb.select(self.t_diag.master)
            self._status(f"{len(t.erros)} erro(s) de {t.erros[0].fase}. Nenhum código foi gerado.")
            return
        if res.compilou is False:
            self._escrever(self.t_exec, res.log_compilacao)
            self.nb.select(self.t_exec.master)
            self._status("Falha ao compilar o C gerado.")
            if res.sem_compilador:
                messagebox.showwarning("Compilador C não encontrado", res.log_compilacao)
            return
        self._escrever(self.t_exec, res.saida_execucao)
        if res.png:
            self._foto = tk.PhotoImage(data=base64.b64encode(res.png).decode("ascii"))
            self.cv.create_image(12, 12, image=self._foto, anchor="nw")
            self.cv.configure(scrollregion=(0, 0, self._foto.width() + 24, self._foto.height() + 24))
            self.lbl_img.configure(text=f"{res.largura}x{res.altura} pixels (ampliado {res.ampliacao}x)  •  {res.ppm}")
            self.nb.select(self.cv.master)
            self._status(f"Pronto: {res.largura}x{res.altura} px, {len(t.avisos)} aviso(s).")
        else:
            self.nb.select(self.t_exec.master)
            self._status("O executável rodou, mas nenhuma imagem foi produzida.")

    # ------------------------------------------------------------------ arquivos
    def _carregar_arquivo(self, caminho):
        try:
            self._set_editor(Path(caminho).read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as e:
            messagebox.showerror("Abrir", str(e))
            return
        self._estado_assist = "pendente"
        self._pintar_etapas(None)
        self._status(f"Carregado: {caminho}")

    def acao_abrir(self):
        c = filedialog.askopenfilename(title="Abrir programa TinyDraw", filetypes=[("TinyDraw", "*.td"), ("Todos", "*.*")])
        if c:
            self._carregar_arquivo(c)

    def acao_salvar_td(self):
        c = filedialog.asksaveasfilename(title="Salvar programa TinyDraw", defaultextension=".td",
                                         filetypes=[("TinyDraw", "*.td")])
        if c:
            try:
                Path(c).write_text(self._texto_editor(), encoding="utf-8")
            except OSError as e:
                messagebox.showerror("Salvar programa", str(e))
                return
            self._status(f"Salvo: {c}")

    def acao_salvar_imagem(self):
        if not (self._res and self._res.png):
            messagebox.showinfo("Salvar imagem", "Gere um desenho primeiro.")
            return
        c = filedialog.asksaveasfilename(title="Salvar imagem", defaultextension=".png",
                                         filetypes=[("PNG ampliado", "*.png"), ("PPM original", "*.ppm")])
        if not c:
            return
        try:
            if c.lower().endswith(".ppm"):
                Path(c).write_bytes(self._res.ppm.read_bytes())
            else:
                Path(c).write_bytes(self._res.png)
        except OSError as e:
            messagebox.showerror("Salvar imagem", str(e))
            return
        self._status(f"Imagem salva: {c}")

    def acao_abrir_pasta(self):
        pasta = caminhos.pasta_saida_padrao()
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(pasta))                                  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(pasta)])
            else:
                subprocess.Popen(["xdg-open", str(pasta)])
        except OSError as e:
            messagebox.showinfo("Pasta de saída", f"{pasta}\n\n({e})")

    def acao_diagnostico(self):
        def ao_terminar(r):
            self._mostrar_texto("Diagnóstico do ambiente", r[1])
        self._rodar("Rodando o autoteste (exemplo casa.td)...", pipeline.autoteste, ao_terminar)

    def _mostrar_texto(self, titulo, texto):
        j = tk.Toplevel(self)
        j.title(titulo)
        j.geometry("760x520")
        t = tk.Text(j, wrap="word", font=MONO)
        t.insert("1.0", texto)
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)

    def _ver_referencia(self):
        self._mostrar_texto("Referência", REFERENCIA)

    def _fechar(self):
        self.destroy()


def iniciar():
    if sys.platform.startswith("win"):
        try:                                           # texto nítido em telas de alta resolução
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:                              # noqa: BLE001
            pass
    App().mainloop()
