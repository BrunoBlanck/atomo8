# -*- coding: utf-8 -*-
"""
ESQUEMA INTERATIVO DO HARDWARE DO LABIRINTO 3D

    python esquema/esquema.py

- Clique num componente: a barra lateral explica o que ele faz e os fios
  dele acendem.
- "Caminho da instrução": escolha uma instrução e veja por onde os dados
  passam (com os sinais de controle tirados do proprio hardware.py).
- "Simulação": roda o DOOM, a Bola ou o Tetris no MESMO hardware.py (porta a porta).
    Livre : so o display, o mais rapido possivel (ou no CLOCK real).
    Debug : instrucao por instrucao, com o valor de cada barramento bit a
            bit e as 5 fases do ciclo; velocidade de 1 a 6000 instrucoes
            por minuto, Pausar e Passo.
- Roda do mouse = zoom · arrastar o fundo = mover · F = ajustar · Esc = limpar.
- Com a simulacao aberta: W A S D (ou setas) e M sao os botoes do teclado.

So tkinter (vem com o Python). Os dados ficam em dados.py e simulacao.py.
"""

import os
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, RAIZ)

import dados                                    # noqa: E402
import hardware                                 # noqa: E402
import simulacao                                # noqa: E402
import portas                                   # noqa: E402
import visor_portas                             # noqa: E402

# ============================================================
# TEMA
# ============================================================

FUNDO = "#0d1117"
FUNDO_PONTO = "#222b38"
PAINEL = "#131a24"
PAINEL_BORDA = "#232c3a"
TEXTO = "#e6edf3"
TEXTO_SUAVE = "#8b98a9"
TEXTO_APAGADO = "#3b4555"
FIO = "#4a5668"
FIO_APAGADO = "#1f2733"
FIO_ATIVO = "#7ee0ff"
VALOR = "#ffe08a"
PIXEL_LIGADO = "#ff6f9a"
PIXEL_DESLIGADO = "#170d14"
VERDE = "#2ed39a"

MUNDO = (0, 0, 1870, 1040)                      # retangulo que contem tudo

VELOCIDADES_DEBUG = [1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1200, 3000, 6000]
TECLAS = {"w": 1, "Up": 1, "s": 2, "Down": 2, "a": 4, "Left": 4, "d": 8, "Right": 8, "m": 16}


def misturar(c1, c2, t):
    """Cor entre c1 (t=0) e c2 (t=1)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("{:02x}".format(int(x + (y - x) * t)) for x, y in zip(a, b))


def largura_px(bits):
    return {1: 1.6, 2: 2.0}.get(bits, 2.4 if bits <= 5 else 3.2 if bits <= 8 else 3.8)


# ============================================================
# APLICATIVO
# ============================================================

class Esquema:

    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Hardware do labirinto 3D · esquema interativo")
        raiz.configure(bg=FUNDO)
        raiz.geometry("1560x940")
        raiz.minsize(1100, 700)

        familias = set(tkfont.families())
        base = "Segoe UI" if "Segoe UI" in familias else "Helvetica"
        mono = "Cascadia Mono" if "Cascadia Mono" in familias else (
            "Consolas" if "Consolas" in familias else "Courier")
        self.f_base, self.f_mono = base, mono

        self.zoom = 1.0
        self.ox = self.oy = 0.0
        self.sel = None              # componente selecionado
        self.inst = None             # instrucao selecionada (caminho estatico)
        self.hover = None
        self.arrasto = None
        self.particulas = []
        self.ativos_fios = set()
        self.ativos_comps = set()
        self.valores_fios = {}       # fio -> (valor, bits) na simulacao
        self.arquivo_atual = None
        self._fontes = {}
        self.rotulos = []
        self.rotulados = set()

        # simulacao
        self.maq = None
        self.sim_aberta = False
        self.rodando = False
        self.rastro = None
        self.fios_sim = {}
        self.fase_vis = 4
        self._id_tick = None
        self._id_fase = None
        self._vram_vista = None
        self._ultimo_desenho = 0.0
        self._inicio_livre = None
        self.por_fio = {f[0]: (f[1], f[2]) for f in dados.FIOS}

        self._montar_interface()
        self.raiz.after(60, self.ajustar)
        self._animar()

    # ========================================================
    # interface
    # ========================================================
    def _montar_interface(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Escuro.TCombobox", fieldbackground=PAINEL, background=PAINEL,
                         foreground=TEXTO, arrowcolor=TEXTO, bordercolor=PAINEL_BORDA,
                         lightcolor=PAINEL, darkcolor=PAINEL, selectbackground=PAINEL,
                         selectforeground=TEXTO)
        estilo.map("Escuro.TCombobox", fieldbackground=[("readonly", PAINEL)],
                   foreground=[("readonly", TEXTO)])
        self.raiz.option_add("*TCombobox*Listbox.background", PAINEL)
        self.raiz.option_add("*TCombobox*Listbox.foreground", TEXTO)
        self.raiz.option_add("*TCombobox*Listbox.selectBackground", "#26324a")
        self.raiz.option_add("*TCombobox*Listbox.font", (self.f_mono, 10))

        # ---- topo
        topo = tk.Frame(self.raiz, bg=FUNDO)
        topo.pack(side="top", fill="x")
        tk.Label(topo, text="Hardware do labirinto 3D", bg=FUNDO, fg=TEXTO,
                 font=(self.f_base, 17, "bold")).pack(side="left", padx=(20, 10), pady=12)
        tk.Label(topo, text="tudo em portas lógicas · clique para explorar", bg=FUNDO,
                 fg=TEXTO_SUAVE, font=(self.f_base, 10)).pack(side="left", pady=(18, 12))

        self._botao(topo, "Limpar  Esc", self.limpar).pack(side="right", padx=(6, 20))
        self._botao(topo, "Ajustar  F", self.ajustar).pack(side="right", padx=6)
        self.bt_sim = self._botao(topo, "▶  Simulação", self.alternar_simulacao, destaque=True)
        self.bt_sim.pack(side="right", padx=6)

        self.var_inst = tk.StringVar(value="Caminho da instrução…")
        combo = ttk.Combobox(topo, textvariable=self.var_inst, values=list(dados.CAMINHOS),
                             width=22, state="readonly", style="Escuro.TCombobox",
                             font=(self.f_mono, 11))
        combo.pack(side="right", padx=12)
        combo.bind("<<ComboboxSelected>>", lambda e: self.escolher_instrucao(self.var_inst.get()))

        # ---- barra da simulacao (aparece com o botao Simulação)
        self.barra_sim = tk.Frame(self.raiz, bg=PAINEL, highlightthickness=1,
                                  highlightbackground=PAINEL_BORDA)
        self._montar_barra_sim(self.barra_sim)

        # ---- legenda
        self.legenda = tk.Frame(self.raiz, bg=FUNDO)
        self.legenda.pack(side="top", fill="x", padx=20, pady=(0, 8))
        for chave, (nome, cor) in dados.CATEGORIAS.items():
            f = tk.Frame(self.legenda, bg=FUNDO)
            f.pack(side="left", padx=(0, 16))
            c = tk.Canvas(f, width=12, height=12, bg=FUNDO, highlightthickness=0)
            c.create_oval(1, 1, 11, 11, fill=cor, outline="")
            c.pack(side="left", padx=(0, 5))
            tk.Label(f, text=nome, bg=FUNDO, fg=TEXTO_SUAVE,
                     font=(self.f_base, 9)).pack(side="left")

        # ---- corpo: tela + barra lateral
        corpo = tk.Frame(self.raiz, bg=FUNDO)
        corpo.pack(side="top", fill="both", expand=True)

        self.lateral = tk.Frame(corpo, bg=PAINEL, width=440,
                                highlightthickness=1, highlightbackground=PAINEL_BORDA)
        self.lateral.pack(side="right", fill="y")
        self.lateral.pack_propagate(False)

        self.tela = tk.Canvas(corpo, bg=FUNDO, highlightthickness=0, cursor="arrow")
        self.tela.pack(side="left", fill="both", expand=True)

        self._montar_lateral()

        t = self.tela
        t.bind("<Configure>", lambda e: self.desenhar())
        t.bind("<ButtonPress-1>", self._apertou)
        t.bind("<B1-Motion>", self._arrastou)
        t.bind("<ButtonRelease-1>", self._soltou)
        t.bind("<MouseWheel>", self._roda)
        t.bind("<Button-4>", lambda e: self._zoom_em(e.x, e.y, 1.12))
        t.bind("<Button-5>", lambda e: self._zoom_em(e.x, e.y, 1 / 1.12))
        t.bind("<Motion>", self._moveu)
        self.raiz.bind("<Escape>", lambda e: self.limpar())
        self.raiz.bind("<KeyPress>", self._tecla)

    def _botao(self, pai, texto, acao, destaque=False):
        fundo = "#173048" if destaque else PAINEL
        b = tk.Label(pai, text=texto, bg=fundo, fg=FIO_ATIVO if destaque else TEXTO,
                     padx=12, pady=5, font=(self.f_base, 9, "bold" if destaque else "normal"),
                     cursor="hand2", highlightthickness=1,
                     highlightbackground=misturar(PAINEL_BORDA, FIO_ATIVO, 0.4) if destaque
                     else PAINEL_BORDA)
        b._fundo = fundo
        b.bind("<Button-1>", lambda e: acao())
        b.bind("<Enter>", lambda e: b.configure(bg=misturar(b._fundo, "#ffffff", 0.08)))
        b.bind("<Leave>", lambda e: b.configure(bg=b._fundo))
        return b

    def _segmentado(self, pai, opcoes, inicial, acao):
        """Botoes lado a lado; so um fica marcado."""
        f = tk.Frame(pai, bg=PAINEL_BORDA)
        botoes = {}

        def marcar(nome, chamar=True):
            for n, b in botoes.items():
                ativo = n == nome
                b.configure(bg="#26405e" if ativo else PAINEL,
                            fg=TEXTO if ativo else TEXTO_SUAVE)
            if chamar:
                acao(nome)

        for nome in opcoes:
            b = tk.Label(f, text=nome, bg=PAINEL, fg=TEXTO_SUAVE, padx=12, pady=4,
                         font=(self.f_base, 9, "bold"), cursor="hand2")
            b.pack(side="left", padx=(0 if not botoes else 1, 0))
            b.bind("<Button-1>", lambda e, n=nome: marcar(n))
            botoes[nome] = b
        marcar(inicial, chamar=False)
        f.marcar = marcar
        return f

    def _montar_barra_sim(self, barra):
        def rotulo(texto):
            tk.Label(barra, text=texto, bg=PAINEL, fg=TEXTO_SUAVE,
                     font=(self.f_base, 8, "bold")).pack(side="left", padx=(16, 6))

        rotulo("PROGRAMA")
        self.prog_nome = "DOOM"
        self.seg_prog = self._segmentado(barra, ["DOOM", "Bola", "Tetris"], "DOOM", self.trocar_programa)
        self.seg_prog.pack(side="left")
        rotulo("MODO")
        self.modo = "Livre"
        self.seg_modo = self._segmentado(barra, ["Livre", "Debug"], "Livre", self.trocar_modo)
        self.seg_modo.pack(side="left")

        self.bt_rodar = self._botao(barra, "▶  Rodar", self.rodar_pausar, destaque=True)
        self.bt_rodar.pack(side="left", padx=(18, 4), pady=8)
        self._botao(barra, "⏭  Passo", self.passo).pack(side="left", padx=4)
        self._botao(barra, "⟲  Reiniciar", self.reiniciar).pack(side="left", padx=4)

        rotulo("VELOCIDADE")
        self.var_vel = tk.StringVar()
        self.combo_vel = ttk.Combobox(barra, textvariable=self.var_vel, width=18,
                                      state="readonly", style="Escuro.TCombobox",
                                      font=(self.f_mono, 10))
        self.combo_vel.pack(side="left")
        self.combo_vel.bind("<<ComboboxSelected>>", lambda e: self._velocidade_mudou())
        self._opcoes_velocidade()

        self.lb_estado = tk.Label(barra, text="", bg=PAINEL, fg=TEXTO_SUAVE,
                                  font=(self.f_mono, 9))
        self.lb_estado.pack(side="right", padx=16)

    def _opcoes_velocidade(self):
        if self.modo == "Livre":
            valores = ["CLOCK real ({:g} µs)".format(hardware.CLOCK_US), "Máxima"]
            self.combo_vel.configure(values=valores)
            self.var_vel.set(valores[0])
        else:
            valores = ["{} instr/min".format(v) for v in VELOCIDADES_DEBUG]
            self.combo_vel.configure(values=valores)
            self.var_vel.set("60 instr/min")

    def _instr_por_min(self):
        try:
            return int(self.var_vel.get().split()[0])
        except (ValueError, IndexError):
            return 60

    # ========================================================
    # barra lateral (abas: Componente / Simulação)
    # ========================================================
    def _montar_lateral(self):
        abas = tk.Frame(self.lateral, bg=PAINEL)
        abas.pack(side="top", fill="x", padx=16, pady=(14, 0))
        self.abas = {}
        for nome in ("Componente", "Simulação"):
            b = tk.Label(abas, text=nome, bg=PAINEL, fg=TEXTO_SUAVE, padx=10, pady=6,
                         font=(self.f_base, 9, "bold"), cursor="hand2")
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, n=nome: self.mostrar_aba(n))
            self.abas[nome] = b
        tk.Frame(self.lateral, bg=PAINEL_BORDA, height=1).pack(side="top", fill="x", padx=16)

        # ---------- aba Componente
        self.aba_comp = tk.Frame(self.lateral, bg=PAINEL)
        cab = tk.Frame(self.aba_comp, bg=PAINEL)
        cab.pack(side="top", fill="x", padx=22, pady=(16, 6))
        self.lb_chip = tk.Label(cab, text="", bg=PAINEL, fg=FUNDO,
                                font=(self.f_base, 8, "bold"), padx=8, pady=2)
        self.lb_chip.pack(side="top", anchor="w")
        self.lb_titulo = tk.Label(cab, text="", bg=PAINEL, fg=TEXTO, justify="left",
                                  font=(self.f_base, 18, "bold"), wraplength=370, anchor="w")
        self.lb_titulo.pack(side="top", anchor="w", pady=(8, 0))
        self.lb_sub = tk.Label(cab, text="", bg=PAINEL, fg=TEXTO_SUAVE, justify="left",
                               font=(self.f_mono, 9), anchor="w")
        self.lb_sub.pack(side="top", anchor="w", pady=(2, 0))
        self.botoes_comp = tk.Frame(self.aba_comp, bg=PAINEL)
        self.bt_portas = self._botao(self.botoes_comp, "Visualizar em portas lógicas",
                                     self.visualizar_portas, destaque=True)
        self.bt_doc = self._botao(self.botoes_comp, "Abrir documento  ↗", self.abrir_documento)
        self.vista_atual = None
        self.texto = self._texto(self.aba_comp)
        self.texto.pack(side="top", fill="both", expand=True)

        # ---------- aba Simulação
        self.aba_sim = tk.Frame(self.lateral, bg=PAINEL)
        topo = tk.Frame(self.aba_sim, bg=PAINEL)
        topo.pack(side="top", fill="x", padx=18, pady=(12, 4))
        self.lb_sim_titulo = tk.Label(topo, text="", bg=PAINEL, fg=TEXTO,
                                      font=(self.f_base, 14, "bold"))
        self.lb_sim_titulo.pack(side="left")
        self.lb_sim_estado = tk.Label(topo, text="", bg=PAINEL, fg=TEXTO_SUAVE,
                                      font=(self.f_mono, 9))
        self.lb_sim_estado.pack(side="right")

        px = 6
        lado = 32 * px
        self.painel = tk.Canvas(self.aba_sim, width=lado + 8, height=lado + 8, bg="#05070a",
                                highlightthickness=1,
                                highlightbackground=misturar(PAINEL, PIXEL_LIGADO, 0.35))
        self.painel.pack(side="top", pady=(4, 6))
        self.pixels = []
        for x in range(32):
            col = []
            for y in range(32):
                col.append(self.painel.create_rectangle(
                    4 + x * px + 1, 4 + y * px + 1, 4 + x * px + px, 4 + y * px + px,
                    fill=PIXEL_DESLIGADO, outline=""))
            self.pixels.append(col)

        teclas = tk.Frame(self.aba_sim, bg=PAINEL)
        teclas.pack(side="top", pady=(0, 6))
        for txt, bitv in (("W", 1), ("S", 2), ("A", 4), ("D", 8), ("M", 16)):
            b = self._botao(teclas, txt, lambda v=bitv: self._apertar(v))
            b.configure(padx=10, pady=2, font=(self.f_mono, 9, "bold"))
            b.pack(side="left", padx=2)
        tk.Label(teclas, text="teclado", bg=PAINEL, fg=TEXTO_SUAVE,
                 font=(self.f_base, 8)).pack(side="left", padx=(6, 0))

        self.fases_frame = tk.Frame(self.aba_sim, bg=PAINEL)
        self.fases_frame.pack(side="top", fill="x", padx=18, pady=(2, 2))
        self.lb_fases = []
        for i, (nome, _) in enumerate(simulacao.FASES):
            lb = tk.Label(self.fases_frame, text="{} {}".format(i + 1, nome), bg=PAINEL,
                          fg=TEXTO_APAGADO, font=(self.f_base, 8, "bold"), padx=5, pady=2)
            lb.pack(side="left", padx=(0, 2))
            self.lb_fases.append(lb)
        self.lb_fase_desc = tk.Label(self.aba_sim, text="", bg=PAINEL, fg=TEXTO_SUAVE,
                                     font=(self.f_base, 8), anchor="w", justify="left")
        self.lb_fase_desc.pack(side="top", fill="x", padx=18)

        self.sim_texto = self._texto(self.aba_sim, pady=4)
        self.sim_texto.configure(height=8)

        self.lb_codigo = tk.Label(self.aba_sim, text="CÓDIGO", bg=PAINEL, fg=TEXTO_SUAVE,
                                  font=(self.f_base, 8, "bold"), anchor="w")
        self.codigo = tk.Text(self.aba_sim, bg="#0f151e", fg=TEXTO_SUAVE, relief="flat",
                              wrap="none", font=(self.f_mono, 9), padx=10, pady=6, height=9,
                              highlightthickness=0, borderwidth=0, cursor="arrow")
        self.codigo.pack(side="bottom", fill="x", padx=16, pady=(2, 12))
        self.lb_codigo.pack(side="bottom", fill="x", padx=22, pady=(2, 0))
        self.sim_texto.pack(side="top", fill="both", expand=True)
        self.codigo.tag_configure("atual", background="#21405c", foreground=TEXTO)
        self.codigo.tag_configure("prox", background="#1a2533", foreground=TEXTO)
        self.codigo.tag_configure("rotulo", foreground="#b07cff")

        self.mostrar_aba("Componente")
        self.mostrar_inicio()

    def _texto(self, pai, pady=10):
        tx = tk.Text(pai, bg=PAINEL, fg=TEXTO, relief="flat", wrap="word",
                     font=(self.f_base, 10), padx=22, pady=pady, cursor="arrow",
                     highlightthickness=0, borderwidth=0, spacing1=2, spacing3=2)
        tx.tag_configure("h", font=(self.f_base, 8, "bold"), foreground=TEXTO_SUAVE,
                         spacing1=10, spacing3=3)
        tx.tag_configure("p", font=(self.f_base, 10), foreground=TEXTO, spacing3=4)
        tx.tag_configure("item", font=(self.f_base, 10), foreground=TEXTO,
                         lmargin1=4, lmargin2=18)
        tx.tag_configure("mono", font=(self.f_mono, 9), foreground="#c9d6e3",
                         lmargin1=4, lmargin2=4)
        tx.tag_configure("valor", font=(self.f_mono, 9, "bold"), foreground=VALOR)
        tx.tag_configure("sinal", font=(self.f_mono, 9, "bold"), foreground=FIO_ATIVO)
        tx.tag_configure("suave", font=(self.f_base, 9), foreground=TEXTO_SUAVE)
        return tx

    def mostrar_aba(self, nome):
        for n, b in self.abas.items():
            b.configure(fg=TEXTO if n == nome else TEXTO_SUAVE,
                        bg="#1b2533" if n == nome else PAINEL)
        self.aba_comp.pack_forget()
        self.aba_sim.pack_forget()
        (self.aba_comp if nome == "Componente" else self.aba_sim).pack(
            side="top", fill="both", expand=True)

    def _escrever(self, tx, blocos):
        tx.configure(state="normal")
        tx.delete("1.0", "end")
        for tipo, conteudo in blocos:
            if tipo == "h":
                tx.insert("end", conteudo.upper() + "\n", "h")
            elif tipo == "p":
                tx.insert("end", conteudo + "\n", "p")
            elif tipo == "lista":
                for item in conteudo:
                    tx.insert("end", "•  " + item + "\n", "item")
            elif tipo == "mono":
                tx.insert("end", conteudo + "\n", "mono")
            elif tipo == "sinais":
                for i, s in enumerate(conteudo):
                    tx.insert("end", ("   " if i else "") + s, "sinal")
                tx.insert("end", "\n")
            elif tipo == "suave":
                tx.insert("end", conteudo + "\n", "suave")
            elif tipo == "regs":                # [(nome, texto, mudou)]
                for nome, val, mudou in conteudo:
                    tx.insert("end", "{:<9}".format(nome), "mono")
                    tx.insert("end", val + "\n", "valor" if mudou else "mono")
        tx.configure(state="disabled")

    def _lateral(self, titulo, chip, cor, sub, blocos, arquivo=None, vista=None):
        self.mostrar_aba("Componente")
        self.lb_titulo.configure(text=titulo)
        self.lb_chip.configure(text=chip.upper(), bg=cor)
        self.lb_sub.configure(text=sub)
        self.arquivo_atual = arquivo
        self.vista_atual = vista
        self.bt_portas.pack_forget()
        self.bt_doc.pack_forget()
        if vista:
            self.bt_portas.pack(side="top", anchor="w", pady=(0, 6))
        if arquivo:
            self.bt_doc.pack(side="top", anchor="w")
        if vista or arquivo:
            self.botoes_comp.pack(side="top", anchor="w", padx=22, pady=(8, 4), before=self.texto)
        else:
            self.botoes_comp.pack_forget()
        self._escrever(self.texto, blocos)

    def mostrar_inicio(self):
        self._lateral(
            "Visão geral", "esquema", FIO_ATIVO, "computador dedicado · 8 bits",
            [("p", "Hardware mínimo para rodar o labirinto 3D num display 32 × 32. "
                   "Tudo é montado com portas lógicas (AND, OR, NOT, XOR) e "
                   "flip-flops; cada bloco tem um documento em componentes/."),
             ("h", "Como usar"),
             ("lista", ["Clique num bloco para ver o que ele faz.",
                        "Escolha uma instrução no topo para ver o caminho dos dados.",
                        "▶ Simulação: roda o DOOM, a Bola ou o Tetris no hardware simulado "
                        "(Livre ou Debug, bit a bit).",
                        "Roda do mouse: zoom · arrastar o fundo: mover.",
                        "F: ajustar à tela · Esc: limpar."]),
             ("h", "Números"),
             ("lista", ["A: 8 bits · PC: 11 bits · flags Z e C",
                        "ROM 2048 × 16 · RAM 256 × 8 · VRAM 128 × 8",
                        "16 opcodes · 1 instrução = 1 × CLOCK",
                        "doom: 1596 palavras · quadro 3D ~318 × CLOCK"]),
             ("h", "Formato da instrução"),
             ("mono", " 15..12   11..8    7..0\n [ OP ]  [  F  ] [ N  ]\n"
                      " saltos: destino = bits 10..0")])

    def mostrar_componente(self, c):
        nome_cat, cor = dados.CATEGORIAS[c["cat"]]
        blocos = [("p", c["resumo"])]
        if self.maq is not None:
            v = simulacao.valores_blocos(self.maq, self.rastro).get(c["id"])
            if v:
                blocos += [("h", "Agora (simulação)"), ("mono", v)]
        if c["entradas"]:
            blocos += [("h", "Entradas"), ("lista", c["entradas"])]
        if c["saidas"]:
            blocos += [("h", "Saídas"), ("lista", c["saidas"])]
        if c["sinais"]:
            blocos += [("h", "Sinais de controle"), ("sinais", c["sinais"])]
        if c["custo"]:
            blocos += [("h", "Custo"), ("p", c["custo"])]
        if c["tempo"]:
            blocos += [("h", "Tempo"), ("p", c["tempo"])]
        if c["instrucoes"]:
            blocos += [("h", "Instruções que usam"), ("p", c["instrucoes"])]
        if c["id"] == "dec":
            blocos += [("suave", "\nOs blocos acesos são os que recebem sinais do decodificador.")]
        dentro = " · dentro da ULA" if c["pai"] else ""
        self._lateral(c["nome"], nome_cat, cor, "componentes/" + c["arquivo"] + dentro,
                      blocos, os.path.join(RAIZ, "componentes", c["arquivo"]),
                      portas.DO_ESQUEMA.get(c["id"]))

    def mostrar_instrucao(self, nome):
        cam = dados.CAMINHOS[nome]
        op, f, tipo = hardware.INSTRUCOES[nome]
        exemplo = nome + {"n": " 5", "m": " 5", "e": " 0", "": ""}[tipo]
        palavra = hardware.montar_binario(exemplo)[0]
        sinais = hardware.decodifica(op, f)
        ativos = [s for s in sinais.__slots__ if getattr(sinais, s)]
        flags = ("Z e C" if sinais.C_WE else "Z" if sinais.Z_WE else "nenhuma")
        self._lateral(
            nome, "instrução", FIO_ATIVO, "opcode {} · F = {:04b}".format(op, f),
            [("p", cam["descricao"]),
             ("h", "Palavra na ROM"),
             ("mono", "{}\n{}".format(exemplo, palavra)),
             ("h", "Sinais ativos (hardware.decodifica)"),
             ("sinais", ativos or ["nenhum"]),
             ("h", "Flags que mudam"), ("p", flags),
             ("h", "Caminho"),
             ("lista", [dados.POR_ID[c]["nome"] for c in cam["comps"] if c != "relogio"]),
             ("suave", "\nBusca (PC → ROM → decodificador, PC + 1) acontece em toda "
                       "instrução. Tudo em 1 × CLOCK.")])

    def visualizar_portas(self):
        if self.vista_atual:
            visor_portas.abrir(self.raiz, self.vista_atual)

    def abrir_documento(self):
        caminho = self.arquivo_atual
        if not caminho or not os.path.exists(caminho):
            return
        try:
            os.startfile(caminho)                       # Windows
        except AttributeError:
            import webbrowser
            webbrowser.open("file://" + caminho)

    # ========================================================
    # selecao no esquema
    # ========================================================
    def selecionar(self, cid):
        self.inst = None
        self.var_inst.set("Caminho da instrução…")
        self.sel = cid
        c = dados.POR_ID[cid]
        fios, comps = set(), {cid}
        grupo = {cid} | {x["id"] for x in dados.COMPONENTES if x["pai"] == cid}
        for fid, de, para, *_ in dados.FIOS:
            if de in grupo or para in grupo:
                fios.add(fid)
                comps.update((de, para))
        if cid == "dec":
            comps.update(x["id"] for x in dados.COMPONENTES if x["sinais"])
            fios.add("rom_dec")
        if c["pai"]:
            comps.add(c["pai"])
        self.ativos_fios, self.ativos_comps = fios, comps
        self.valores_fios = {}
        self.mostrar_componente(c)
        self.desenhar()

    def escolher_instrucao(self, nome):
        if nome not in dados.CAMINHOS:
            return
        self.sel = None
        self.inst = nome
        cam = dados.CAMINHOS[nome]
        self.ativos_fios = set(cam["fios"])
        self.ativos_comps = set(cam["comps"])
        self.valores_fios = {}
        self.mostrar_instrucao(nome)
        self.desenhar()

    def limpar(self):
        self.sel = self.inst = None
        self.var_inst.set("Caminho da instrução…")
        self._aplicar_destaque_sim()
        if self.sim_aberta:
            self.mostrar_aba("Simulação")
        else:
            self.mostrar_inicio()
        self.desenhar()

    def _aplicar_destaque_sim(self):
        """Sem selecao: o destaque vem da ultima instrucao simulada."""
        if self.sim_aberta and self.rastro is not None and self.modo == "Debug":
            vis = {f: v for f, v in self.fios_sim.items() if v[2] <= self.fase_vis}
            self.ativos_fios = set(vis)
            self.valores_fios = {f: (v[0], v[1]) for f, v in vis.items()}
            self.ativos_comps = simulacao.blocos_ativos(self.rastro, vis, self.por_fio)
        else:
            self.ativos_fios, self.ativos_comps, self.valores_fios = set(), set(), {}

    # ========================================================
    # simulacao
    # ========================================================
    def alternar_simulacao(self):
        self.sim_aberta = not self.sim_aberta
        if self.sim_aberta:
            self.barra_sim.pack(side="top", fill="x", padx=16, pady=(0, 8), before=self.legenda)
            self.bt_sim.configure(text="■  Fechar simulação")
            if self.maq is None:
                self.reiniciar()
            self.sel = self.inst = None
            self.mostrar_aba("Simulação")
        else:
            self.pausar()
            self.barra_sim.pack_forget()
            self.bt_sim.configure(text="▶  Simulação")
            self.rastro = None
            self.maq = None
            self.limpar()
        self._aplicar_destaque_sim()
        self.desenhar()

    def trocar_programa(self, nome):
        self.prog_nome = nome
        self.seg_prog.marcar(nome, chamar=False)
        self.reiniciar()

    def trocar_modo(self, nome):
        self.modo = nome
        self.seg_modo.marcar(nome, chamar=False)
        self._opcoes_velocidade()
        if self.rodando:
            self._agendar(0)
        self._aplicar_destaque_sim()
        self.atualizar_sim()
        self.desenhar()

    def _velocidade_mudou(self):
        self._inicio_livre = None
        if self.rodando:
            self._agendar(0)

    def reiniciar(self):
        rodava = self.rodando
        self.pausar()
        self.maq = simulacao.Maquina(simulacao.programas()[self.prog_nome])
        self.rastro = None
        self.fios_sim = {}
        self._vram_vista = None
        self._aplicar_destaque_sim()
        self.atualizar_sim()
        self.desenhar()
        if rodava:
            self.rodar_pausar()

    def rodar_pausar(self):
        if self.rodando:
            self.pausar()
        else:
            if self.maq is None:
                self.reiniciar()
            self.rodando = True
            self._inicio_livre = None
            self.bt_rodar.configure(text="⏸  Pausar")
            self._agendar(0)
        self.atualizar_sim()

    def pausar(self):
        self.rodando = False
        for attr in ("_id_tick", "_id_fase"):
            ident = getattr(self, attr)
            if ident:
                self.raiz.after_cancel(ident)
                setattr(self, attr, None)
        if hasattr(self, "bt_rodar"):
            self.bt_rodar.configure(text="▶  Rodar")
        if self.maq is not None:
            self.fase_vis = 4
            self._aplicar_destaque_sim()
            self.atualizar_sim()
            self.desenhar()

    def _agendar(self, ms):
        if self._id_tick:
            self.raiz.after_cancel(self._id_tick)
        self._id_tick = self.raiz.after(int(ms), self._tick)

    def _tick(self):
        self._id_tick = None
        if not self.rodando or self.maq is None:
            return
        if self.modo == "Livre":
            self._tick_livre()
        else:
            intervalo = 60000.0 / self._instr_por_min()
            self._executar_rastreado(animar=intervalo >= 1000, duracao=intervalo * 0.8)
            self._agendar(intervalo)

    def _tick_livre(self):
        m = self.maq
        agora = time.perf_counter()
        limite = agora + 0.025
        real = self.var_vel.get().startswith("CLOCK")
        if real:
            if self._inicio_livre is None:
                self._inicio_livre = (agora, m.clocks)
            t0, c0 = self._inicio_livre
            alvo = c0 + (agora - t0) * 1e6 / hardware.CLOCK_US
            while m.clocks < alvo and time.perf_counter() < limite:
                for _ in range(50):
                    m.passo()
            if m.clocks < alvo - 200000:              # simulador atrasado: nao acumula
                self._inicio_livre = (agora, m.clocks)
        else:
            while time.perf_counter() < limite:
                for _ in range(100):
                    m.passo()
        self.rastro = None
        self.atualizar_painel()
        if agora - self._ultimo_desenho > 0.5:        # valores nos blocos, devagar
            self._ultimo_desenho = agora
            self.atualizar_sim()
            self._aplicar_destaque_sim()
            self.desenhar()
        self._agendar(15)

    def passo(self):
        if self.maq is None:
            self.alternar_simulacao() if not self.sim_aberta else self.reiniciar()
        if self.rodando:
            self.pausar()
        if self.modo != "Debug":
            self.modo = "Debug"
            self.seg_modo.marcar("Debug", chamar=False)
            self._opcoes_velocidade()
        self._executar_rastreado(animar=True, duracao=900)

    def _executar_rastreado(self, animar, duracao):
        r = self.maq.passo_rastreado()
        self.rastro = r
        self.fios_sim = simulacao.caminho(r)
        if self._id_fase:
            self.raiz.after_cancel(self._id_fase)
            self._id_fase = None
        if animar:
            self.fase_vis = 0
            self._passo_fase(duracao / len(simulacao.FASES))
        else:
            self.fase_vis = 4
        self.sel = self.inst = None
        self._aplicar_destaque_sim()
        self.atualizar_painel()
        self.atualizar_sim()
        self.desenhar()

    def _passo_fase(self, ms):
        self._id_fase = None
        if self.fase_vis >= 4:
            return
        def avancar():
            self.fase_vis += 1
            if not self.sel and not self.inst:
                self._aplicar_destaque_sim()
                self.desenhar()
            self.atualizar_sim()
            self._passo_fase(ms)
        self._id_fase = self.raiz.after(int(max(60, ms)), avancar)

    def _apertar(self, bitv):
        if self.maq is not None:
            self.maq.apertar(bitv)
            self.atualizar_sim()

    def _tecla(self, e):
        if isinstance(e.widget, ttk.Combobox):
            return
        k = e.keysym
        if self.sim_aberta and self.maq is not None:
            chave = k if k in TECLAS else k.lower()
            if chave in TECLAS:
                self._apertar(TECLAS[chave])
                return
            if k == "space":
                self.rodar_pausar()
                return
            if k in ("n", "N", "period"):
                self.passo()
                return
        if k in ("f", "F"):
            self.ajustar()

    # ---------- atualizacao dos paineis da simulacao
    def atualizar_painel(self):
        if self.maq is None:
            return
        vram = bytes(self.maq.display.vram)
        if vram == self._vram_vista:
            return
        antigo = self._vram_vista or bytes(128)
        for i in range(128):
            if self._vram_vista is not None and vram[i] == antigo[i]:
                continue
            x, pag = i >> 2, i & 3
            for b in range(8):
                y = pag * 8 + b
                self.painel.itemconfigure(self.pixels[x][y], fill=PIXEL_LIGADO
                                          if (vram[i] >> b) & 1 else PIXEL_DESLIGADO)
        self._vram_vista = vram

    def atualizar_fases(self):
        debug = self.modo == "Debug" and self.rastro is not None
        for i, lb in enumerate(self.lb_fases):
            if debug and i == self.fase_vis:
                lb.configure(bg="#26405e", fg=TEXTO)
            elif debug and i < self.fase_vis:
                lb.configure(bg=PAINEL, fg=FIO_ATIVO)
            else:
                lb.configure(bg=PAINEL, fg=TEXTO_APAGADO)
        if debug:
            nome, desc = simulacao.FASES[self.fase_vis]
            self.lb_fase_desc.configure(text="Fase {}: {}".format(self.fase_vis + 1, desc))
        else:
            self.lb_fase_desc.configure(text="")

    def atualizar_sim(self):
        m = self.maq
        if m is None:
            return
        estado = "rodando" if self.rodando else "pausado"
        self.lb_sim_titulo.configure(text="{} · {}".format(self.prog_nome, self.modo))
        self.lb_sim_estado.configure(text=estado)
        self.lb_estado.configure(text="instr {:,}  ·  {:,} × CLOCK  ·  quadros {}".format(
            m.ciclos, m.clocks, m.quadros).replace(",", " "))
        self.atualizar_fases()

        r = self.rastro
        h = lambda v, d=2: "0x{:0{}X}".format(v, d)
        blocos = []
        if r is not None:
            s = r["sinais"]
            palavra = format(r["palavra"], "016b")
            blocos += [("h", "Instrução executada"),
                       ("mono", "{}  {}\n{} {} {}".format(
                           h(r["pc"], 3), hardware.desmontar(r["palavra"]),
                           palavra[:4], palavra[4:8], palavra[8:])),
                       ("sinais", [n for n in s.__slots__ if getattr(s, n)] or ["nenhum"])]
            regs = [("PC", "{} → {}".format(h(r["pc"], 3), h(m.pc, 3)), True),
                    ("A", "{} → {}  {:08b}".format(h(r["a"]), h(m.a), m.a), r["a"] != m.a),
                    ("Z  C", "{} {} → {} {}".format(r["z"], r["c"], m.z, m.c),
                     (r["z"], r["c"]) != (m.z, m.c)),
                    ("ponteiro", "{} → {}".format(h(r["ponteiro"]), h(m.ponteiro)),
                     r["ponteiro"] != m.ponteiro),
                    ("cursor", "{} → {}".format(h(r["cursor"]), h(m.cursor)),
                     r["cursor"] != m.cursor)]
            if s.RAM_WE:
                regs.append(("RAM", "[{}] ← {}".format(h(r["end"]), h(r["a"])), True))
            if s.VID_WR:
                regs.append(("VRAM", "[{}] ← {:08b}".format(h(r["cursor"]), r["a"]), True))
        else:
            blocos += [("h", "Próxima instrução"),
                       ("mono", "{}  {}".format(h(m.pc, 3), hardware.desmontar(m.rom[m.pc])))]
            regs = [("PC", h(m.pc, 3), False), ("A", "{}  {:08b}".format(h(m.a), m.a), False),
                    ("Z  C", "{} {}".format(m.z, m.c), False),
                    ("ponteiro", h(m.ponteiro), False), ("cursor", h(m.cursor), False)]
        regs.append(("teclado", "{:05b} pendente".format(m.teclas_pendentes),
                     m.teclas_pendentes != 0))
        blocos += [("h", "Registradores"), ("regs", regs)]
        if r is not None and self.modo == "Debug":
            linhas = []
            for fio, (val, bits, fase) in sorted(self.fios_sim.items(), key=lambda x: x[1][2]):
                if fase > self.fase_vis:
                    continue
                de, para = self.por_fio[fio]
                nome = "{}→{}".format(simulacao.CURTO[de], simulacao.CURTO[para])
                hexa = "0x{:0{}X}".format(val, (bits + 3) // 4)
                linhas.append("{} {:<13} {:>5}  {}".format(fase + 1, nome, hexa,
                                                         format(val, "0{}b".format(bits))))
            blocos += [("h", "Barramentos (fase · origem→destino · valor · bits)"),
                       ("mono", "\n".join(linhas))]
        self._escrever(self.sim_texto, blocos)
        self._atualizar_codigo(r)

    def _atualizar_codigo(self, r):
        m = self.maq
        cod = self.codigo
        cod.configure(state="normal")
        cod.delete("1.0", "end")
        atual = m.linha_de[r["pc"]] if r is not None else None
        prox = m.linha_atual()
        centro = atual or prox or 1
        ini = max(1, centro - 3)
        fim = min(len(m.fonte), ini + 10)
        for num in range(ini, fim + 1):
            texto = m.fonte[num - 1].rstrip()
            marca = "▶ " if num == atual else ("· " if num == prox else "  ")
            linha = "{}{:4d}  {}\n".format(marca, num, texto[:46])
            tag = "atual" if num == atual else ("prox" if num == prox else None)
            ini_idx = cod.index("end-1c")
            cod.insert("end", linha, tag or ())
            if texto.strip().endswith(":") or (":" in texto.split(";")[0] and not tag):
                cod.tag_add("rotulo", ini_idx, cod.index("end-1c"))
        cod.configure(state="disabled")

    # ========================================================
    # coordenadas e mouse
    # ========================================================
    def tx(self, x, y):
        return x * self.zoom + self.ox, y * self.zoom + self.oy

    def ajustar(self):
        w = max(self.tela.winfo_width(), 100)
        h = max(self.tela.winfo_height(), 100)
        x0, y0, x1, y1 = MUNDO
        margem = 30
        self.zoom = min((w - 2 * margem) / (x1 - x0), (h - 2 * margem) / (y1 - y0))
        self.ox = (w - (x1 - x0) * self.zoom) / 2 - x0 * self.zoom
        self.oy = (h - (y1 - y0) * self.zoom) / 2 - y0 * self.zoom
        self.desenhar()

    def _zoom_em(self, mx, my, fator):
        novo = max(0.25, min(3.5, self.zoom * fator))
        fator = novo / self.zoom
        self.ox = mx - (mx - self.ox) * fator
        self.oy = my - (my - self.oy) * fator
        self.zoom = novo
        self.desenhar()

    def _roda(self, e):
        self._zoom_em(e.x, e.y, 1.12 if e.delta > 0 else 1 / 1.12)

    def _bloco_sob_mouse(self):
        for tag in self.tela.gettags("current"):
            if tag.startswith("blk:"):
                return tag[4:]
        return None

    def _apertou(self, e):
        self.tela.focus_set()
        cid = self._bloco_sob_mouse()
        if cid:
            self.selecionar(cid)
            self.arrasto = None
        else:
            self.arrasto = (e.x, e.y, self.ox, self.oy, False)

    def _arrastou(self, e):
        if not self.arrasto:
            return
        x0, y0, ox, oy, _ = self.arrasto
        if abs(e.x - x0) + abs(e.y - y0) > 3:
            self.arrasto = (x0, y0, ox, oy, True)
            self.ox = ox + e.x - x0
            self.oy = oy + e.y - y0
            self.tela.configure(cursor="fleur")
            self.desenhar()

    def _soltou(self, e):
        if self.arrasto and not self.arrasto[4]:
            self.limpar()
        self.arrasto = None
        self.tela.configure(cursor="arrow")

    def _moveu(self, e):
        cid = self._bloco_sob_mouse()
        if cid != self.hover:
            antigo, self.hover = self.hover, cid
            for x in (antigo, cid):
                if x:
                    self._pintar_contorno(x)
            self.tela.configure(cursor="hand2" if cid else "arrow")

    # ========================================================
    # desenho
    # ========================================================
    def _destaque(self):
        return bool(self.ativos_comps)

    def _cor_bloco(self, c):
        cor = dados.CATEGORIAS[c["cat"]][1]
        ativo = (not self._destaque()) or c["id"] in self.ativos_comps
        return cor, ativo

    def _pintar_contorno(self, cid):
        c = dados.POR_ID[cid]
        cor, ativo = self._cor_bloco(c)
        if cid == self.hover or cid == self.sel:
            contorno, larg = misturar(cor, "#ffffff", 0.35), 2.6
        elif ativo:
            contorno, larg = cor, 1.6
        else:
            contorno, larg = misturar(FUNDO, cor, 0.25), 1.2
        self.tela.itemconfigure("forma:" + cid, outline=contorno, width=larg)

    def _fonte(self, familia, tam, negrito=False):
        chave = (familia, tam, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = tkfont.Font(family=familia, size=tam,
                                              weight="bold" if negrito else "normal")
        return self._fontes[chave]

    def _retangulo(self, x0, y0, x1, y1, r, **kw):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
               x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.tela.create_polygon(pts, smooth=True, **kw)

    def desenhar(self):
        t = self.tela
        t.delete("all")
        self.particulas = []
        self.rotulos = []
        self.rotulados = set()
        z = self.zoom
        w, h = t.winfo_width(), t.winfo_height()
        self.valores_bloco = (simulacao.valores_blocos(self.maq, self.rastro)
                              if self.maq is not None else {})

        passo = 40 * z
        if passo >= 14:
            x0 = self.ox % passo
            yy = self.oy % passo
            while yy < h:
                xx = x0
                while xx < w:
                    t.create_rectangle(xx, yy, xx + 1, yy + 1, outline="", fill=FUNDO_PONTO)
                    xx += passo
                yy += passo

        ordem = sorted(dados.COMPONENTES, key=lambda c: 0 if c["id"] == "ula" else 1)
        self._desenhar_bloco(ordem[0])
        # fios com valor por ultimo (os rotulos com bits ficam por cima)
        fios = sorted(dados.FIOS, key=lambda f: f[0] in self.valores_fios)
        for fio in fios:
            if fio[0] not in self.valores_fios:
                self._desenhar_fio(*fio)
        for c in ordem[1:]:
            self._desenhar_bloco(c)
        for fio in fios:
            if fio[0] in self.valores_fios:
                self._desenhar_fio(*fio)

    def _lugar_rotulo(self, tela_pts, lw, lh, estrito=False):
        trechos = sorted(zip(tela_pts, tela_pts[1:]),
                         key=lambda s: -(abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1])))
        for (ax, ay), (bx, by) in trechos:
            horiz = abs(by - ay) < 1
            tam = abs(bx - ax) if horiz else abs(by - ay)
            if tam < (lw if horiz else lh) + 16:
                continue
            for fr in (0.5, 0.3, 0.7, 0.2, 0.8):
                cx, cy = ax + (bx - ax) * fr, ay + (by - ay) * fr
                caixa = (cx - lw / 2, cy - lh / 2, cx + lw / 2, cy + lh / 2)
                if not any(caixa[0] < o[2] and o[0] < caixa[2] and
                           caixa[1] < o[3] and o[1] < caixa[3] for o in self.rotulos):
                    return caixa
        if estrito:
            return None
        # nenhum trecho comprido livre: encosta no meio do maior, mesmo sobrepondo
        (ax, ay), (bx, by) = trechos[0]
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        return (cx - lw / 2, cy - lh / 2, cx + lw / 2, cy + lh / 2)

    def _desenhar_fio(self, fid, de, para, bits, rotulo, pontos):
        t = self.tela
        z = self.zoom
        ativo = fid in self.ativos_fios
        apagado = self._destaque() and not ativo
        cor = FIO_ATIVO if ativo else (FIO_APAGADO if apagado else FIO)
        tela_pts = [self.tx(x, y) for x, y in pontos]
        plano = [v for p in tela_pts for v in p]
        larg = max(1.0, largura_px(bits) * z * (1.25 if ativo else 1))
        seta = (8 * z + 2, 10 * z + 2, 3.5 * z + 1)
        if ativo:
            t.create_line(*plano, fill=misturar(FUNDO, FIO_ATIVO, 0.25),
                          width=larg + 5 * z, capstyle="round", joinstyle="round")
        t.create_line(*plano, fill=cor, width=larg, arrow="last", arrowshape=seta,
                      capstyle="round", joinstyle="round")
        if fid in self.valores_fios:
            self._rotulo_valor(tela_pts, rotulo, *self.valores_fios[fid])
        elif rotulo and z >= 0.4 and not apagado and (de, rotulo, ativo) not in self.rotulados:
            texto = "{} · {}".format(rotulo, bits) if bits > 1 else rotulo
            fonte = self._fonte(self.f_mono, max(7, int(8.5 * z)))
            lw, lh = fonte.measure(texto) + 8, fonte.metrics("linespace") + 2
            trechos_ok = any(abs(b[0] - a[0]) + abs(b[1] - a[1]) >= lw + 16
                             for a, b in zip(tela_pts, tela_pts[1:]))
            if trechos_ok:
                x0, y0, x1, y1 = self._lugar_rotulo(tela_pts, lw, lh)
                self.rotulos.append((x0, y0, x1, y1))
                self.rotulados.add((de, rotulo, ativo))
                t.create_rectangle(x0, y0, x1, y1, fill=FUNDO, outline=misturar(FUNDO, cor, 0.5))
                t.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=texto, font=fonte,
                              fill=FIO_ATIVO if ativo else TEXTO_SUAVE)
        if ativo:
            self._criar_particulas(tela_pts)

    def _rotulo_valor(self, tela_pts, rotulo, valor, bits):
        """Rotulo da simulacao: nome, valor em hexa e uma luz por bit (MSB a esquerda)."""
        t = self.tela
        z = max(self.zoom, 0.55)
        fonte = self._fonte(self.f_mono, max(7, int(8.5 * z)), True)
        digitos = (bits + 3) // 4
        texto = "{} {}".format(rotulo or "", "0x{:0{}X}".format(valor, digitos)).strip() \
            if bits > 1 else "{} {}".format(rotulo or "", valor).strip()
        cel = max(5.0, 7.0 * z)
        tw = fonte.measure(texto)
        lh = max(fonte.metrics("linespace") + 4, cel + 6)
        lw = tw + 10 + bits * cel + 6
        caixa = self._lugar_rotulo(tela_pts, lw, lh, estrito=True)
        if caixa is None:                 # nao cabe com os bits: so o valor
            hexa = texto.split()[-1]
            tw = fonte.measure(hexa)
            caixa = self._lugar_rotulo(tela_pts, tw + 10, lh, estrito=True)
            if caixa is None:             # fio curto: o valor fica so na barra lateral
                return
            x0, y0, x1, y1 = caixa
            self.rotulos.append(caixa)
            t.create_rectangle(x0, y0, x1, y1, fill="#0a1a24", outline=FIO_ATIVO)
            t.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=hexa, font=fonte, fill=VALOR)
            return
        x0, y0, x1, y1 = caixa
        self.rotulos.append(caixa)
        t.create_rectangle(x0, y0, x1, y1, fill="#0a1a24", outline=FIO_ATIVO)
        t.create_text(x0 + 5, (y0 + y1) / 2, text=texto, anchor="w", font=fonte, fill=VALOR)
        bx = x0 + 5 + tw + 6
        cy = (y0 + y1) / 2
        for i in range(bits):
            b = (valor >> (bits - 1 - i)) & 1
            t.create_rectangle(bx + i * cel, cy - cel / 2 + 0.5, bx + (i + 1) * cel - 1.5,
                               cy + cel / 2 - 0.5, outline=misturar(FUNDO, FIO_ATIVO, 0.6),
                               fill=VALOR if b else "#0d1117")

    def _desenhar_bloco(self, c):
        t = self.tela
        z = self.zoom
        cid = c["id"]
        cor, ativo = self._cor_bloco(c)
        x0, y0 = self.tx(c["x"], c["y"])
        x1, y1 = self.tx(c["x"] + c["l"], c["y"] + c["a"])
        conteiner = cid == "ula"
        tags = ("blk:" + cid,)

        corpo = misturar(FUNDO, cor, (0.07 if ativo else 0.03) if conteiner
                         else (0.16 if ativo else 0.05))
        if not conteiner and ativo:
            self._retangulo(x0 + 3 * z, y0 + 4 * z, x1 + 3 * z, y1 + 4 * z, 12 * z,
                            fill="#07090d", outline="", tags=tags)
        self._retangulo(x0, y0, x1, y1, 12 * z, fill=corpo, outline=cor, width=1.6,
                        tags=tags + ("forma:" + cid,))
        if not conteiner:
            t.create_rectangle(x0 + 1, y0 + 10 * z, x0 + 4 * z + 1, y1 - 10 * z,
                               fill=cor if ativo else misturar(FUNDO, cor, 0.3),
                               outline="", tags=tags)

        cor_txt = TEXTO if ativo else TEXTO_APAGADO
        cor_sub = TEXTO_SUAVE if ativo else TEXTO_APAGADO
        pequeno = c["pai"] is not None
        valor = self.valores_bloco.get(cid)
        livre = (x1 - x0) - 40 * z
        tam = max(6, int((10 if pequeno else 12) * z))
        while tam > 6 and self._fonte(self.f_base, tam, True).measure(c["nome"]) > livre:
            tam -= 1
        if conteiner:
            t.create_text(x0 + 16 * z, y0 + 22 * z, text="ULA", anchor="w", fill=cor_txt,
                          font=(self.f_base, max(7, int(15 * z)), "bold"), tags=tags)
            sub = valor or c["subtitulo"]
            t.create_text(x0 + 70 * z, y0 + 23 * z, text=sub, anchor="w",
                          fill=VALOR if valor else cor_sub,
                          font=(self.f_mono if valor else self.f_base, max(6, int(9 * z))),
                          tags=tags)
        else:
            cy = (y0 + y1) / 2
            if cid == "vram":
                cy = y0 + 32 * z
            sub = valor or c["subtitulo"]
            dy = 9 * z if sub and z > 0.45 else 0
            t.create_text(x0 + 14 * z, cy - dy, text=c["nome"], anchor="w", fill=cor_txt,
                          font=(self.f_base, tam, "bold"), tags=tags)
            if dy:
                fonte_sub = (self.f_mono, max(6, int(8 * z)), "bold") if valor else \
                    (self.f_base, max(6, int((8 if pequeno else 9) * z)))
                t.create_text(x0 + 14 * z, cy + dy + 2 * z, text=sub, anchor="w",
                              fill=VALOR if valor else cor_sub, font=fonte_sub, tags=tags)
        if z > 0.45:
            ny = y1 - 9 * z if pequeno else y0 + 11 * z
            t.create_text(x1 - 10 * z, ny, text=c["arquivo"][:2], anchor="e",
                          fill=misturar(FUNDO, cor, 0.8) if ativo else TEXTO_APAGADO,
                          font=(self.f_mono, max(6, int(8 * z)), "bold"), tags=tags)
        if cid == "vram" and z > 0.4:
            if self.maq is not None:
                self._mini_vram(x0 + 14 * z, y0 + 58 * z, 100 * z, tags)
            else:
                self._mini_painel(x0 + 14 * z, y0 + 118 * z, 46 * z, ativo, tags)
        self._pintar_contorno(cid)

    def _mini_vram(self, x, y, lado, tags):
        """A VRAM de verdade, desenhada dentro do bloco."""
        t = self.tela
        t.create_rectangle(x, y, x + lado, y + lado, fill="#05070a",
                           outline=misturar(FUNDO, PIXEL_LIGADO, 0.4), tags=tags)
        p = lado / 32
        vram = self.maq.display.vram
        cursor = self.maq.cursor
        for i in range(128):
            v = vram[i]
            if not v:
                continue
            cx, pag = i >> 2, i & 3
            for b in range(8):
                if (v >> b) & 1:
                    yy = pag * 8 + b
                    t.create_rectangle(x + cx * p, y + yy * p, x + (cx + 1) * p,
                                       y + (yy + 1) * p, fill=PIXEL_LIGADO, outline="",
                                       tags=tags)
        # onde o cursor esta (1 byte = 1 coluna x 8 linhas)
        cx, pag = cursor >> 2, cursor & 3
        t.create_rectangle(x + cx * p, y + pag * 8 * p, x + (cx + 1) * p,
                           y + (pag + 1) * 8 * p, outline=VALOR, tags=tags)

    def _mini_painel(self, x, y, lado, ativo, tags):
        t = self.tela
        t.create_rectangle(x, y, x + lado, y + lado, fill="#05070a",
                           outline=misturar(FUNDO, "#ff5c8a", 0.4), tags=tags)
        p = lado / 16
        cor = "#ff8fb0" if ativo else TEXTO_APAGADO
        for i in range(16):
            if i % 2 == 0:
                t.create_rectangle(x + i * p, y + i * p, x + (i + 1) * p, y + (i + 1) * p,
                                   fill=cor, outline="", tags=tags)
            t.create_rectangle(x + i * p, y + 15 * p, x + (i + 1) * p, y + 16 * p,
                               fill=misturar("#05070a", cor, 0.4), outline="", tags=tags)

    # ========================================================
    # animacao: pontos correndo pelos fios ativos
    # ========================================================
    def _criar_particulas(self, pts):
        comp = sum(abs(bx - ax) + abs(by - ay) for (ax, ay), (bx, by) in zip(pts, pts[1:]))
        if comp < 4:
            return
        r = max(2.0, 3.2 * self.zoom)
        espaco = max(40.0, 90 * self.zoom)
        n = max(1, int(comp / espaco))
        for k in range(n):
            item = self.tela.create_oval(0, 0, 0, 0, fill="#ffffff", outline="")
            self.particulas.append([item, pts, comp, comp * k / n, r])

    def _ponto_em(self, pts, pos):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            d = abs(bx - ax) + abs(by - ay)
            if pos <= d and d > 0:
                f = pos / d
                return ax + (bx - ax) * f, ay + (by - ay) * f
            pos -= d
        return pts[-1]

    def _animar(self):
        vel = max(1.5, 2.6 * self.zoom)
        for p in self.particulas:
            item, pts, comp, pos, r = p
            pos = (pos + vel) % comp
            p[3] = pos
            x, y = self._ponto_em(pts, pos)
            self.tela.coords(item, x - r, y - r, x + r, y + r)
        self.raiz.after(30, self._animar)


def main():
    try:                                     # nitidez em telas com escala (Windows)
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    raiz = tk.Tk()
    Esquema(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
