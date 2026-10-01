# -*- coding: utf-8 -*-
"""
CIRCUITOS EM NIVEL DE PORTAS (para o visualizador de portas)

Cada componente do hardware descrito so com portas (AND, OR, NOT, XOR,
NAND, NOR), flip-flops D e latches D. Blocos repetidos aparecem como
"bloco" que abre o proprio circuito por dentro.

Nao tem ligacao com a simulacao dos programas: cada circuito avalia
sozinho, com chaves nas entradas e LEDs nas saidas, igual ao teste de
protoboard descrito em componentes/*.md.
"""

from collections import Counter

PORTAS = ("AND", "OR", "NOT", "XOR", "NAND", "NOR")


# ============================================================
# CIRCUITO (netlist + avaliacao)
# ============================================================

class Circuito:

    def __init__(self, titulo, arquivo="", descricao="", nota=""):
        self.titulo = titulo
        self.arquivo = arquivo
        self.descricao = descricao
        self.nota = nota
        self.nos = []
        self.entradas = []          # ids dos nos de entrada (na ordem)
        self.saidas = []            # ids dos nos de saida (na ordem)
        self.vals = {}

    # ---------------- construcao
    def _no(self, tipo, ins=(), nome="", nout=1, **extra):
        no = dict(id=len(self.nos), tipo=tipo, ins=list(ins), nome=nome, nout=nout)
        no.update(extra)
        self.nos.append(no)
        return no["id"]

    def entrada(self, nome, valor=0):
        i = self._no("in", nome=nome, valor=valor)
        self.entradas.append(i)
        return (i, 0)

    def const(self, valor):
        return (self._no("const", nome=str(valor), valor=valor), 0)

    def porta(self, tipo, *ins):
        return (self._no(tipo, ins), 0)

    def and_(self, *ins): return self.porta("AND", *ins)
    def or_(self, *ins): return self.porta("OR", *ins)
    def not_(self, a): return self.porta("NOT", a)
    def xor(self, a, b): return self.porta("XOR", a, b)
    def nand(self, *ins): return self.porta("NAND", *ins)
    def nor(self, *ins): return self.porta("NOR", *ins)

    def ou_arvore(self, refs):
        """OR de varias entradas feito com OR de 2 entradas em arvore."""
        refs = list(refs)
        while len(refs) > 1:
            novo = [self.or_(refs[i], refs[i + 1]) for i in range(0, len(refs) - 1, 2)]
            if len(refs) % 2:
                novo.append(refs[-1])
            refs = novo
        return refs[0]

    def mux2(self, s, d0, d1, ns=None):
        """Mux 2x1 de 1 bit (arquivo 05): (D0 AND /S) OR (D1 AND S)."""
        ns = ns or self.not_(s)
        return self.or_(self.and_(d0, ns), self.and_(d1, s))

    def adiante(self):
        """Fio que sera ligado depois (realimentacao, ex.: Q de um flip-flop)."""
        return (self._no("fio"), 0)

    def ligar(self, fio, ref):
        self.nos[fio[0]]["ins"] = [ref]

    def ff(self, d, clk, clr=None, nome="FF D"):
        ins = [d, clk] + ([clr] if clr else [])
        return (self._no("ff", ins, nome=nome, estado=0, clk_ant=0), 0)

    def latch(self, d, en, nome="LATCH D"):
        return (self._no("latch", [d, en], nome=nome, estado=0), 0)

    def bloco(self, vista, *ins, nome=None):
        sub = VISTAS[vista]()
        if len(ins) != len(sub.entradas):
            raise ValueError("bloco {}: {} entradas, recebeu {}".format(
                vista, len(sub.entradas), len(ins)))
        i = self._no("bloco", ins, nome=nome or sub.titulo, nout=len(sub.saidas),
                     vista=vista, sub=sub)
        refs = [(i, k) for k in range(len(sub.saidas))]
        return refs if len(refs) > 1 else refs[0]

    def saida(self, nome, ref, pos=None):
        i = self._no("out", [ref], nome=nome)
        if pos:
            self.nos[i]["pos"] = pos
        self.saidas.append(i)
        return i

    def pos(self, ref, col, lin):
        """Posicao fixa no desenho (coluna, linha); o resto e automatico."""
        self.nos[ref[0]]["pos"] = (col, lin)
        return ref

    # ---------------- leitura
    def resolver(self, ref):
        while self.nos[ref[0]]["tipo"] == "fio":
            ref = self.nos[ref[0]]["ins"][0]
        return ref

    def rotulos_in(self, no):
        if no["tipo"] == "bloco":
            return [no["sub"].nos[i]["nome"] for i in no["sub"].entradas]
        if no["tipo"] == "ff":
            return ["D", "CLK", "CLR"][:len(no["ins"])]
        if no["tipo"] == "latch":
            return ["D", "EN"]
        return [""] * len(no["ins"])

    def rotulos_out(self, no):
        if no["tipo"] == "bloco":
            return [no["sub"].nos[i]["nome"] for i in no["sub"].saidas]
        if no["tipo"] in ("ff", "latch"):
            return ["Q"]
        return [""]

    # ---------------- avaliacao
    def valor(self, ref):
        return self.vals.get(self.resolver(ref), 0)

    def _calcula(self, no):
        v = [self.valor(r) for r in no["ins"]]
        t = no["tipo"]
        if t in ("in", "const"):
            return [no["valor"]]
        if t == "AND":
            return [int(all(v))]
        if t == "OR":
            return [int(any(v))]
        if t == "NOT":
            return [1 - v[0]]
        if t == "XOR":
            return [v[0] ^ v[1]]
        if t == "NAND":
            return [1 - int(all(v))]
        if t == "NOR":
            return [1 - int(any(v))]
        if t == "ff":
            if len(v) > 2 and v[2] == 0:          # /CLR ativo em 0
                no["estado"] = 0
            return [no["estado"]]
        if t == "latch":
            if v[1]:
                no["estado"] = v[0]
            return [no["estado"]]
        if t == "bloco":
            sub = no["sub"]
            for i, val in zip(sub.entradas, v):
                sub.nos[i]["valor"] = val
            sub.avaliar()
            return [sub.valor(sub.nos[o]["ins"][0]) for o in sub.saidas]
        return [0]

    def _ponto_fixo(self):
        for _ in range(60):
            mudou = False
            for no in self.nos:
                if no["tipo"] in ("fio", "out"):
                    continue
                for k, val in enumerate(self._calcula(no)):
                    if self.vals.get((no["id"], k)) != val:
                        self.vals[(no["id"], k)] = val
                        mudou = True
            if not mudou:
                return

    def avaliar(self):
        self._ponto_fixo()
        # flip-flops: borda de subida do CLK grava D
        bordas = False
        for no in self.nos:
            if no["tipo"] != "ff":
                continue
            clk = self.valor(no["ins"][1])
            if clk and not no["clk_ant"]:
                limpa = len(no["ins"]) > 2 and self.valor(no["ins"][2]) == 0
                no["estado"] = 0 if limpa else self.valor(no["ins"][0])
                bordas = True
            no["clk_ant"] = clk
        if bordas:
            self._ponto_fixo()

    # ---------------- contagem
    def contar(self):
        """(Counter de portas por (tipo, entradas), flip-flops, latches)."""
        portas, ffs, latches = Counter(), 0, 0
        for no in self.nos:
            t = no["tipo"]
            if t in PORTAS:
                portas[(t, len(no["ins"]))] += 1
            elif t == "ff":
                ffs += 1
            elif t == "latch":
                latches += 1
            elif t == "bloco":
                p, f, l = no["sub"].contar()
                portas.update(p)
                ffs += f
                latches += l
        return portas, ffs, latches


# ============================================================
# CIRCUITOS BASICOS
# ============================================================

def v_fa():
    c = Circuito("Somador completo", "01-somador-completo.md",
                 "Soma 3 bits (A, B e o vai-um que chega) e devolve a soma S e o "
                 "vai-um COUT.")
    a, b, cin = c.entrada("A"), c.entrada("B"), c.entrada("CIN")
    x1 = c.xor(a, b)
    c.saida("S", c.xor(x1, cin))
    c.saida("COUT", c.or_(c.and_(a, b), c.and_(cin, x1)))
    return c


def v_soma8():
    c = Circuito("Somador 8 bits", "02-somador-8-bits.md",
                 "8 somadores completos em cadeia: o vai-um de cada bit entra no "
                 "próximo. É o caminho mais longo do hardware.")
    a = [c.entrada("A{}".format(i)) for i in range(8)]
    b = [c.entrada("B'{}".format(i)) for i in range(8)]
    vem = c.entrada("CIN")
    for i in range(8):
        s, vem = c.bloco("fa", a[i], b[i], vem, nome="Somador bit {}".format(i))
        c.saida("S{}".format(i), s)
    c.saida("COUT", vem)
    return c


def v_inv8():
    c = Circuito("Inversor de B", "03-inversor-controlado-8-bits.md",
                 "8 XOR: com SUB = 1 cada bit de B sai invertido (para subtrair); "
                 "com SUB = 0 passa igual.")
    sub = c.entrada("SUB")
    bs = [c.entrada("B{}".format(i)) for i in range(8)]
    for i in range(8):
        c.saida("B'{}".format(i), c.xor(bs[i], sub))
    return c


def v_logica():
    c = Circuito("Unidade lógica (1 bit)", "04-unidade-logica.md",
                 "Mux 4×1 montado ao contrário: An e Bn escolhem qual bit da "
                 "tabela-verdade T sai. Com T = 1000 é AND, 1110 OR, 0110 XOR, "
                 "1100 passa A, 0011 NOT A.",
                 "Repetido 8 vezes (um por bit) = 72 portas; T é o mesmo para todos.")
    an, bn = c.entrada("An"), c.entrada("Bn")
    t = [c.entrada("T{}".format(i)) for i in range(4)]
    na, nb = c.not_(an), c.not_(bn)
    termos = [c.and_(t[0], na, nb), c.and_(t[1], na, bn),
              c.and_(t[2], an, nb), c.and_(t[3], an, bn)]
    c.saida("Rn", c.ou_arvore(termos))
    return c


def _v_mux2(titulo, arquivo, s, d0, d1, y, descricao, nota=""):
    def criar():
        c = Circuito(titulo, arquivo, descricao, nota)
        sel = c.entrada(s)
        a = c.entrada(d0)
        b = c.entrada(d1)
        c.saida(y, c.mux2(sel, a, b))
        return c
    return criar


def _v_mux4(titulo, arquivo, s1, s0, ds, y, descricao, nota=""):
    def criar():
        c = Circuito(titulo, arquivo, descricao, nota)
        a1, a0 = c.entrada(s1), c.entrada(s0)
        dados = [c.const(0) if d == "0" else c.entrada(d) for d in ds]
        n1, n0 = c.not_(a1), c.not_(a0)
        linhas = [c.and_(n1, n0), c.and_(n1, a0), c.and_(a1, n0), c.and_(a1, a0)]
        termos = [c.and_(d, l) for d, l in zip(dados, linhas)]
        c.saida(y, c.ou_arvore(termos))
        return c
    return criar


def v_zero():
    c = Circuito("Detector de zero", "06-detector-de-zero.md",
                 "Z = NOR dos 8 bits: OR em árvore (3 níveis em vez de 7 em fila) "
                 "e um NOT no fim.")
    r = [c.entrada("R{}".format(i)) for i in range(8)]
    c.saida("Z", c.not_(c.ou_arvore(r)))
    return c


def v_cin():
    c = Circuito("Vai-um de entrada", "07-ula.md",
                 "CIN = (USA_C AND C) OR (NOT USA_C AND SUB). ADD: 0 · SUB: 1 · "
                 "ADC e SBC: a flag C.")
    sub, usa_c, flag = c.entrada("SUB"), c.entrada("USA_C"), c.entrada("C")
    c.saida("CIN", c.or_(c.and_(usa_c, flag), c.and_(c.not_(usa_c), sub)))
    return c


def v_shr():
    c = Circuito("SHR", "07-ula.md",
                 "Deslocar 1 bit para a direita é só fio: A7..A1 vão para R6..R0 e "
                 "R7 fica em 0. O bit que sai (A0) vira o C. Nenhuma porta.")
    a = [c.entrada("A{}".format(i)) for i in range(8)]
    for i in range(7):
        c.saida("R{}".format(i), a[i + 1])
    c.saida("R7", c.const(0))
    c.saida("C (A0)", a[0])
    return c


def v_ula():
    c = Circuito("ULA (1 bit + partes comuns)", "07-ula.md",
                 "Em cima, uma fatia de 1 bit da ULA: inversor de B (XOR), somador "
                 "completo, unidade lógica e o mux de resultado (soma, lógica, SHR). "
                 "Embaixo, as partes que existem uma vez só: o vai-um de entrada "
                 "(CIN) e o C novo.",
                 "A fatia se repete 8 vezes; o vai-um sai de um bit e entra no próximo. "
                 "Z sai do detector de zero (06) ligado nos 8 bits de R.")
    P = c.pos
    an = P(c.entrada("An"), 0, 0)
    bn = P(c.entrada("Bn"), 0, 2)
    sub = P(c.entrada("SUB"), 0, 3)
    vem = P(c.entrada("VEM (bit n−1)"), 1, 4)
    t = [P(c.entrada("T{}".format(i)), 1, 6 + i) for i in range(4)]
    shr = P(c.entrada("SHR"), 2, 11)
    logica = P(c.entrada("LOGICA"), 2, 12)
    a_cima = P(c.entrada("An+1 (SHR)"), 2, 13)
    zero = P(c.const(0), 2, 14)
    bx = P(c.xor(bn, sub), 1, 2)
    s, vai = c.bloco("fa", an, bx, vem, nome="Somador completo")
    P(s, 2, 1)
    ln = P(c.bloco("logica", an, bn, *t, nome="Unidade lógica"), 2, 5)
    rn = P(c.bloco("mux4", shr, logica, s, ln, a_cima, zero, nome="Mux de resultado"), 3, 9)
    c.saida("Rn", rn, pos=(4, 9))
    c.saida("VAI (bit n+1)", vai, pos=(4, 1))
    # partes comuns
    usa_c = P(c.entrada("USA_C"), 0, 15)
    flag = P(c.entrada("C atual"), 0, 16)
    nusa = P(c.not_(usa_c), 1, 17)
    cin = P(c.or_(P(c.and_(usa_c, flag), 2, 15), P(c.and_(nusa, sub), 2, 17)), 3, 16)
    c.saida("CIN (bit 0)", cin, pos=(4, 16))
    cout = P(c.entrada("COUT (bit 7)"), 0, 19)
    a0 = P(c.entrada("A0"), 0, 21)
    nshr = P(c.not_(shr), 1, 20)
    cn = P(c.or_(P(c.and_(cout, nshr), 2, 19), P(c.and_(a0, shr), 2, 21)), 3, 20)
    c.saida("C novo", cn, pos=(4, 20))
    return c

def v_latch():
    c = Circuito("Latch D", "16-ram.md",
                 "Guarda 1 bit enquanto EN = 0; com EN = 1 a saída segue D. "
                 "4 NAND: as duas da direita formam a trava (uma realimenta a outra).",
                 "É a célula de memória da RAM e da VRAM.")
    d, en = c.pos(c.entrada("D"), 0, 0), c.pos(c.entrada("EN"), 0, 2)
    q, qn = c.adiante(), c.adiante()
    s_ = c.pos(c.nand(d, en), 1, 0)
    r = c.pos(c.nand(s_, en), 2, 2)
    c.ligar(q, c.pos(c.nand(s_, qn), 3, 0))
    c.ligar(qn, c.pos(c.nand(r, q), 3, 2))
    c.saida("Q", q, pos=(4, 0))
    c.saida("/Q", qn, pos=(4, 2))
    return c

def v_ffd():
    c = Circuito("Flip-flop D", "08-registrador-a.md",
                 "Grava D só na borda de subida do CLK. São 2 latches em fila "
                 "(mestre e escravo): o mestre copia D com CLK = 0, o escravo copia "
                 "o mestre com CLK = 1. Mude D e depois o CLK de 0 para 1.",
                 "8 NAND + 1 NOT. É o flip-flop usado em todos os registradores.")
    d, clk = c.pos(c.entrada("D"), 0, 0), c.pos(c.entrada("CLK"), 0, 4)
    nclk = c.pos(c.not_(clk), 1, 4)
    qm, qmn = c.adiante(), c.adiante()
    s1 = c.pos(c.nand(d, nclk), 2, 0)
    r1 = c.pos(c.nand(s1, nclk), 3, 2)
    c.ligar(qm, c.pos(c.nand(s1, qmn), 4, 0))
    c.ligar(qmn, c.pos(c.nand(r1, qm), 4, 2))
    q, qn = c.adiante(), c.adiante()
    s2 = c.pos(c.nand(qm, clk), 5, 0)
    r2 = c.pos(c.nand(s2, clk), 6, 2)
    c.ligar(q, c.pos(c.nand(s2, qn), 7, 0))
    c.ligar(qn, c.pos(c.nand(r2, q), 7, 2))
    c.saida("Q", q, pos=(8, 0))
    c.saida("/Q", qn, pos=(8, 2))
    return c

def v_rega():
    c = Circuito("Registrador A (1 bit)", "08-registrador-a.md",
                 "Flip-flop D com enable: com A_WE = 1 grava o valor novo no ↑CLK; "
                 "com A_WE = 0 o mux devolve o próprio Q e nada muda.",
                 "Repetido 8 vezes = 8 flip-flops + 25 portas (o NOT do A_WE é um só).")
    P = c.pos
    novo = P(c.entrada("NOVO n"), 0, 0)
    we = P(c.entrada("A_WE"), 0, 2)
    clk = P(c.entrada("CLK"), 3, 4)
    q = c.adiante()
    nwe = P(c.not_(we), 1, 3)
    d = P(c.or_(P(c.and_(novo, we), 2, 0), P(c.and_(q, nwe), 2, 3)), 3, 1)
    c.ligar(q, P(c.ff(d, clk), 4, 1))
    c.saida("An", q, pos=(5, 1))
    return c

def v_flags():
    c = Circuito("Flags Z e C", "09-flags-z-e-c.md",
                 "Duas flags, cada uma um flip-flop D com enable: Z_WE e C_WE "
                 "decidem se a flag grava o valor novo no ↑CLK.")
    P = c.pos
    clk = P(c.entrada("CLK"), 3, 10)
    for k, nome in enumerate(("Z", "C")):
        o = 5 * k
        novo = P(c.entrada(nome + " novo"), 0, o)
        we = P(c.entrada(nome + "_WE"), 0, o + 2)
        q = c.adiante()
        nwe = P(c.not_(we), 1, o + 3)
        d = P(c.or_(P(c.and_(novo, we), 2, o), P(c.and_(q, nwe), 2, o + 3)), 3, o + 1)
        c.ligar(q, P(c.ff(d, clk, nome="FF " + nome), 4, o + 1))
        c.saida(nome, q, pos=(5, o + 1))
    return c

def v_pc():
    c = Circuito("PC (1 bit)", "12-registrador-pc.md",
                 "Um flip-flop D com clear: grava o próximo PC em todo ↑CLK; "
                 "/RST = 0 zera na hora (sem esperar o relógio).",
                 "Repetido 11 vezes. Não precisa de enable: o PC muda em toda instrução.")
    prox, clk, rst = c.entrada("PRÓX n"), c.entrada("CLK"), c.entrada("/RST", 1)
    c.saida("PCn", c.ff(prox, clk, rst))
    return c


def v_inc():
    c = Circuito("Incrementador +1 (11 bits)", "11-incrementador-11-bits.md",
                 "Soma 1 com meio-somadores em cadeia: cada bit é PCi XOR vem e "
                 "o vai-um é PCi AND vem. No bit 0 o vem é 1, então S0 = NOT PC0 e "
                 "o vai-um é o próprio PC0.")
    pc = [c.entrada("PC{}".format(i)) for i in range(11)]
    c.saida("S0", c.not_(pc[0]))
    vem = pc[0]
    for i in range(1, 11):
        c.saida("S{}".format(i), c.xor(pc[i], vem))
        vem = c.and_(pc[i], vem)
    c.saida("vai-um (sem uso)", vem)
    return c


def v_ptr():
    c = Circuito("Registrador-ponteiro (1 bit)", "21-registrador-ponteiro.md",
                 "Bit n do ponteiro da RAM (8 bits) e do cursor da VRAM (7 bits): "
                 "CARREGA põe A; AVANCA soma 1 (meio-somador com o vai-um do bit "
                 "anterior); sem os dois, segura.",
                 "WE = CARREGA OR AVANCA é um só para todos os bits. O vem do bit 0 é 1. "
                 "/RST só existe no cursor.")
    P = c.pos
    an = P(c.entrada("An"), 0, 0)
    carrega = P(c.entrada("CARREGA"), 0, 2)
    avanca = P(c.entrada("AVANCA"), 0, 4)
    vem = P(c.entrada("VEM (bit n−1)"), 0, 7)
    clk = P(c.entrada("CLK"), 5, 7)
    rst = P(c.entrada("/RST (cursor)", 1), 5, 8)
    q = c.adiante()
    inc = P(c.xor(q, vem), 1, 6)
    vai = P(c.and_(q, vem), 1, 8)
    ncar = P(c.not_(carrega), 1, 3)
    novo = P(c.or_(P(c.and_(an, carrega), 2, 0), P(c.and_(inc, ncar), 2, 5)), 3, 1)
    we = P(c.or_(carrega, avanca), 1, 4)
    nwe = P(c.not_(we), 2, 4)
    d = P(c.or_(P(c.and_(novo, we), 4, 1), P(c.and_(q, nwe), 4, 5)), 5, 3)
    c.ligar(q, P(c.ff(d, clk, rst), 6, 3))
    c.saida("Qn", q, pos=(7, 3))
    c.saida("VAI (bit n+1)", vai, pos=(7, 8))
    return c

def v_salto():
    c = Circuito("Lógica de salto", "14-logica-de-salto.md",
                 "TOMA = SALTO + SE_Z·Z + SE_NZ·/Z + SE_C·C + SE_NC·/C. "
                 "Só um dos sinais de salto fica em 1 por instrução.")
    salto = c.entrada("SALTO")
    se_z, se_nz = c.entrada("SE_Z"), c.entrada("SE_NZ")
    se_c, se_nc = c.entrada("SE_C"), c.entrada("SE_NC")
    z, cf = c.entrada("Z"), c.entrada("C")
    termos = [salto, c.and_(se_z, z), c.and_(se_nz, c.not_(z)),
              c.and_(se_c, cf), c.and_(se_nc, c.not_(cf))]
    c.saida("TOMA", c.ou_arvore(termos))
    return c


def v_dec4x16():
    c = Circuito("Decodificador 4 → 16", "17-decodificador-de-instrucoes.md",
                 "Uma linha por opcode: Lk = AND dos 4 bits de OP, cada um "
                 "invertido ou não. Só uma linha fica em 1.")
    op = [c.entrada("OP{}".format(i)) for i in (3, 2, 1, 0)]
    nops = [c.not_(o) for o in op]
    for k in range(16):
        bits = [(op[j] if (k >> (3 - j)) & 1 else nops[j]) for j in range(4)]
        c.saida("L{}".format(k), c.and_(*bits))
    return c


def v_dec():
    c = Circuito("Decodificador de instruções", "17-decodificador-de-instrucoes.md",
                 "OP vira 16 linhas (uma por opcode) e cada sinal de controle é um OR "
                 "das linhas onde ele vale 1. Os bits de F só entram no MEM e na ARIT "
                 "(na LOG vão direto para a ULA).",
                 "As mesmas equações de hardware.decodifica().")
    op = [c.entrada("OP{}".format(i)) for i in (3, 2, 1, 0)]
    f3, f2, f1, f0 = (c.entrada("F{}".format(i)) for i in (3, 2, 1, 0))
    L = c.bloco("dec4x16", *op, nome="Decodificador 4→16")
    arit, logica, mem = c.or_(L[4], L[5]), c.or_(L[6], L[7]), L[14]
    nf2, nf1, nf0 = c.not_(f2), c.not_(f1), c.not_(f0)
    m_grava = c.and_(mem, nf1, nf0)
    m_le = c.and_(mem, nf1, f0)
    m_carrega = c.and_(mem, f1, nf0)
    sinais = [
        ("A_WE", c.or_(L[0], L[1], L[3], c.and_(arit, c.not_(f3)), logica, L[13], m_le)),
        ("A_SRC1", c.or_(arit, logica, L[13])),
        ("A_SRC0", c.or_(L[1], L[3], L[13], mem)),
        ("MEM_VID", c.and_(mem, nf2)),
        ("RAM_WE", c.or_(L[2], c.and_(m_grava, f2))),
        ("END_SRC1", mem), ("END_SRC0", L[3]),
        ("B_IMED", c.or_(L[5], L[7])),
        ("SUB", c.and_(arit, f0)), ("USA_C", c.and_(arit, f1)), ("SHR", c.and_(arit, f2)),
        ("LOGICA", logica),
        ("Z_WE", c.or_(arit, logica)), ("C_WE", arit),
        ("SALTO", L[8]), ("SE_Z", L[9]), ("SE_NZ", L[10]), ("SE_C", L[11]), ("SE_NC", L[12]),
        ("TEC_RD", L[13]),
    ]
    vid_wr = c.and_(m_grava, nf2)
    sinais += [("VID_WR", vid_wr), ("CUR_INC", vid_wr),
               ("CUR_LD", c.and_(m_carrega, nf2)), ("PTR_LD", c.and_(m_carrega, f2)),
               ("PTR_INC", c.and_(mem, f2, nf1))]
    for nome, ref in sinais:
        c.saida(nome, ref)
    return c


# ============================================================
# MEMORIAS (fatias pequenas, mesma ideia do tamanho real)
# ============================================================

def v_rom():
    c = Circuito("ROM (fatia: 4 palavras × 8 bits)", "15-rom-de-programa.md",
                 "Decodificador de endereço + matriz de diodos. Cada diodo liga uma "
                 "linha de endereço a uma coluna de bit: vários diodos numa coluna "
                 "formam um OR. Aqui: bits 15..8 (OP e F) das 4 primeiras palavras "
                 "da bola (LDI, VPOS, LDI, ST).",
                 "A ROM real tem 11 bits de endereço (2048 linhas) × 16 colunas.")
    e1, e0 = c.entrada("END1"), c.entrada("END0")
    n1, n0 = c.not_(e1), c.not_(e0)
    linhas = [c.and_(n1, n0), c.and_(n1, e0), c.and_(e1, n0), c.and_(e1, e0)]
    palavras = [0x00, 0xE2, 0x00, 0x20]
    for b in range(7, -1, -1):
        uns = [linhas[k] for k in range(4) if (palavras[k] >> b) & 1]
        ref = c.const(0) if not uns else (uns[0] if len(uns) == 1 else c.or_(*uns))
        c.saida("D{}".format(b + 8), ref)
    return c


def _memoria(c, end1, end0, dado, we):
    n1, n0 = c.not_(end1), c.not_(end0)
    linhas = [c.and_(n1, n0), c.and_(n1, end0), c.and_(end1, n0), c.and_(end1, end0)]
    cel = [c.latch(dado, c.and_(we, l), nome="célula {}".format(k))
           for k, l in enumerate(linhas)]
    return c.ou_arvore([c.and_(q, l) for q, l in zip(cel, linhas)])


def v_ram():
    c = Circuito("RAM (fatia: 4 endereços × 1 bit)", "16-ram.md",
                 "Decodificador de endereço, uma célula (latch D) por endereço e "
                 "um mux de saída. A gravação só acontece com RAM_WE = 1 e "
                 "CLK_BAIXO = 1 (metade baixa do relógio).",
                 "A RAM real: 256 endereços × 8 bits = 2048 células.")
    e1, e0 = c.entrada("END1"), c.entrada("END0")
    din = c.entrada("DIN (= A)")
    we = c.and_(c.entrada("RAM_WE"), c.entrada("CLK_BAIXO"))
    c.saida("DOUT", _memoria(c, e1, e0, din, we))
    return c


def v_vram():
    c = Circuito("VRAM (fatia: 4 endereços × 1 bit)", "18-display.md",
                 "Igual à RAM, com um mux na frente do endereço: em instruções de "
                 "vídeo (MEM_VID = 1) quem endereça é o cursor da CPU; no resto do "
                 "tempo, a varredura que acende o painel.",
                 "A VRAM real: 128 endereços × 8 bits.")
    sel = c.entrada("MEM_VID")
    cur1, cur0 = c.entrada("CURSOR1"), c.entrada("CURSOR0")
    var1, var0 = c.entrada("VARRE1"), c.entrada("VARRE0")
    dado = c.entrada("DADO (= A)")
    we = c.and_(c.entrada("VID_WR"), c.entrada("CLK_BAIXO"))
    ns = c.not_(sel)
    e1 = c.mux2(sel, var1, cur1, ns)
    e0 = c.mux2(sel, var0, cur0, ns)
    c.saida("DOUT (CPU e painel)", _memoria(c, e1, e0, dado, we))
    return c


# ============================================================
# ENTRADA, SAIDA E RELOGIO
# ============================================================

def v_teclado():
    c = Circuito("Teclado (1 botão)", "19-teclado.md",
                 "O botão passa por 2 flip-flops (sincroniza e guarda o valor "
                 "anterior); aperto = agora AND NOT antes. O evento fica guardado "
                 "até a CPU ler (TEC_RD).",
                 "Repetido 5 vezes; o NOT do TEC_RD é um só. O debounce (RC + "
                 "Schmitt) vem antes, fora deste circuito.")
    P = c.pos
    botao = P(c.entrada("BOTÃO"), 0, 0)
    clk = P(c.entrada("CLK"), 0, 3)
    rd = P(c.entrada("TEC_RD"), 0, 7)
    b1 = P(c.ff(botao, clk, nome="FF sincroniza"), 1, 0)
    b2 = P(c.ff(b1, clk, nome="FF anterior"), 2, 3)
    aperto = P(c.and_(b1, P(c.not_(b2), 3, 3)), 4, 1)
    ev = c.adiante()
    manter = P(c.and_(ev, P(c.not_(rd), 1, 7)), 4, 6)
    c.ligar(ev, P(c.ff(P(c.or_(aperto, manter), 5, 3), clk, nome="FF evento"), 6, 3))
    c.saida("SAÍDA n", ev, pos=(7, 3))
    return c

def v_relogio():
    c = Circuito("Relógio e reset", "20-relogio-e-reset.md",
                 "CLK vem do oscilador (MODO = 1) ou do botão de passo (MODO = 0). "
                 "CLK_BAIXO = NOT CLK libera os pulsos de escrita. /RST é o botão "
                 "RESET invertido.",
                 "O oscilador e o debounce dos botões são peças analógicas (fora "
                 "deste circuito).")
    osc, passo, modo = c.entrada("OSCILADOR"), c.entrada("BOTÃO PASSO"), c.entrada("MODO")
    reset = c.entrada("BOTÃO RESET")
    clk = c.mux2(modo, passo, osc)
    c.saida("CLK", clk)
    c.saida("CLK_BAIXO", c.not_(clk))
    c.saida("/RST", c.not_(reset))
    return c


# ============================================================
# TODAS AS VISTAS
# ============================================================

VISTAS = {
    "fa": v_fa,
    "soma8": v_soma8,
    "inv8": v_inv8,
    "logica": v_logica,
    "mux2": _v_mux2("Mux 2×1 (1 bit)", "05-multiplexador-2x1-8-bits.md", "S", "D0", "D1",
                    "Y", "Y = (D0 AND /S) OR (D1 AND S).",
                    "Com 8 bits: o NOT do S é um só (1 NOT + 16 AND + 8 OR)."),
    "mux4": _v_mux4("Mux 4×1 (1 bit)", "10-multiplexador-4x1-8-bits.md", "S1", "S0",
                    ["D0", "D1", "D2", "D3"], "Y",
                    "S1 e S0 viram 4 linhas (só uma em 1); cada linha libera uma "
                    "entrada e um OR junta.",
                    "Com 8 bits: as 4 linhas (2 NOT + 4 AND) são feitas uma vez só."),
    "zero": v_zero,
    "cin": v_cin,
    "shr": v_shr,
    "cnovo": _v_mux2("C novo", "07-ula.md", "SHR", "COUT", "A0", "C novo",
                     "Mux 2×1 de 1 bit: com SHR o C novo é o bit que saiu (A0); "
                     "senão, o vai-um final do somador."),
    "muxr": _v_mux4("Mux de resultado (1 bit)", "10-multiplexador-4x1-8-bits.md",
                    "SHR", "LOGICA", ["SOMA n", "LÓGICA n", "An+1", "0"], "Rn",
                    "Escolhe o resultado da ULA: 00 soma, 01 lógica, 10 SHR.",
                    "Repetido 8 vezes; a entrada 11 é 0 (sem uso)."),
    "ula": v_ula,
    "latch": v_latch,
    "ffd": v_ffd,
    "rega": v_rega,
    "flags": v_flags,
    "pc": v_pc,
    "inc": v_inc,
    "ptr": v_ptr,
    "salto": v_salto,
    "dec4x16": v_dec4x16,
    "dec": v_dec,
    "rom": v_rom,
    "ram": v_ram,
    "vram": v_vram,
    "teclado": v_teclado,
    "relogio": v_relogio,
    "muxpc": _v_mux2("Mux do próximo PC (1 bit)", "13-multiplexador-proximo-pc.md",
                     "TOMA", "PC+1 n", "DEST n", "PRÓX n",
                     "TOMA = 0 segue para PC + 1; TOMA = 1 salta para o destino.",
                     "Repetido 11 vezes (1 NOT + 22 AND + 11 OR)."),
    "muxb": _v_mux2("Mux B (1 bit)", "05-multiplexador-2x1-8-bits.md",
                    "B_IMED", "RAM n", "N n", "Bn",
                    "Segundo operando da ULA: dado da RAM (B_IMED = 0) ou o número N "
                    "da instrução (B_IMED = 1).", "Repetido 8 vezes."),
    "muxmem": _v_mux2("Mux de memória (1 bit)", "05-multiplexador-2x1-8-bits.md",
                      "MEM_VID", "RAM n", "VRAM n", "MEM n",
                      "Qual memória entrega o dado para A: RAM (0) ou VRAM (1).",
                      "Repetido 8 vezes."),
    "muxend": _v_mux4("Mux de endereço da RAM (1 bit)", "10-multiplexador-4x1-8-bits.md",
                      "END_SRC1", "END_SRC0", ["N n", "A n", "PONT n", "0"], "END n",
                      "Endereço da RAM: 00 N, 01 A (LDR), 10 ponteiro (LDP/STP).",
                      "Repetido 8 vezes; a entrada 11 é 0 (sem uso)."),
    "muxa": _v_mux4("Mux de A (1 bit)", "10-multiplexador-4x1-8-bits.md",
                    "A_SRC1", "A_SRC0", ["N n", "MEM n", "R n", "TECL n"], "NOVO n",
                    "Valor novo de A: 00 N, 01 memória, 10 ULA, 11 teclado.",
                    "Repetido 8 vezes."),
}

# componente do esquema principal -> vista em portas
DO_ESQUEMA = {
    "relogio": "relogio", "muxpc": "muxpc", "pc": "pc", "inc": "inc", "rom": "rom",
    "dec": "dec", "salto": "salto", "flags": "flags", "muxend": "muxend", "ptr": "ptr",
    "ram": "ram", "muxb": "muxb", "ula": "ula", "inv": "inv8", "cin": "cin",
    "soma": "soma8", "logica": "logica", "shr": "shr", "muxr": "muxr", "zero": "zero",
    "cnovo": "cnovo", "muxmem": "muxmem", "muxa": "muxa", "rega": "rega",
    "cursor": "ptr", "vram": "vram", "teclado": "teclado",
}
