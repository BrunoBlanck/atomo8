# -*- coding: utf-8 -*-
"""
VISUALIZADOR EM NIVEL DE PORTAS

Abre uma janela com o circuito de um componente desenhado com portas
logicas (circuitos em portas.py). Nao tem ligacao com a simulacao dos
programas: clique nas chaves (entradas) para mudar 0/1 e veja os fios e
os LEDs (saidas) mudarem. Blocos com ↗ abrem o circuito de dentro.

Layout automatico:
  - colunas = profundidade logica (quantas portas desde as entradas);
  - linhas  = alinhadas com as portas que alimentam cada uma;
  - fios ortogonais: cada fio tem a sua trilha vertical entre colunas e a
    sua trilha horizontal nos canais entre linhas (nunca passam por cima
    de uma porta e nunca se sobrepoem).
"""

import math
import os
import tkinter as tk
import tkinter.font as tkfont

import portas

FUNDO = "#0d1117"
PAINEL = "#131a24"
PAINEL_BORDA = "#232c3a"
TEXTO = "#e6edf3"
TEXTO_SUAVE = "#8b98a9"
FIO_0 = "#3a4658"
FIO_1 = "#7ee0ff"
LIGADO = "#2ed39a"
LED_1 = "#ffd166"

COR_TIPO = {"AND": "#4f8cff", "NAND": "#4f8cff", "OR": "#b07cff", "NOR": "#b07cff",
            "XOR": "#22c3d6", "NOT": "#ffd166", "ff": "#2ed39a", "latch": "#2ed39a",
            "bloco": "#ff9f43"}

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def misturar(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("{:02x}".format(int(x + (y - x) * t)) for x, y in zip(a, b))


# ============================================================
# LAYOUT
# ============================================================

class Layout:
    TRILHA_X = 11          # distancia entre trilhas verticais
    TRILHA_Y = 9           # distancia entre trilhas horizontais

    def __init__(self, c):
        self.c = c
        self.nos = [n for n in c.nos if n["tipo"] != "fio"]
        self.por_id = {n["id"]: n for n in self.nos}
        self._arestas()
        self._colunas()
        self._tamanhos()
        self._linhas()
        self._rotas()
        self._posicoes()

    # ---------------- grafo
    def _arestas(self):
        self.arestas = []                 # (src_id, src_k, dst_id, dst_k)
        for n in self.nos:
            for k, ref in enumerate(n["ins"]):
                s = self.c.resolver(ref)
                self.arestas.append((s[0], s[1], n["id"], k))
        self.entram = {n["id"]: [] for n in self.nos}
        self.saem = {n["id"]: [] for n in self.nos}
        for a in self.arestas:
            self.entram[a[2]].append(a)
            self.saem[a[0]].append(a)

    def _colunas(self):
        fontes = [n["id"] for n in self.nos if n["tipo"] in ("in", "const")]
        # arestas de volta (realimentacao) por busca em profundidade
        volta, estado = set(), {}

        def visita(u):
            estado[u] = 1
            for a in self.saem[u]:
                v = a[2]
                if estado.get(v) == 1:
                    volta.add(a)
                elif v not in estado:
                    visita(v)
            estado[u] = 2

        import sys
        sys.setrecursionlimit(10000)
        for u in fontes + [n["id"] for n in self.nos]:
            if u not in estado:
                visita(u)
        self.volta = volta
        col = {u: 0 for u in fontes}
        mudou = True
        while mudou:
            mudou = False
            for n in self.nos:
                if n["tipo"] in ("in", "const", "out"):
                    continue
                ant = [col.get(a[0], 0) for a in self.entram[n["id"]] if a not in volta]
                novo = 1 + max(ant) if ant else 1
                if col.get(n["id"]) != novo:
                    col[n["id"]] = novo
                    mudou = True
        # constantes ficam logo antes de quem usam
        for n in self.nos:
            if n["tipo"] != "const":
                continue
            usos = [col.get(a[2], 1) for a in self.saem[n["id"]]
                    if self.por_id[a[2]]["tipo"] != "out"]
            col[n["id"]] = max(0, min(usos) - 1) if usos else 0
        # chaves (entradas) ficam logo antes do primeiro bloco que as usa
        for n in self.nos:
            if n["tipo"] != "in":
                continue
            usos = [col.get(a[2], 1) for a in self.saem[n["id"]]
                    if self.por_id[a[2]]["tipo"] != "out"]
            col[n["id"]] = max(0, min(usos) - 1) if usos else 0
        for n in self.nos:
            if "pos" in n and n["tipo"] != "out":
                col[n["id"]] = n["pos"][0]
        ultima = max([v for k, v in col.items()] + [0]) + 1
        for n in self.nos:
            if n["tipo"] == "out":
                col[n["id"]] = n["pos"][0] if "pos" in n else ultima
        self.col = col
        self.ncols = ultima + 1

    def _tamanhos(self):
        self.tam = {}
        for n in self.nos:
            t = n["tipo"]
            nin = len(n["ins"])
            if t in portas.PORTAS:
                self.tam[n["id"]] = (58, max(38, 15 * nin + 8))
            elif t == "bloco":
                ri, ro = self.c.rotulos_in(n), self.c.rotulos_out(n)
                largura = max(130, 7 * max([len(x) for x in ri + ro + [""]]) * 2 + 40,
                              8 * len(n["nome"]) + 30)
                self.tam[n["id"]] = (largura, 34 + 18 * max(len(ri), len(ro)))
            elif t in ("ff", "latch"):
                self.tam[n["id"]] = (96, 26 + 20 * max(2, nin))
            elif t == "in":
                self.tam[n["id"]] = (max(64, 8 * len(n["nome"]) + 34), 26)
            elif t == "const":
                self.tam[n["id"]] = (30, 22)
            elif t == "out":
                self.tam[n["id"]] = (max(60, 8 * len(n["nome"]) + 36), 26)

    def vao(self, u):
        """Quantas linhas o no ocupa (blocos e flip-flops altos ocupam mais)."""
        h = self.tam[u][1]
        return 1 + max(0, math.ceil((h - 40) / 58))

    def _linhas(self):
        colunas = [[] for _ in range(self.ncols)]
        for n in self.nos:
            colunas[self.col[n["id"]]].append(n["id"])
        fixo = {n["id"]: n["pos"][1] for n in self.nos if "pos" in n}
        row = dict(fixo)
        for lista in colunas:
            prox = 0
            for u in lista:
                if u not in row:
                    row[u] = prox
                prox = row[u] + self.vao(u)

        def desejo(u):
            viz = [row[a[0]] for a in self.entram[u] if a not in self.volta]
            if self.por_id[u]["tipo"] in ("in", "const") or not viz:
                viz += [row[a[2]] for a in self.saem[u]]
            return sum(viz) / len(viz) if viz else row[u]

        for _ in range(6):
            for lista in colunas:
                ocupado = set()
                for u in lista:
                    if u in fixo:
                        ocupado.update(range(fixo[u], fixo[u] + self.vao(u)))
                for u in sorted((u for u in lista if u not in fixo),
                                key=lambda u: (desejo(u), u)):
                    r = max(0, int(round(desejo(u))))
                    while any(x in ocupado for x in range(r, r + self.vao(u))):
                        r += 1
                    row[u] = r
                    ocupado.update(range(r, r + self.vao(u)))
        menor = min(row.values()) if row else 0
        self.row = {u: r - menor for u, r in row.items()}
        self.nrows = max(r + self.vao(u) for u, r in self.row.items()) if row else 1
        # canais (entre linhas) cobertos por nos altos, por coluna
        self.bloqueado = set()
        for u, r in self.row.items():
            for k in range(r, r + self.vao(u) - 1):
                self.bloqueado.add((self.col[u], k))

    # ---------------- pinos (relativos ao centro)
    def pino_in(self, u, k):
        n = self.por_id[u]
        w, h = self.tam[u]
        t = n["tipo"]
        if t in portas.PORTAS:
            nin = len(n["ins"])
            return (-w / 2, -h / 2 + h * (k + 0.5) / nin)
        if t == "bloco":
            return (-w / 2, -h / 2 + 30 + 18 * k)
        if t in ("ff", "latch"):
            return (-w / 2, -h / 2 + 20 + 20 * k)
        return (-w / 2, 0)

    def pino_out(self, u, k):
        n = self.por_id[u]
        w, h = self.tam[u]
        if n["tipo"] == "bloco":
            return (w / 2, -h / 2 + 30 + 18 * k)
        if n["tipo"] in ("ff", "latch"):
            return (w / 2, -h / 2 + 20)
        if n["tipo"] == "NOT":
            return (w / 2, 0)
        return (w / 2, 0)

    # ---------------- rotas (trilhas)
    def _rotas(self):
        self.trilha_v = {}         # (gap, rede) -> indice
        self.trilha_h = {}         # (canal, rede) -> indice
        self.uso_v = {}
        self.uso_h = {}
        self.planos = []           # (aresta, tipo, gaps/canal)
        for a in self.arestas:
            s, sk, d, dk = a
            rede = (s, sk)
            cs, cd = self.col[s], self.col[d]
            if cd == cs + 1:
                g = cs
                self._trilha(self.trilha_v, self.uso_v, g, rede)
                self.planos.append((a, "direto", g, None, None))
            else:
                g1, g2 = cs, cd - 1
                rs, rd = self.row[s], self.row[d]
                fim_s = rs + self.vao(s) - 1
                canal = fim_s if rd >= rs else rs - 1
                cols = range(min(cs, cd), max(cs, cd) + 1) if cd <= cs else range(cs + 1, cd)
                for desvio in (0, 1, -1, 2, -2, 3, -3, 4, -4, 6, -6):
                    k = canal + desvio
                    if k < -1 or k >= self.nrows:
                        continue
                    if not any((c, k) in self.bloqueado for c in cols):
                        canal = k
                        break
                self._trilha(self.trilha_v, self.uso_v, g1, rede)
                self._trilha(self.trilha_v, self.uso_v, g2, rede)
                self._trilha(self.trilha_h, self.uso_h, canal, rede)
                self.planos.append((a, "canal", g1, g2, canal))

    @staticmethod
    def _trilha(mapa, uso, chave, rede):
        if (chave, rede) not in mapa:
            mapa[(chave, rede)] = uso.get(chave, 0)
            uso[chave] = uso.get(chave, 0) + 1

    def _posicoes(self):
        m = 40
        larg_col = [0] * self.ncols
        for u, c in self.col.items():
            larg_col[c] = max(larg_col[c], self.tam[u][0])
        alt_lin = [40] * self.nrows
        for u, r in self.row.items():
            if self.vao(u) == 1:
                alt_lin[r] = max(alt_lin[r], self.tam[u][1])
        self.x_col = []
        x = m
        self.gap_x = {}
        for c in range(self.ncols):
            self.x_col.append(x)
            x += larg_col[c]
            n = self.uso_v.get(c, 0)
            gap = 34 + self.TRILHA_X * n
            self.gap_x[c] = x + 17
            x += gap
        self.largura = x + m
        topo_canal = self.uso_h.get(-1, 0)
        y = m + (14 + self.TRILHA_Y * topo_canal if topo_canal else 0)
        self.y_canal = {-1: m + 7}
        self.y_lin = []
        for r in range(self.nrows):
            self.y_lin.append(y)
            y += alt_lin[r]
            self.y_canal[r] = y + 9
            y += 18 + self.TRILHA_Y * self.uso_h.get(r, 0)
        self.altura = y + m
        self.centro = {}
        for u in self.col:
            c, r = self.col[u], self.row[u]
            if self.vao(u) == 1:
                cy = self.y_lin[r] + alt_lin[r] / 2
            else:
                cy = self.y_lin[r] + self.tam[u][1] / 2
            self.centro[u] = (self.x_col[c] + larg_col[c] / 2, cy)
        # pontos de cada fio
        self.fios = []             # (rede, [pontos])
        for a, tipo, g1, g2, canal in self.planos:
            s, sk, d, dk = a
            rede = (s, sk)
            cx, cy = self.centro[s]
            px, py = self.pino_out(s, sk)
            sx, sy = cx + px, cy + py
            cx, cy = self.centro[d]
            px, py = self.pino_in(d, dk)
            tx, ty = cx + px, cy + py
            x1 = self.gap_x[g1] + self.TRILHA_X * self.trilha_v[(g1, rede)]
            if tipo == "direto":
                pts = [(sx, sy), (x1, sy), (x1, ty), (tx, ty)]
            else:
                x2 = self.gap_x[g2] + self.TRILHA_X * self.trilha_v[(g2, rede)]
                yc = self.y_canal[canal] + self.TRILHA_Y * self.trilha_h[(canal, rede)]
                pts = [(sx, sy), (x1, sy), (x1, yc), (x2, yc), (x2, ty), (tx, ty)]
            self.fios.append((rede, pts))


# ============================================================
# JANELA
# ============================================================

class VisorPortas:

    def __init__(self, mestre, vista, fontes=None):
        self.win = tk.Toplevel(mestre)
        self.win.configure(bg=FUNDO)
        self.win.geometry("1400x860")
        self.win.minsize(900, 600)
        familias = set(tkfont.families())
        self.f_base = "Segoe UI" if "Segoe UI" in familias else "Helvetica"
        self.f_mono = "Cascadia Mono" if "Cascadia Mono" in familias else (
            "Consolas" if "Consolas" in familias else "Courier")
        self.pilha = []
        self.zoom, self.ox, self.oy = 1.0, 0.0, 0.0
        self.arrasto = None
        self._montar()
        self.abrir(vista)

    # ---------------- interface
    def _botao(self, pai, texto, acao):
        b = tk.Label(pai, text=texto, bg=PAINEL, fg=TEXTO, padx=12, pady=5,
                     font=(self.f_base, 9), cursor="hand2",
                     highlightthickness=1, highlightbackground=PAINEL_BORDA)
        b.bind("<Button-1>", lambda e: acao())
        b.bind("<Enter>", lambda e: b.configure(bg="#1c2533"))
        b.bind("<Leave>", lambda e: b.configure(bg=PAINEL))
        return b

    def _montar(self):
        topo = tk.Frame(self.win, bg=FUNDO)
        topo.pack(side="top", fill="x")
        self.bt_voltar = self._botao(topo, "←  Voltar", self.voltar)
        self.bt_voltar.pack(side="left", padx=(16, 8), pady=12)
        self.lb_caminho = tk.Label(topo, text="", bg=FUNDO, fg=TEXTO_SUAVE,
                                   font=(self.f_base, 10))
        self.lb_caminho.pack(side="left", pady=12)
        self._botao(topo, "Ajustar  F", self.ajustar).pack(side="right", padx=(6, 16))
        self._botao(topo, "Zerar entradas", self.zerar).pack(side="right", padx=6)
        self.bt_clk = self._botao(topo, "⏵  Pulso de CLK", self.pulso_clk)

        corpo = tk.Frame(self.win, bg=FUNDO)
        corpo.pack(side="top", fill="both", expand=True)
        lado = tk.Frame(corpo, bg=PAINEL, width=360, highlightthickness=1,
                        highlightbackground=PAINEL_BORDA)
        lado.pack(side="right", fill="y")
        lado.pack_propagate(False)
        self.tela = tk.Canvas(corpo, bg=FUNDO, highlightthickness=0)
        self.tela.pack(side="left", fill="both", expand=True)

        self.lb_chip = tk.Label(lado, text="PORTAS LÓGICAS", bg=LIGADO, fg=FUNDO,
                                font=(self.f_base, 8, "bold"), padx=8, pady=2)
        self.lb_chip.pack(side="top", anchor="w", padx=20, pady=(20, 0))
        self.lb_titulo = tk.Label(lado, text="", bg=PAINEL, fg=TEXTO, wraplength=320,
                                  justify="left", font=(self.f_base, 16, "bold"))
        self.lb_titulo.pack(side="top", anchor="w", padx=20, pady=(8, 0))
        self.lb_arq = tk.Label(lado, text="", bg=PAINEL, fg=TEXTO_SUAVE,
                               font=(self.f_mono, 9))
        self.lb_arq.pack(side="top", anchor="w", padx=20)
        self.bt_doc = self._botao(lado, "Abrir documento  ↗", self.abrir_documento)
        self.bt_doc.pack(side="top", anchor="w", padx=20, pady=(10, 4))
        self.texto = tk.Text(lado, bg=PAINEL, fg=TEXTO, relief="flat", wrap="word",
                             font=(self.f_base, 10), padx=20, pady=8, cursor="arrow",
                             highlightthickness=0, borderwidth=0, spacing3=3)
        self.texto.pack(side="top", fill="both", expand=True)
        self.texto.tag_configure("h", font=(self.f_base, 8, "bold"),
                                 foreground=TEXTO_SUAVE, spacing1=12)
        self.texto.tag_configure("mono", font=(self.f_mono, 9), foreground="#c9d6e3")
        self.texto.tag_configure("suave", foreground=TEXTO_SUAVE)

        t = self.tela
        t.bind("<Configure>", lambda e: self.desenhar())
        t.bind("<ButtonPress-1>", self._apertou)
        t.bind("<B1-Motion>", self._arrastou)
        t.bind("<ButtonRelease-1>", lambda e: setattr(self, "arrasto", None))
        t.bind("<MouseWheel>", lambda e: self._zoom_em(e.x, e.y, 1.12 if e.delta > 0 else 1 / 1.12))
        t.bind("<Button-4>", lambda e: self._zoom_em(e.x, e.y, 1.12))
        t.bind("<Button-5>", lambda e: self._zoom_em(e.x, e.y, 1 / 1.12))
        t.bind("<Motion>", self._moveu)
        self.win.bind("<KeyPress-f>", lambda e: self.ajustar())
        self.win.bind("<Escape>", lambda e: self.voltar())

    # ---------------- navegacao
    def abrir(self, vista):
        c = portas.VISTAS[vista]()
        self.pilha.append((vista, c))
        self._mostrar()

    def voltar(self):
        if len(self.pilha) > 1:
            self.pilha.pop()
            self._mostrar()

    def _mostrar(self):
        vista, c = self.pilha[-1]
        self.c = c
        c.avaliar()
        self.lay = Layout(c)
        self.win.title("Portas lógicas · " + c.titulo)
        self.lb_caminho.configure(text="  ›  ".join(x[1].titulo for x in self.pilha))
        self.bt_voltar.configure(fg=TEXTO if len(self.pilha) > 1 else PAINEL_BORDA)
        tem_clk = any(c.nos[i]["nome"] == "CLK" for i in c.entradas)
        if tem_clk:
            if not self.bt_clk.winfo_ismapped():
                self.bt_clk.pack(side="right", padx=6)
        else:
            self.bt_clk.pack_forget()
        self.lb_titulo.configure(text=c.titulo)
        self.lb_arq.configure(text="componentes/" + c.arquivo if c.arquivo else "")
        self._escrever_lateral()
        self.win.after(30, self.ajustar)

    def _escrever_lateral(self):
        c = self.c
        tx = self.texto
        tx.configure(state="normal")
        tx.delete("1.0", "end")
        tx.insert("end", c.descricao + "\n")
        if c.nota:
            tx.insert("end", "\n" + c.nota + "\n", "suave")
        p, ffs, latches = c.contar()
        tx.insert("end", "CONTAGEM\n", "h")
        nomes = {1: "", 2: "", 3: " de 3 entradas", 4: " de 4 entradas"}
        total = 0
        for (tipo, n), q in sorted(p.items()):
            tx.insert("end", "{:>3} × {}{}\n".format(
                q, tipo, nomes.get(n, " de {} entradas".format(n))), "mono")
            total += q
        tx.insert("end", "{:>3}   portas no total\n".format(total), "mono")
        if ffs:
            tx.insert("end", "{:>3} × flip-flop D (8 NAND + 1 NOT cada)\n".format(ffs), "mono")
        if latches:
            tx.insert("end", "{:>3} × latch D (4 NAND cada)\n".format(latches), "mono")
        tx.insert("end", "COMO USAR\n", "h")
        tx.insert("end", "•  Clique numa chave (entrada) para trocar 0 ↔ 1.\n"
                         "•  Fio aceso = 1 · fio apagado = 0 · LED aceso = saída em 1.\n"
                         "•  Blocos com ↗, flip-flops e latches abrem o circuito "
                         "de dentro.\n", "suave")
        if any(n["tipo"] == "ff" for n in c.nos):
            tx.insert("end", "•  Flip-flops gravam D quando o CLK vai de 0 para 1 "
                             "(chave CLK ou botão Pulso de CLK).\n", "suave")
        tx.insert("end", "•  Roda do mouse: zoom · arrastar: mover · F: ajustar · "
                         "Esc: voltar.\n", "suave")
        tx.configure(state="disabled")

    def abrir_documento(self):
        arq = self.c.arquivo
        caminho = os.path.join(RAIZ, "componentes", arq)
        if arq and os.path.exists(caminho):
            try:
                os.startfile(caminho)
            except AttributeError:
                import webbrowser
                webbrowser.open("file://" + caminho)

    # ---------------- interacao
    def _alvo(self):
        for tag in self.tela.gettags("current"):
            if ":" in tag:
                tipo, ident = tag.split(":", 1)
                if tipo in ("chave", "abre"):
                    return tipo, int(ident)
        return None

    def _apertou(self, e):
        alvo = self._alvo()
        if alvo is None:
            self.arrasto = (e.x, e.y, self.ox, self.oy)
            return
        tipo, u = alvo
        no = self.c.nos[u]
        if tipo == "chave":
            no["valor"] ^= 1
            self.c.avaliar()
            self.desenhar()
        else:
            if no["tipo"] == "bloco":
                self.abrir(no["vista"])
            elif no["tipo"] == "ff":
                self.abrir("ffd")
            elif no["tipo"] == "latch":
                self.abrir("latch")

    def _arrastou(self, e):
        if self.arrasto:
            x0, y0, ox, oy = self.arrasto
            self.ox, self.oy = ox + e.x - x0, oy + e.y - y0
            self.desenhar()

    def _moveu(self, e):
        self.tela.configure(cursor="hand2" if self._alvo() else "arrow")

    def zerar(self):
        for i in self.c.entradas:
            self.c.nos[i]["valor"] = 1 if self.c.nos[i]["nome"].startswith("/") else 0
        self.c.avaliar()
        self.desenhar()

    def pulso_clk(self):
        clk = [i for i in self.c.entradas if self.c.nos[i]["nome"] == "CLK"]
        for valor in (0, 1):
            for i in clk:
                self.c.nos[i]["valor"] = valor
            self.c.avaliar()
        self.desenhar()
        self.win.after(250, self._clk_baixa)

    def _clk_baixa(self):
        for i in self.c.entradas:
            if self.c.nos[i]["nome"] == "CLK":
                self.c.nos[i]["valor"] = 0
        self.c.avaliar()
        self.desenhar()

    # ---------------- zoom
    def ajustar(self):
        w, h = self.tela.winfo_width(), self.tela.winfo_height()
        if w < 200 or h < 200:                # janela ainda sem tamanho
            self.win.after(60, self.ajustar)
            return
        L = self.lay
        self.zoom = min(1.6, (w - 40) / L.largura, (h - 40) / L.altura)
        self.ox = (w - L.largura * self.zoom) / 2
        self.oy = (h - L.altura * self.zoom) / 2
        self.desenhar()

    def _zoom_em(self, mx, my, f):
        novo = max(0.2, min(4.0, self.zoom * f))
        f = novo / self.zoom
        self.ox = mx - (mx - self.ox) * f
        self.oy = my - (my - self.oy) * f
        self.zoom = novo
        self.desenhar()

    def T(self, x, y):
        return x * self.zoom + self.ox, y * self.zoom + self.oy

    # ---------------- desenho
    def desenhar(self):
        if not hasattr(self, "lay"):
            return
        t = self.tela
        t.delete("all")
        L, c, z = self.lay, self.c, self.zoom
        # fios (valor da rede = saida da origem)
        juncoes = {}
        for rede, pts in L.fios:
            v = c.vals.get(rede, 0)
            plano = [q for p in pts for q in self.T(*p)]
            t.create_line(*plano, fill=FIO_1 if v else FIO_0,
                          width=max(1.2, (2.4 if v else 1.6) * z), capstyle="round",
                          joinstyle="round")
            for p in pts[1:-1]:
                chave = (rede, round(p[0]), round(p[1]))
                juncoes[chave] = juncoes.get(chave, 0) + 1
        # pontos de juncao (onde a mesma rede se divide)
        contagem = {}
        for (rede, x, y), q in juncoes.items():
            contagem.setdefault(rede, {})[(x, y)] = q
        for rede, pontos in contagem.items():
            if sum(1 for a in L.fios if a[0] == rede) < 2:
                continue
            v = c.vals.get(rede, 0)
            for (x, y), q in pontos.items():
                if q >= 1 and self._ponto_compartilhado(rede, x, y):
                    X, Y = self.T(x, y)
                    r = max(2.0, 3.2 * z)
                    t.create_oval(X - r, Y - r, X + r, Y + r, fill=FIO_1 if v else FIO_0,
                                  outline="")
        for n in L.nos:
            self._desenhar_no(n)

    def _ponto_compartilhado(self, rede, x, y):
        """Juncao de verdade: o ponto esta no meio de um segmento de outro fio da rede."""
        vezes = 0
        for r, pts in self.lay.fios:
            if r != rede:
                continue
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if (min(ax, bx) - 0.5 <= x <= max(ax, bx) + 0.5 and
                        min(ay, by) - 0.5 <= y <= max(ay, by) + 0.5):
                    vezes += 1
                    break
        return vezes >= 2

    def _texto(self, x, y, s, tam=9, cor=TEXTO, negrito=False, mono=False, anchor="center",
               tags=()):
        z = self.zoom
        if tam * z < 3.2:
            return
        fam = self.f_mono if mono else self.f_base
        self.tela.create_text(x, y, text=s, fill=cor, anchor=anchor, tags=tags,
                              font=(fam, max(5, int(round(tam * z))), "bold" if negrito else "normal"))

    def _desenhar_no(self, n):
        L, c, t, z = self.lay, self.c, self.tela, self.zoom
        u = n["id"]
        cx, cy = L.centro[u]
        w, h = L.tam[u]
        X0, Y0 = self.T(cx - w / 2, cy - h / 2)
        X1, Y1 = self.T(cx + w / 2, cy + h / 2)
        tipo = n["tipo"]
        if tipo == "in":
            v = n["valor"]
            tags = ("chave:{}".format(u),)
            self._ret(X0, Y0, X1, Y1, 6 * z, fill=misturar(FUNDO, LIGADO, 0.25 if v else 0.06),
                      outline=LIGADO if v else PAINEL_BORDA, width=1.4, tags=tags)
            self._texto(X0 + 8 * z, (Y0 + Y1) / 2, n["nome"], 9, TEXTO, True, anchor="w", tags=tags)
            self._texto(X1 - 10 * z, (Y0 + Y1) / 2, str(v), 10, LIGADO if v else TEXTO_SUAVE,
                        True, True, tags=tags)
        elif tipo == "const":
            v = n["valor"]
            self._ret(X0, Y0, X1, Y1, 4 * z, fill=PAINEL, outline=PAINEL_BORDA)
            self._texto((X0 + X1) / 2, (Y0 + Y1) / 2, str(v), 9, TEXTO_SUAVE, True, True)
        elif tipo == "out":
            v = c.valor(n["ins"][0])
            r = 8 * z
            lx = X0 + 6 * z + r
            t.create_oval(lx - r - 3 * z, (Y0 + Y1) / 2 - r - 3 * z, lx + r + 3 * z,
                          (Y0 + Y1) / 2 + r + 3 * z, fill=misturar(FUNDO, LED_1, 0.25) if v
                          else FUNDO, outline="")
            t.create_oval(lx - r, (Y0 + Y1) / 2 - r, lx + r, (Y0 + Y1) / 2 + r,
                          fill=LED_1 if v else "#2a2f38", outline=misturar(FUNDO, LED_1, 0.6))
            self._texto(lx + r + 6 * z, (Y0 + Y1) / 2, "{}  {}".format(n["nome"], v), 9,
                        LED_1 if v else TEXTO_SUAVE, True, anchor="w")
        elif tipo in portas.PORTAS:
            if tipo in ("OR", "NOR", "XOR"):     # fio ate a curva das costas
                for k, ref in enumerate(n["ins"]):
                    px, py = L.pino_in(u, k)
                    X, Y = self.T(cx + px, cy + py)
                    s_ = (Y1 - Y) / max(1, (Y1 - Y0))
                    xr = X1
                    Xc = X0 + 0.18 * (xr - X0) * math.sin(math.pi * s_)
                    v = c.valor(ref)
                    t.create_line(X, Y, Xc + 1, Y, fill=FIO_1 if v else FIO_0,
                                  width=max(1.2, (2.4 if v else 1.6) * z))
            self._porta(tipo, X0, Y0, X1, Y1, c.vals.get((u, 0), 0))
        elif tipo == "bloco":
            tags = ("abre:{}".format(u),)
            cor = COR_TIPO["bloco"]
            self._ret(X0, Y0, X1, Y1, 10 * z, fill=misturar(FUNDO, cor, 0.12), outline=cor,
                      width=1.6, tags=tags)
            self._texto((X0 + X1) / 2, Y0 + 14 * z, n["nome"] + "  ↗", 9, TEXTO, True, tags=tags)
            for k, nome in enumerate(c.rotulos_in(n)):
                px, py = L.pino_in(u, k)
                X, Y = self.T(cx + px, cy + py)
                self._texto(X + 6 * z, Y, nome, 8, TEXTO_SUAVE, anchor="w", mono=True, tags=tags)
            for k, nome in enumerate(c.rotulos_out(n)):
                px, py = L.pino_out(u, k)
                X, Y = self.T(cx + px, cy + py)
                self._texto(X - 6 * z, Y, nome, 8, TEXTO_SUAVE, anchor="e", mono=True, tags=tags)
        elif tipo in ("ff", "latch"):
            tags = ("abre:{}".format(u),)
            cor = COR_TIPO[tipo]
            self._ret(X0, Y0, X1, Y1, 6 * z, fill=misturar(FUNDO, cor, 0.12), outline=cor,
                      width=1.6, tags=tags)
            self._texto((X0 + X1) / 2, Y1 - 10 * z, n["nome"] + " ↗", 8, TEXTO, True, tags=tags)
            for k, nome in enumerate(c.rotulos_in(n)):
                px, py = L.pino_in(u, k)
                X, Y = self.T(cx + px, cy + py)
                if nome == "CLK":         # triangulo do relogio
                    t.create_line(X, Y - 5 * z, X + 7 * z, Y, X, Y + 5 * z, fill=cor,
                                  width=max(1, 1.4 * z), tags=tags)
                    self._texto(X + 10 * z, Y, "CLK", 7, TEXTO_SUAVE, anchor="w", mono=True, tags=tags)
                else:
                    self._texto(X + 6 * z, Y, nome, 8, TEXTO_SUAVE, anchor="w", mono=True, tags=tags)
            px, py = L.pino_out(u, 0)
            X, Y = self.T(cx + px, cy + py)
            q = c.vals.get((u, 0), 0)
            self._texto(X - 6 * z, Y, "Q", 8, TEXTO_SUAVE, anchor="e", mono=True, tags=tags)
            self._texto((X0 + X1) / 2, (Y0 + Y1) / 2 - 2 * z, str(q), 13,
                        FIO_1 if q else TEXTO_SUAVE, True, True, tags=tags)

    def _ret(self, x0, y0, x1, y1, r, **kw):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
               x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.tela.create_polygon(pts, smooth=True, **kw)

    def _porta(self, tipo, x0, y0, x1, y1, saida):
        """Simbolo da porta dentro do retangulo (x0,y0)-(x1,y1)."""
        t, z = self.tela, self.zoom
        cor = COR_TIPO[tipo]
        corpo = misturar(FUNDO, cor, 0.16)
        borda = cor
        lw = max(1.0, 1.6 * z)
        bolha = tipo in ("NAND", "NOR", "NOT")
        rb = 4 * z
        xr = x1 - (2 * rb if bolha else 0)          # onde termina o corpo
        ym = (y0 + y1) / 2
        h = y1 - y0
        if tipo in ("AND", "NAND"):
            xm = x0 + (xr - x0) * 0.45
            pts = [(x0, y0), (xm, y0)]
            for i in range(1, 16):
                a = -math.pi / 2 + math.pi * i / 16
                pts.append((xm + (xr - xm) * math.cos(a), ym + h / 2 * math.sin(a)))
            pts += [(xm, y1), (x0, y1)]
        elif tipo in ("OR", "NOR", "XOR"):
            pts = []
            n = 14
            for i in range(n + 1):                     # frente de cima
                s = i / n
                pts.append((x0 + (xr - x0) * s, y0 + (ym - y0) * s ** 2.2))
            for i in range(1, n + 1):                  # frente de baixo
                s = 1 - i / n
                pts.append((x0 + (xr - x0) * s, y1 - (y1 - ym) * s ** 2.2))
            for i in range(1, n):                      # costas (curva para dentro)
                s = i / n
                yy = y1 - h * s
                pts.append((x0 + 0.18 * (xr - x0) * math.sin(math.pi * s), yy))
        else:                                          # NOT: triangulo
            pts = [(x0, y0), (xr, ym), (x0, y1)]
        plano = [q for p in pts for q in p]
        t.create_polygon(*plano, fill=corpo, outline=borda, width=lw)
        if tipo == "XOR":                              # segunda curva das costas
            antes = []
            for i in range(0, 15):
                s = i / 14
                antes.append((x0 - 6 * z + 0.18 * (xr - x0) * math.sin(math.pi * s), y1 - h * s))
            t.create_line(*[q for p in antes for q in p], fill=borda, width=lw, smooth=True)
        if bolha:
            t.create_oval(xr, ym - rb, xr + 2 * rb, ym + rb, fill=FUNDO, outline=borda, width=lw)
        # nome pequeno dentro
        rot = {"AND": "AND", "NAND": "NAND", "OR": "OR", "NOR": "NOR", "XOR": "XOR", "NOT": ""}[tipo]
        if rot:
            self._texto(x0 + (xr - x0) * 0.42, ym, rot, 7, misturar(cor, TEXTO, 0.5), True)
        # saida acesa
        if saida:
            t.create_oval(x1 - 2 * z, ym - 2 * z, x1 + 2 * z, ym + 2 * z, fill=FIO_1, outline="")


def abrir(mestre, vista):
    return VisorPortas(mestre, vista)
