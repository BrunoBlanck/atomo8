# -*- coding: utf-8 -*-
"""
HARDWARE DO LABIRINTO 3D (simulado)

Este NAO e um computador de uso geral: e o hardware minimo para rodar os
programas da ROM (doom.py, bola.py, tetris.py) num display 32 x 32 de 1 bit. Tudo e
feito com PORTAS LOGICAS (AND, OR, NOT, XOR) e flip-flops de portas; cada
peca esta descrita em componentes/*.md para ser construida e testada
sozinha.

------------------------------------------------------------------
VISAO GERAL
------------------------------------------------------------------

  +---------+  endereco 11 bits  +------------------+
  |   PC    |------------------->|  ROM 2048 x 16   |
  +---------+                    +------------------+
     ^   |                     OP (4) | F (4) | N (8) / destino (11)
     |  +1                            v
  +--------+   TOMA          +-------------+
  | MUX PC |<----------------| DECODIFICA  |---- sinais de controle
  +--------+                 |  + SALTO    |<--- flags Z e C
                             +-------------+
         N ---->+-----+   endereco   +-----------+
         A ---->| MUX |------------->| RAM 256x8 |
  PONTEIRO ---->+-----+              +-----------+
                                          | dado
                                          v
   N ----------------------------->+-----+     +-------+
                                   | MUX |---->|  ULA  |---> Z, C
                                   +-----+  B  +-------+
                                                   |  F = funcao / tabela
                                                   v
   N, MEMORIA (RAM ou VRAM), ULA, TECLADO -> MUX 4x1 -> [ A ]
                                                         |
                    RAM (ST/STP), VRAM (VOUT), PONTEIRO e CURSOR (carga) <-+

  CURSOR (7 bits) ---> VRAM 128 x 8 ---> painel 32 x 32

------------------------------------------------------------------
REGISTRADORES
------------------------------------------------------------------
  A        : 8 bits   acumulador (unico registrador de dados)
  PC       : 11 bits  contador de programa (ROM de 2048 instrucoes)
  Z        : 1 bit    resultado da ULA foi zero
  C        : 1 bit    vai-um da ULA (depois de SUB/CMP: C = 1 -> A >= B)
  PONTEIRO : 8 bits   endereco da RAM para LDP / STP (soma 1 sozinho)
  CURSOR   : 7 bits   endereco da VRAM para VIN / VOUT (soma 1 no VOUT)

------------------------------------------------------------------
MEMORIAS
------------------------------------------------------------------
  ROM  : 2048 palavras de 16 bits (so o programa; a CPU nao le dados dela)
  RAM  : 256 bytes. Liga com lixo; o programa inicializa o que usa.
  VRAM : 128 bytes = a imagem. Separada da RAM; a CPU le e grava.

------------------------------------------------------------------
FORMATO DA INSTRUCAO (16 bits)
------------------------------------------------------------------
   15 .. 12   11 .. 8    7 .. 0
  [ opcode ] [   F   ] [ operando N ]

  saltos : destino = bits 10..0 (bit 11 = 0)
  demais : F = funcao (ARIT), tabela-verdade (LOG) ou subfuncao (MEM)
           N = numero imediato ou endereco de RAM

------------------------------------------------------------------
CONJUNTO DE INSTRUCOES
------------------------------------------------------------------
  cod  nome       F         efeito                           flags
   0   LDI n      -         A = n
   1   LD  m      -         A = RAM[m]
   2   ST  m      -         RAM[m] = A
   3   LDR        -         A = RAM[A]  (leitura indireta)
   4   ARIT m     funcao    A = A (op) RAM[m]                Z, C
   5   ARITI n    funcao    A = A (op) n                     Z, C
   6   LOG m      tabela    A = f(A, RAM[m]) bit a bit       Z
   7   LOGI n     tabela    A = f(A, n) bit a bit            Z
   8   JMP e                PC = e
   9   JZ  e                se Z = 1: PC = e
  10   JNZ e                se Z = 0: PC = e
  11   JC  e                se C = 1: PC = e
  12   JNC e                se C = 0: PC = e
  13   IN                   A = eventos do teclado (0 = nada)
  14   MEM        sub       VRAM e ponteiro (tabela abaixo)
  15   (livre: nao faz nada)

  ARIT: cada bit de F liga direto num ponto da ULA (sem decodificar)
     bit 8  = SUB    inverte B e o vai-um de entrada vira 1
     bit 9  = USA_C  o vai-um de entrada vem da flag C
     bit 10 = SHR    resultado = A >> 1, C = bit 0 de A
     bit 11 = NG     nao grava A (so as flags)
     ADD 0000  SUB 0001  ADC 0010  SBC 0011  SHR 0100  CMP 1001

  LOG: F = tabela-verdade. Bit n do resultado = F[2*An + Bn]
     AND 1000  OR 1110  XOR 0110  "passa A" (TST) 1100  NOT A 0011

  MEM: bit 10 escolhe a memoria, bits 9..8 a operacao
     0000 VOUT  VRAM[cursor] = A, cursor + 1
     0001 VIN   A = VRAM[cursor]
     0010 VPOS  cursor = A
     0100 STP   RAM[ponteiro] = A, ponteiro + 1
     0101 LDP   A = RAM[ponteiro], ponteiro + 1
     0110 PTR   ponteiro = A

  So ARIT/ARITI mudam C. So ARIT/ARITI/LOG/LOGI mudam Z.

------------------------------------------------------------------
ULA (8 bits)
------------------------------------------------------------------
  SOMADOR  : 8 somadores completos; B passa por 8 XOR (SUB)
  VAI-UM   : CIN = (USA_C AND C) OR (NOT USA_C AND SUB)
  LOGICA   : 1 mux 4x1 por bit, ao contrario: An e Bn na selecao,
             a tabela-verdade F nos dados
  SHR      : so fios (A7..A1 -> R6..R0, R7 = 0)
  RESULTADO: mux 4x1 (soma, logica, SHR)
  Z = NOR dos 8 bits.  C = SHR ? A0 : vai-um final do somador

------------------------------------------------------------------
ENTRADA E SAIDA
------------------------------------------------------------------
  IN  : teclado, um bit por botao (evento: 1 so uma vez por aperto)
        bit0 frente, bit1 tras, bit2 gira esq., bit3 gira dir., bit4 mapa
        Sem aperto pendente, IN devolve 0 (nao espera).
  VRAM: endereco = COLUNA (5 bits) : PAGINA (2 bits) = 4 x coluna + pagina.
        VOUT grava e soma 1 ao cursor: desce as 4 paginas e passa para a
        proxima coluna; depois de 127 volta a 0. Byte = 8 pixels em pe;
        bit 0 = pixel de cima da pagina.
"""

import random
import sys
import time

# ============================================================
# TEMPOS DO HARDWARE - tudo em funcao de uma unica constante: CLOCK
# ============================================================

# Periodo de 1 pulso do relogio, em microssegundos. VALOR X: ainda nao se
# sabe o real. Troque pelo valor medido quando o hardware estiver pronto
# (componentes/20-relogio-e-reset.md, "Como descobrir o CLOCK").
CLOCK_US = 100.0

# Ciclo unico: busca na ROM, leitura da memoria, ULA e gravacao acontecem
# todas dentro do mesmo pulso. Toda instrucao gasta 1 x CLOCK.
CLOCKS_POR_INSTRUCAO = 1

# CLOCKs EXTRAS de espera, para simular pecas mais lentas que o ciclo.
# No hardware descrito em componentes/ todos sao 0.
CLOCKS_EXTRA_LEITURA = 10   # por leitura de RAM (LD, LDR, LDP, ARIT m, LOG m)
CLOCKS_EXTRA_GRAVACAO = 10  # por gravacao (ST/STP na RAM e VOUT na VRAM)
CLOCKS_EXTRA_DISPLAY = 100  # quando o quadro fica completo (cursor volta a 0)

# O painel real varre a VRAM sozinho o tempo todo. O terminal e lento,
# entao o simulador so redesenha: (1) quando o cursor volta a 0 (quadro
# completo) ou (2) a cada TELA_S segundos se a VRAM mudou e nenhum quadro
# completo apareceu no ultimo meio segundo (programas que mudam so alguns
# bytes, como a bola).
TELA_S = 0.05

# ============================================================
# OPCODES E SUBFUNCOES (usados pelo montador e pelo decodificador)
# ============================================================

OP_LDI, OP_LD, OP_ST, OP_LDR = 0, 1, 2, 3
OP_ARIT, OP_ARITI, OP_LOG, OP_LOGI = 4, 5, 6, 7
OP_JMP, OP_JZ, OP_JNZ, OP_JC, OP_JNC = 8, 9, 10, 11, 12
OP_IN, OP_MEM = 13, 14

# Tabelas-verdade do LOG (bits 11..8 = F3 F2 F1 F0; Rn = F[2*An + Bn])
T_AND, T_OR, T_XOR, T_TST, T_NOT = 0b1000, 0b1110, 0b0110, 0b1100, 0b0011

# Cada mnemonico: (opcode, F fixo, tipo do operando)
#   "n" numero 8 bits, "m" endereco de RAM, "e" destino 11 bits, "" nenhum,
#   "tn"/"tm" tabela-verdade + numero/endereco (forma generica do LOG)
INSTRUCOES = {
    "LDI":  (OP_LDI, 0, "n"),
    "LD":   (OP_LD, 0, "m"),
    "ST":   (OP_ST, 0, "m"),
    "LDR":  (OP_LDR, 0, ""),
    # ARIT: F = NG SHR USA_C SUB
    "ADD":  (OP_ARIT, 0b0000, "m"),  "ADDI": (OP_ARITI, 0b0000, "n"),
    "SUB":  (OP_ARIT, 0b0001, "m"),  "SUBI": (OP_ARITI, 0b0001, "n"),
    "ADC":  (OP_ARIT, 0b0010, "m"),  "ADCI": (OP_ARITI, 0b0010, "n"),
    "SBC":  (OP_ARIT, 0b0011, "m"),  "SBCI": (OP_ARITI, 0b0011, "n"),
    "CMP":  (OP_ARIT, 0b1001, "m"),  "CMPI": (OP_ARITI, 0b1001, "n"),
    "SHR":  (OP_ARITI, 0b0100, ""),
    # LOG: F = tabela-verdade
    "AND":  (OP_LOG, T_AND, "m"),    "ANDI": (OP_LOGI, T_AND, "n"),
    "OR":   (OP_LOG, T_OR, "m"),     "ORI":  (OP_LOGI, T_OR, "n"),
    "XOR":  (OP_LOG, T_XOR, "m"),    "XORI": (OP_LOGI, T_XOR, "n"),
    "TST":  (OP_LOGI, T_TST, ""),    "NOT":  (OP_LOGI, T_NOT, ""),
    "LOG":  (OP_LOG, 0, "tm"),       "LOGI": (OP_LOGI, 0, "tn"),
    # saltos
    "JMP":  (OP_JMP, 0, "e"),  "JZ": (OP_JZ, 0, "e"),  "JNZ": (OP_JNZ, 0, "e"),
    "JC":   (OP_JC, 0, "e"),   "JNC": (OP_JNC, 0, "e"),
    "IN":   (OP_IN, 0, ""),
    # MEM: F = 0 RAM? operacao(2)   00 grava, 01 le, 10 carrega
    "VOUT": (OP_MEM, 0b0000, ""),  "OUT": (OP_MEM, 0b0000, ""),
    "VIN":  (OP_MEM, 0b0001, ""),
    "VPOS": (OP_MEM, 0b0010, ""),
    "STP":  (OP_MEM, 0b0100, ""),
    "LDP":  (OP_MEM, 0b0101, ""),
    "PTR":  (OP_MEM, 0b0110, ""),
}


# ============================================================
# PORTAS (1 bit). Todo o resto e montado so com elas.
# ============================================================

def NOT(a):
    return a ^ 1


def bit(v, i):
    return (v >> i) & 1


def mux2(s, d0, d1):
    """Mux 2x1 de 1 bit (arquivo 05): (D0 AND /S) OR (D1 AND S)."""
    return (d0 & NOT(s)) | (d1 & s)


def mux4(s1, s0, d0, d1, d2, d3):
    """Mux 4x1 de 1 bit (arquivo 10): um AND por entrada + OR."""
    l0 = NOT(s1) & NOT(s0)
    l1 = NOT(s1) & s0
    l2 = s1 & NOT(s0)
    l3 = s1 & s0
    return (d0 & l0) | (d1 & l1) | (d2 & l2) | (d3 & l3)


def mux2_n(s, d0, d1, largura=8):
    r = 0
    for i in range(largura):
        r |= mux2(s, bit(d0, i), bit(d1, i)) << i
    return r


def mux4_n(s1, s0, d0, d1, d2, d3, largura=8):
    r = 0
    for i in range(largura):
        r |= mux4(s1, s0, bit(d0, i), bit(d1, i), bit(d2, i), bit(d3, i)) << i
    return r


def incrementa(v, largura):
    """Incrementador (arquivo 11): meio-somadores em cadeia, vem-um = 1."""
    vem, r = 1, 0
    for i in range(largura):
        a = bit(v, i)
        r |= (a ^ vem) << i
        vem = a & vem
    return r


# ============================================================
# ULA - simulada porta a porta, igual ao circuito (arquivo 07)
# ============================================================

class ULA:

    @staticmethod
    def somador_completo(a, b, vem):
        s = a ^ b ^ vem
        vai = (a & b) | (vem & (a ^ b))
        return s, vai

    def calcula(self, a, b, sub, usa_c, shr, logica, tabela, c):
        """
        a, b   : bytes
        sub    : inverte B (8 XOR)
        usa_c  : o vai-um de entrada vem da flag C
        shr    : resultado = A >> 1
        logica : resultado = unidade logica (tabela-verdade)
        tabela : F3..F0 (so vale com logica = 1)
        c      : flag C atual
        Retorna (resultado, Z, C novo).
        """
        # vai-um de entrada: (USA_C AND C) OR (NOT USA_C AND SUB)
        vem = (usa_c & c) | (NOT(usa_c) & sub)
        cin = vem

        soma = 0
        logico = 0
        deslocado = 0
        for i in range(8):
            ai, bi = bit(a, i), bit(b, i)
            # somador (arquivos 01-03)
            s, vem = self.somador_completo(ai, bi ^ sub, vem)
            soma |= s << i
            # unidade logica (arquivo 04): An e Bn na selecao, F nos dados
            logico |= mux4(ai, bi, bit(tabela, 0), bit(tabela, 1),
                           bit(tabela, 2), bit(tabela, 3)) << i
            # SHR: so fios (R7 = 0)
            if i < 7:
                deslocado |= bit(a, i + 1) << i
        cout = vem

        # mux de resultado 4x1: 00 soma, 01 logica, 10 SHR, 11 (sem uso)
        r = mux4_n(shr, logica, soma, logico, deslocado, 0)
        # Z = NOR dos 8 bits (arquivo 06)
        z = NOT(bit(r, 0) | bit(r, 1) | bit(r, 2) | bit(r, 3) |
                bit(r, 4) | bit(r, 5) | bit(r, 6) | bit(r, 7))
        # C novo = SHR ? A0 : vai-um final
        c_novo = mux2(shr, cout, bit(a, 0))
        # valores dos fios internos (so leitura, para o esquema interativo)
        self.interno = dict(b_inv=b ^ (0xFF if sub else 0), cin=cin, soma=soma,
                            logico=logico, deslocado=deslocado, cout=cout)
        return r, z, c_novo


# ============================================================
# DECODIFICADOR - so portas (arquivo 17)
# ============================================================

class Sinais:
    """Sinais de controle de uma instrucao (todos 0 ou 1)."""
    __slots__ = ("A_WE", "A_SRC1", "A_SRC0", "MEM_VID", "RAM_WE",
                 "END_SRC1", "END_SRC0", "B_IMED", "SUB", "USA_C", "SHR",
                 "LOGICA", "Z_WE", "C_WE", "SALTO", "SE_Z", "SE_NZ", "SE_C",
                 "SE_NC", "TEC_RD", "VID_WR", "CUR_LD", "CUR_INC",
                 "PTR_LD", "PTR_INC")


def decodifica(op, f):
    """Gera os sinais de controle a partir do opcode e de F (bits 11..8)."""
    o3, o2, o1, o0 = bit(op, 3), bit(op, 2), bit(op, 1), bit(op, 0)
    f3, f2, f1, f0 = bit(f, 3), bit(f, 2), bit(f, 1), bit(f, 0)
    n3, n2, n1, n0 = NOT(o3), NOT(o2), NOT(o1), NOT(o0)

    # passo 1: decodificador 4 -> 16 (uma linha por opcode)
    L = [0] * 16
    for k in range(16):
        L[k] = ((o3 if k & 8 else n3) & (o2 if k & 4 else n2) &
                (o1 if k & 2 else n1) & (o0 if k & 1 else n0))

    # passo 2: grupos
    arit = L[4] | L[5]
    logica = L[6] | L[7]
    mem = L[14]
    # subfuncoes do MEM (bit 10 = RAM, bits 9..8 = 00 grava, 01 le, 10 carrega)
    nf2, nf1, nf0 = NOT(f2), NOT(f1), NOT(f0)
    m_grava = mem & nf1 & nf0
    m_le = mem & nf1 & f0
    m_carrega = mem & f1 & nf0

    s = Sinais()
    s.A_WE = (L[0] | L[1] | L[3] | (arit & NOT(f3)) | logica | L[13] | m_le)
    s.A_SRC0 = L[1] | L[3] | L[13] | mem                 # 01 memoria, 11 teclado
    s.A_SRC1 = arit | logica | L[13]                    # 10 ULA, 11 teclado
    s.MEM_VID = mem & nf2                               # memoria = VRAM
    s.RAM_WE = L[2] | (m_grava & f2)
    s.END_SRC0 = L[3]                                   # 01: endereco = A
    s.END_SRC1 = mem                                    # 10: endereco = ponteiro
    s.B_IMED = L[5] | L[7]
    s.SUB = arit & f0
    s.USA_C = arit & f1
    s.SHR = arit & f2
    s.LOGICA = logica
    s.Z_WE = arit | logica
    s.C_WE = arit
    s.SALTO = L[8]
    s.SE_Z = L[9]
    s.SE_NZ = L[10]
    s.SE_C = L[11]
    s.SE_NC = L[12]
    s.TEC_RD = L[13]
    s.VID_WR = m_grava & nf2
    s.CUR_INC = m_grava & nf2
    s.CUR_LD = m_carrega & nf2
    s.PTR_LD = m_carrega & f2
    s.PTR_INC = mem & f2 & nf1                          # STP e LDP
    return s


def toma_salto(s, z, c):
    """Logica de salto (arquivo 14)."""
    return (s.SALTO | (s.SE_Z & z) | (s.SE_NZ & NOT(z)) |
            (s.SE_C & c) | (s.SE_NC & NOT(c)))


# ============================================================
# DISPLAY 32 x 32 de 1 bit: VRAM de 128 bytes (arquivo 18)
# O cursor que a CPU usa e o registrador-ponteiro de 7 bits (arquivo 21).
# ============================================================

class Display:
    MEIO_BLOCO = (" ", "▀", "▄", "█")

    def __init__(self):
        self.vram = bytearray(128)
        self.ajuda = "W/S andar  A/D girar  M mapa  Q desliga"   # so texto do terminal

    def le(self, x, y):
        return (self.vram[(x << 2) | (y >> 3)] >> (y & 7)) & 1

    def mostrar(self, rodape=""):
        # 2 linhas de pixels por caractere e cada pixel com 2 caracteres
        # de largura, para a imagem ficar quadrada no terminal
        out = ["\x1b[H+", "-" * 64, "+\n"]
        for y in range(0, 32, 2):
            out.append("|")
            for x in range(32):
                out.append(self.MEIO_BLOCO[self.le(x, y) | (self.le(x, y + 1) << 1)] * 2)
            out.append("|\n")
        out.append("+" + "-" * 64 + "+\n")
        out.append(rodape.ljust(66) + "\n")
        out.append(self.ajuda + "\n")
        sys.stdout.write("".join(out))
        sys.stdout.flush()


# ============================================================
# TECLADO (no PC: le o terminal SEM esperar, como a trava de evento do
# hardware: cada tecla apertada e entregue uma unica vez; sem tecla = 0)
# ============================================================

class Teclado:
    MAPA_TECLAS = {"w": 1, "s": 2, "a": 4, "d": 8, "m": 16}

    def __init__(self):
        self._antigo = None

    def iniciar(self):
        try:
            import termios
            import tty
            fd = sys.stdin.fileno()
            self._antigo = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except (ImportError, OSError, ValueError, AttributeError):
            self._antigo = None

    def terminar(self):
        if self._antigo is not None:
            import termios
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._antigo)
            self._antigo = None

    def ler(self):
        """Junta (OR) todas as teclas apertadas desde a ultima leitura."""
        v = 0
        while True:
            k = self._tecla()
            if k is None:
                return v
            if k in ("q", "\x1b", "\x03"):
                raise KeyboardInterrupt
            v |= self.MAPA_TECLAS.get(k, 0)

    def _tecla(self):
        """Uma tecla pendente, ou None se nao ha nenhuma."""
        try:
            import msvcrt
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return {"H": "w", "P": "s", "K": "a", "M": "d"}.get(msvcrt.getwch(), "")
            return ch.lower()
        except ImportError:
            pass
        try:
            import select
            if not select.select([sys.stdin], [], [], 0)[0]:
                return None
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    return {"[A": "w", "[B": "s", "[D": "a", "[C": "d"}.get(sys.stdin.read(2), "")
                return "q"
            return ch.lower()
        except (OSError, ValueError):
            return None


# ============================================================
# O HARDWARE
# ============================================================

class Computador:

    def __init__(self):
        self.rom = [0] * 2048
        self.ram = bytearray(random.getrandbits(8) for _ in range(256))
        self.ula = ULA()
        self.display = Display()
        self.teclado = Teclado()
        self.a = 0
        self.pc = 0
        self.z = 0
        self.c = 0
        self.ponteiro = random.getrandbits(8)   # liga com lixo
        self.cursor = 0                          # zerado pelo /RST
        self.ciclos = 0              # instrucoes executadas
        self.clocks = 0              # pulsos de CLOCK gastos (instrucoes + extras)
        self.ciclos_quadro = 0
        self.clocks_quadro = 0
        self.rodape = ""
        self.vram_mudou = False
        self.ultima_tela = 0.0
        self.ultimo_quadro = 0.0
        self.alvo_ns = time.perf_counter_ns()   # "relogio" do hardware simulado
        # rastro: valores de todos os barramentos da ultima instrucao
        # (desligado por padrao; o esquema interativo liga no modo debug)
        self.rastrear = False
        self.rastro = None

    # --------------------------------------------------------
    # Atrasos em CLOCKs. O Python nao consegue dormir microssegundos,
    # entao o tempo devido e acumulado e esperado em blocos de >= 1 ms.
    # Se o simulador ja estiver mais lento que o hardware, nao espera.
    # --------------------------------------------------------
    def _gastar_clocks(self, n):
        if not n:
            return
        self.clocks += n
        self.alvo_ns += int(n * CLOCK_US * 1000)
        agora = time.perf_counter_ns()
        if self.alvo_ns < agora:
            self.alvo_ns = agora
        elif self.alvo_ns - agora >= 1_000_000:
            time.sleep((self.alvo_ns - agora) / 1e9)

    def gravar_rom(self, palavras):
        if len(palavras) > 2048:
            raise ValueError("programa nao cabe na ROM")
        for i, p in enumerate(palavras):
            self.rom[i] = p & 0xFFFF

    # --------------------------------------------------------
    # Tela do simulador (o painel real varre a VRAM sozinho)
    # --------------------------------------------------------
    def _quadro_completo(self):
        self._gastar_clocks(CLOCKS_EXTRA_DISPLAY)
        instr = self.ciclos - self.ciclos_quadro
        clocks = self.clocks - self.clocks_quadro
        self.ciclos_quadro = self.ciclos
        self.clocks_quadro = self.clocks
        self.rodape = "quadro: {} instr = {} x CLOCK = {:.0f} ms (CLOCK={}us)".format(
            instr, clocks, clocks * CLOCK_US / 1000, CLOCK_US)
        self.ultimo_quadro = time.perf_counter()
        self._mostrar()

    def _mostrar(self):
        self.display.mostrar(self.rodape)
        self.vram_mudou = False
        self.ultima_tela = time.perf_counter()

    def _talvez_mostrar(self):
        agora = time.perf_counter()
        if (self.vram_mudou and agora - self.ultima_tela >= TELA_S
                and agora - self.ultimo_quadro >= 0.5):
            self.rodape = "{} instr = {} x CLOCK desde o inicio (CLOCK={}us)".format(
                self.ciclos, self.clocks, CLOCK_US)
            self._mostrar()

    # --------------------------------------------------------
    # Um ciclo de instrucao: busca, decodifica, executa
    # --------------------------------------------------------
    def passo(self):
        palavra = self.rom[self.pc]
        op = palavra >> 12
        f = (palavra >> 8) & 0xF
        n = palavra & 0xFF
        destino = palavra & 0x7FF
        s = decodifica(op, f)
        self.ciclos += 1
        self._gastar_clocks(CLOCKS_POR_INSTRUCAO)

        # ---- metade alta: tudo o que e combinacional estabiliza ----
        # endereco da RAM: mux 4x1 (00 N, 01 A, 10 ponteiro)
        end = mux4_n(s.END_SRC1, s.END_SRC0, n, self.a, self.ponteiro, 0)
        le_ram = ((s.A_WE & s.A_SRC0 & NOT(s.A_SRC1) & NOT(s.MEM_VID)) |
                  ((s.Z_WE) & NOT(s.B_IMED)))
        dado_ram = self.ram[end]
        if le_ram:
            self._gastar_clocks(CLOCKS_EXTRA_LEITURA)
        dado_vram = self.display.vram[self.cursor]
        # memoria que vai para A: mux 2x1 (RAM ou VRAM)
        memoria = mux2_n(s.MEM_VID, dado_ram, dado_vram)
        # operando B da ULA: mux 2x1 (RAM ou N)
        b = mux2_n(s.B_IMED, dado_ram, n)
        r, z, c = self.ula.calcula(self.a, b, s.SUB, s.USA_C, s.SHR,
                                   s.LOGICA, f, self.c)
        teclado = self.teclado.ler() if s.TEC_RD else 0
        novo_a = mux4_n(s.A_SRC1, s.A_SRC0, n, memoria, r, teclado)
        toma = toma_salto(s, self.z, self.c)
        pc_mais_1 = incrementa(self.pc, 11)
        if self.rastrear:
            self.rastro = dict(
                pc=self.pc, palavra=palavra, op=op, f=f, n=n, destino=destino,
                sinais=s, end=end, le_ram=le_ram, dado_ram=dado_ram,
                dado_vram=dado_vram, memoria=memoria, b=b, r=r, z_novo=z,
                c_novo=c, teclado=teclado, novo_a=novo_a, toma=toma,
                pc_mais_1=pc_mais_1, prox_pc=destino if toma else pc_mais_1,
                a=self.a, z=self.z, c=self.c, ponteiro=self.ponteiro,
                cursor=self.cursor, ula=dict(self.ula.interno))

        # ---- metade baixa: pulsos de escrita (RAM e VRAM) ----
        if s.RAM_WE:
            self._gastar_clocks(CLOCKS_EXTRA_GRAVACAO)
            self.ram[end] = self.a
        quadro = False
        if s.VID_WR:
            self._gastar_clocks(CLOCKS_EXTRA_GRAVACAO)
            self.display.vram[self.cursor] = self.a
            self.vram_mudou = True
            quadro = self.cursor == 127

        # ---- borda de subida: registradores gravam juntos ----
        a_antigo = self.a
        if s.A_WE:
            self.a = novo_a
        if s.Z_WE:
            self.z = z
        if s.C_WE:
            self.c = c
        if s.PTR_LD:
            self.ponteiro = a_antigo
        elif s.PTR_INC:
            self.ponteiro = incrementa(self.ponteiro, 8)
        if s.CUR_LD:
            self.cursor = a_antigo & 0x7F
        elif s.CUR_INC:
            self.cursor = incrementa(self.cursor, 7)
        self.pc = destino if toma else pc_mais_1

        if quadro:
            self._quadro_completo()
        elif self.vram_mudou and (self.ciclos & 255) == 0:
            self._talvez_mostrar()

    def ligar(self):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
        import os
        os.system("")                          # ANSI no console do Windows
        sys.stdout.write("\x1b[2J\x1b[?25l")
        self.teclado.iniciar()
        try:
            while True:
                self.passo()
        except KeyboardInterrupt:
            pass
        finally:
            self.teclado.terminar()
            sys.stdout.write("\x1b[?25h\n")


# ============================================================
# MONTADOR (ferramenta do PC que "grava" a ROM; nao e hardware)
#
# Sintaxe:
#   ROTULO:            marca um endereco da ROM
#   .ram NOME 0x20     da nome a um endereco da RAM (so no texto;
#                      na ROM vai o numero fixo)
#   OP operando        ; comentario
#   LOGI tabela n      forma generica do LOG (tabela = 0b1000 etc.)
# Numeros: 12, 0x0C, 0b1100
# ============================================================

def montar(fonte):
    return montar_detalhado(fonte)["rom"]


def montar_detalhado(fonte):
    """Igual a montar(), mas devolve tambem de que linha do texto veio cada
    palavra e os enderecos dos rotulos:
    {"rom": [...], "linhas": [num_linha por endereco], "rotulos": {nome: end}}"""
    nomes = {}
    rotulos = {}
    linhas = []
    pc = 0
    for num, linha in enumerate(fonte.splitlines(), 1):
        linha = linha.split(";")[0].strip()
        if not linha:
            continue
        if linha.startswith(".ram"):
            _, nome, valor = linha.split()
            nomes[nome] = int(valor, 0)
            continue
        while ":" in linha:
            rotulo, linha = linha.split(":", 1)
            nomes[rotulo.strip()] = pc
            rotulos[rotulo.strip()] = pc
            linha = linha.strip()
        if linha:
            linhas.append((num, linha.split()))
            pc += 1

    def valor(tok, num, limite):
        if tok in nomes:
            v = nomes[tok]
        else:
            try:
                v = int(tok, 0)
            except ValueError:
                raise SyntaxError("linha {}: nome desconhecido '{}'".format(num, tok))
        if not 0 <= v <= limite:
            raise SyntaxError("linha {}: operando fora de faixa {}".format(num, v))
        return v

    rom = []
    for num, partes in linhas:
        nome = partes[0].upper()
        if nome not in INSTRUCOES:
            raise SyntaxError("linha {}: instrucao '{}'".format(num, nome))
        op, f, tipo = INSTRUCOES[nome]
        args = partes[1:]
        esperado = {"": 0, "n": 1, "m": 1, "e": 1, "tn": 2, "tm": 2}[tipo]
        if len(args) != esperado:
            raise SyntaxError("linha {}: {} precisa de {} operando(s)".format(num, nome, esperado))
        if tipo == "e":
            palavra = (op << 12) | valor(args[0], num, 0x7FF)
        elif tipo in ("tn", "tm"):
            palavra = (op << 12) | (valor(args[0], num, 0xF) << 8) | valor(args[1], num, 0xFF)
        elif tipo in ("n", "m"):
            palavra = (op << 12) | (f << 8) | valor(args[0], num, 0xFF)
        else:
            palavra = (op << 12) | (f << 8)
        rom.append(palavra)
    return {"rom": rom, "linhas": [num for num, _ in linhas], "rotulos": rotulos}


_NOMES_ARIT = {0b0000: "ADD", 0b0001: "SUB", 0b0010: "ADC", 0b0011: "SBC",
               0b1001: "CMP", 0b0100: "SHR"}
_NOMES_LOG = {T_AND: "AND", T_OR: "OR", T_XOR: "XOR"}
_NOMES_MEM = {0b0000: "VOUT", 0b0001: "VIN", 0b0010: "VPOS",
              0b0100: "STP", 0b0101: "LDP", 0b0110: "PTR"}


def desmontar(palavra):
    """Palavra de 16 bits -> texto em assembly (o inverso de montar)."""
    op, f, n = palavra >> 12, (palavra >> 8) & 0xF, palavra & 0xFF
    if op in (OP_JMP, OP_JZ, OP_JNZ, OP_JC, OP_JNC):
        nome = {OP_JMP: "JMP", OP_JZ: "JZ", OP_JNZ: "JNZ", OP_JC: "JC", OP_JNC: "JNC"}[op]
        return "{} 0x{:03X}".format(nome, palavra & 0x7FF)
    if op == OP_LDI:
        return "LDI {}".format(n)
    if op in (OP_LD, OP_ST):
        return "{} 0x{:02X}".format("LD" if op == OP_LD else "ST", n)
    if op == OP_LDR:
        return "LDR"
    if op == OP_IN:
        return "IN"
    if op == OP_MEM:
        return _NOMES_MEM.get(f, "MEM {:04b}".format(f))
    if op in (OP_ARIT, OP_ARITI):
        if f == 0b0100:
            return "SHR"
        nome = _NOMES_ARIT.get(f, "ARIT {:04b}".format(f))
        return "{}I {}".format(nome, n) if op == OP_ARITI else "{} 0x{:02X}".format(nome, n)
    if op in (OP_LOG, OP_LOGI):
        if op == OP_LOGI and f == T_TST:
            return "TST"
        if op == OP_LOGI and f == T_NOT:
            return "NOT"
        nome = _NOMES_LOG.get(f)
        if nome is None:
            return "{} 0b{:04b} {}".format("LOGI" if op == OP_LOGI else "LOG", f, n)
        return "{}I {}".format(nome, n) if op == OP_LOGI else "{} 0x{:02X}".format(nome, n)
    return "(livre)"


class ListaBinaria(list):
    """Lista normal que, no print, mostra os textos com aspas duplas."""
    def __repr__(self):
        return "[" + ", ".join('"{}"'.format(s) for s in self) + "]"


def montar_binario(fonte):
    """Igual a montar(), mas cada palavra vem como texto de 16 bits,
    separado nos campos da instrucao: opcode, F, operando.
    Ex.: ST 1 -> "0010 0000 00000001"."""
    lista = ListaBinaria()
    for palavra in montar(fonte):
        b = format(palavra, "016b")
        lista.append("{} {} {}".format(b[0:4], b[4:8], b[8:16]))
    return lista
