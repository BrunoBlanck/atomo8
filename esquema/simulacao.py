# -*- coding: utf-8 -*-
"""
SIMULACAO DENTRO DO ESQUEMA

Usa o MESMO hardware.py (porta a porta, bit a bit). Aqui so existe:
  - Maquina: o Computador sem terminal e sem esperar o relogio real;
  - caminho(): a partir do rastro de 1 instrucao, quais fios e blocos
    trabalharam, com o valor de cada barramento e em que fase do ciclo.
Nada de logica do hardware e reescrito aqui: tudo vem dos sinais que
hardware.decodifica() gerou e dos valores que hardware.passo() registrou.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import hardware                                         # noqa: E402

# ============================================================
# PROGRAMAS DISPONIVEIS
# ============================================================

def programas():
    import doom
    import bola
    import tetris
    return {"DOOM": doom.PROGRAMA, "Bola": bola.PROGRAMA, "Tetris": tetris.PROGRAMA}


# ============================================================
# FASES DE UMA INSTRUCAO (tudo dentro de 1 x CLOCK)
# ============================================================

FASES = [
    ("Busca", "PC → ROM → decodificador; PC + 1"),
    ("Operandos", "endereço da RAM, leituras, B, A, flags"),
    ("Calcula", "ULA, mux de A, lógica de salto"),
    ("Grava", "metade baixa: pulso de escrita na RAM / VRAM"),
    ("↑CLK", "registradores gravam juntos: A, Z, C, PC, ponteiro, cursor"),
]


# nomes curtos dos blocos (lista de barramentos na barra lateral)
CURTO = {"pc": "PC", "rom": "ROM", "dec": "DEC", "inc": "INC", "muxpc": "MUXPC",
         "salto": "SALTO", "flags": "FLAGS", "muxend": "MUXEND", "ptr": "PONT",
         "ram": "RAM", "muxb": "MUXB", "ula": "ULA", "inv": "INV", "cin": "CIN",
         "soma": "SOMA", "logica": "LOGICA", "shr": "SHR", "muxr": "MUXR",
         "zero": "ZERO", "cnovo": "CNOVO", "muxmem": "MUXMEM", "muxa": "MUXA",
         "rega": "A", "cursor": "CURSOR", "vram": "VRAM", "teclado": "TECL",
         "relogio": "CLK"}


# ============================================================
# MAQUINA
# ============================================================

class Maquina(hardware.Computador):
    """Computador do hardware.py sem terminal: o tempo e contado em CLOCKs,
    mas quem decide a velocidade e o esquema."""

    def __init__(self, fonte):
        super().__init__()
        d = hardware.montar_detalhado(fonte)
        self.fonte = fonte.splitlines()
        self.linha_de = d["linhas"]                  # endereco -> linha do texto
        self.rotulos = d["rotulos"]
        self.tamanho = len(d["rom"])
        self.gravar_rom(d["rom"])
        self.quadros = 0
        self.teclas_pendentes = 0
        self.display.mostrar = lambda rodape="": None
        self.teclado.ler = self._ler_teclado

    # nada de dormir: o esquema controla a velocidade
    def _gastar_clocks(self, n):
        self.clocks += n

    def _quadro_completo(self):
        self.quadros += 1
        super()._quadro_completo()

    # teclado: trava de evento (cada aperto entregue uma vez; sem aperto = 0)
    def apertar(self, bit):
        self.teclas_pendentes |= bit

    def _ler_teclado(self):
        v, self.teclas_pendentes = self.teclas_pendentes, 0
        return v

    def passo_rastreado(self):
        self.rastrear = True
        self.passo()
        self.rastrear = False
        return self.rastro

    def linha_atual(self):
        """Numero (1..) da linha do texto da instrucao no PC."""
        if self.pc < self.tamanho:
            return self.linha_de[self.pc]
        return None


# ============================================================
# CAMINHO DE UMA INSTRUCAO A PARTIR DO RASTRO
#   devolve {fio: (valor, bits, fase)}, {bloco: texto do valor}
# ============================================================

def _bits_flags(z, c):
    return (z << 1) | c


def caminho(r):
    s = r["sinais"]
    fios = {}

    def liga(fio, valor, bits, fase):
        fios[fio] = (valor & ((1 << bits) - 1), bits, fase)

    # ---- fase 0: busca (sempre)
    liga("pc_rom", r["pc"], 11, 0)
    liga("rom_dec", (r["op"] << 4) | r["f"], 8, 0)
    liga("pc_inc", r["pc"], 11, 0)
    liga("inc_muxpc", r["pc_mais_1"], 11, 0)

    usa_ula = s.Z_WE                            # ARIT/ARITI/LOG/LOGI
    le_ram = r["le_ram"]
    usa_end_ram = le_ram or s.RAM_WE

    # ---- fase 1: operandos
    if usa_end_ram:
        fonte = (s.END_SRC1 << 1) | s.END_SRC0
        if fonte == 0:
            liga("rom_n_end", r["n"], 8, 1)
        elif fonte == 1:
            liga("a_end", r["a"], 8, 1)
        else:
            liga("ptr_end", r["ponteiro"], 8, 1)
        liga("end_ram", r["end"], 8, 1)
    if usa_ula:
        if s.B_IMED:
            liga("rom_n_b", r["n"], 8, 1)
        else:
            liga("ram_b", r["dado_ram"], 8, 1)
        liga("b_ula", r["b"], 8, 1)
        liga("a_ula", r["a"], 8, 1)
        if s.LOGICA:
            liga("rom_f", r["f"], 4, 1)
        if s.USA_C:
            liga("flags_ula", r["c"], 1, 1)
    le_memoria = s.A_WE and s.A_SRC0 and not s.A_SRC1
    if le_memoria:
        if s.MEM_VID:
            liga("cur_vram", r["cursor"], 7, 1)
            liga("vram_mem", r["dado_vram"], 8, 1)
        else:
            liga("ram_mem", r["dado_ram"], 8, 1)
    if s.VID_WR:
        liga("cur_vram", r["cursor"], 7, 1)
    saltos = (s.SALTO << 4) | (s.SE_Z << 3) | (s.SE_NZ << 2) | (s.SE_C << 1) | s.SE_NC
    if saltos:
        liga("dec_salto", saltos, 5, 1)
        if saltos & 0b01111:
            liga("flags_salto", _bits_flags(r["z"], r["c"]), 2, 1)

    # ---- fase 2: calcula
    if usa_ula:
        u = r["ula"]
        if s.LOGICA:
            liga("logica_muxr", u["logico"], 8, 2)
        elif s.SHR:
            liga("shr_muxr", u["deslocado"], 8, 2)
        else:
            liga("inv_soma", u["b_inv"], 8, 2)
            liga("cin_soma", u["cin"], 1, 2)
            liga("soma_muxr", u["soma"], 8, 2)
        if s.C_WE and not s.SHR:
            liga("soma_cnovo", u["cout"], 1, 2)
        liga("muxr_zero", r["r"], 8, 2)
        liga("ula_flags", _bits_flags(r["z_novo"], r["c_novo"]), 2, 2)
    if s.A_WE:
        fonte = (s.A_SRC1 << 1) | s.A_SRC0
        if fonte == 0:
            liga("rom_n_a", r["n"], 8, 2)
        elif fonte == 1:
            liga("mem_a", r["memoria"], 8, 2)
        elif fonte == 2:
            liga("ula_a", r["r"], 8, 2)
        else:
            liga("tec_a", r["teclado"], 8, 2)
    if saltos:
        liga("salto_pc", r["toma"], 1, 2)
        if r["toma"]:
            liga("rom_dest", r["destino"], 11, 2)

    # ---- fase 3: grava (metade baixa)
    if s.RAM_WE:
        liga("a_ram", r["a"], 8, 3)
    if s.VID_WR:
        liga("a_vram", r["a"], 8, 3)

    # ---- fase 4: ↑CLK
    liga("muxpc_pc", r["prox_pc"], 11, 4)
    if s.A_WE:
        liga("muxa_rega", r["novo_a"], 8, 4)
    if s.PTR_LD:
        liga("a_ptr", r["a"], 8, 4)
    if s.CUR_LD:
        liga("a_cursor", r["a"], 8, 4)
    return fios


def blocos_ativos(r, fios, por_fio):
    """Blocos que trabalharam: pontas dos fios ligados + blocos que mudam sem fio."""
    s = r["sinais"]
    ativos = {"relogio", "dec", "rom", "pc", "inc", "muxpc"}
    for fio in fios:
        de, para = por_fio[fio]
        ativos.update((de, para))
    if s.PTR_INC:
        ativos.add("ptr")
    if s.CUR_INC:
        ativos.add("cursor")
    if s.Z_WE:
        ativos.update(("ula", "flags"))
    return ativos


def valores_blocos(maq, r=None):
    """Texto curto de valor para desenhar dentro de cada bloco."""
    h = lambda v, d=2: "0x{:0{}X}".format(v, d)
    v = {
        "pc": h(maq.pc, 3),
        "rega": "{}  {:08b}".format(h(maq.a), maq.a),
        "flags": "Z={}  C={}".format(maq.z, maq.c),
        "ptr": h(maq.ponteiro),
        "cursor": "{} (col {}, pág {})".format(h(maq.cursor), maq.cursor >> 2, maq.cursor & 3),
        "rom": hardware.desmontar(maq.rom[maq.pc]),
        "inc": h((maq.pc + 1) & 0x7FF, 3),
        "teclado": "{:05b}".format(maq.teclas_pendentes),
    }
    if r is not None:
        s = r["sinais"]
        v["rom"] = hardware.desmontar(r["palavra"])
        v["dec"] = "OP={:04b} F={:04b}".format(r["op"], r["f"])
        v["muxpc"] = "→ " + h(r["prox_pc"], 3) + (" (salto)" if r["toma"] else "")
        if r["le_ram"] or s.RAM_WE:
            val = r["a"] if s.RAM_WE else r["dado_ram"]
            v["ram"] = "[{}] {} {}".format(h(r["end"]), "←" if s.RAM_WE else "=", h(val))
            v["muxend"] = ["N", "A", "ponteiro", "-"][(s.END_SRC1 << 1) | s.END_SRC0] + " → " + h(r["end"])
        if s.Z_WE:
            v["ula"] = "R = {}  {:08b}".format(h(r["r"]), r["r"])
            v["muxb"] = ("N" if s.B_IMED else "RAM") + " → " + h(r["b"])
            v["muxr"] = ("lógica" if s.LOGICA else "SHR" if s.SHR else "soma") + " → " + h(r["r"])
        if s.A_WE:
            v["muxa"] = ["N", "MEM", "ULA", "teclado"][(s.A_SRC1 << 1) | s.A_SRC0] + " → " + h(r["novo_a"])
        if s.A_WE and s.A_SRC0 and not s.A_SRC1:
            v["muxmem"] = ("VRAM" if s.MEM_VID else "RAM") + " → " + h(r["memoria"])
        if s.SALTO or s.SE_Z or s.SE_NZ or s.SE_C or s.SE_NC:
            v["salto"] = "TOMA = {}".format(r["toma"])
        if s.VID_WR:
            v["vram"] = "[{}] ← {}".format(h(r["cursor"]), h(r["a"]))
        elif s.MEM_VID and s.A_WE:
            v["vram"] = "[{}] = {}".format(h(r["cursor"]), h(r["dado_vram"]))
        if s.TEC_RD:
            v["teclado"] = "lido {:05b}".format(r["teclado"])
    return v
