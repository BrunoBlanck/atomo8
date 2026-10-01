# -*- coding: utf-8 -*-
"""
TETRIS - PROGRAMA DA ROM (display 32 x 32)

Mesmo hardware e mesmo conjunto de instrucoes do doom.py e do bola.py;
so troca o que vai gravado na ROM. Nenhuma peca nova.

------------------------------------------------------------------
TELA
------------------------------------------------------------------
  x = 0 e x = 21 : paredes do poco
  x = 1..20      : poco de 10 x 16 celulas, cada celula = 2 x 2 pixels
                   (celula c, linha r -> pixels x = 2c+1, 2c+2 e y = 2r, 2r+1)
  x = 22..31     : painel. Em cima, a proxima peca; embaixo, as linhas (00..99)

------------------------------------------------------------------
TECLAS
------------------------------------------------------------------
  A / D (setas) move   W (seta p/ cima) gira   S (seta p/ baixo) desce 1
  M solta a peca ate o fundo

------------------------------------------------------------------
MAPA DA RAM
------------------------------------------------------------------
  0x00..0x2A variaveis (abaixo, nas linhas .ram)
  0x30 CEL   : 4 celulas da peca na tela (x, y, x, y...)
  0x38 NOV   : 4 celulas da tentativa (movida ou girada)
  0x40 COL   : poco, 2 bytes por coluna: COL[2c] linhas 0..7, COL[2c+1] 8..15
  0x60 BIT   : 1 << n (n = 0..7)
  0x68 M2    : mascara da celula no byte da VRAM (3, 12, 48, 192)
  0x70 DUP   : 4 bits -> 8 bits dobrados (cada celula vira 2 pixels)
  0x80 XT    : endereco da VRAM da coluna c = 8c + 4 (c = 0..14)
  0x90 FORMA : 7 pecas x 4 celulas, cada uma = x << 2 | y
  0xB0 KT    : tamanho - 1 da caixa de giro (I = 3, O = 1, outras 2)
  0xC0 FONTE : 10 digitos x 3 colunas (ja com a moldura 0x81)
  0xFF       : lixo de quando liga = semente do sorteio

------------------------------------------------------------------
IDEIAS
------------------------------------------------------------------
  1) O poco fica na RAM em COLUNAS (16 bits = 16 linhas). AND das 10
     colunas = linhas cheias de uma vez so (20 leituras).
  2) Tirar a linha r de uma coluna: bits acima de r sobem 1
     ((v AND LO) << 1), bits abaixo ficam (v AND HI).
  3) A peca e desenhada com XOR (igual a bola): desenhar de novo apaga.
     So o poco inteiro e redesenhado, e so quando some uma linha.
  4) Girar = (x, y) -> (y, K - x) dentro da caixa da peca.
  5) Sem CALL/RET: cada rotina guarda "para onde voltar" numa variavel
     (RTEN, RTES, RAPL, RDSN, RCAR, RDES) e termina num CMPI / JZ.
  6) Sorteio: LFSR de 8 bits (SHR + XORI 0xB8), girado a cada volta do
     laco principal; semente = lixo da RAM.
"""

from hardware import Computador, montar, montar_binario

PROGRAMA = """
; ================= VARIAVEIS NA RAM =================
.ram T      0x00
.ram V      0x01
.ram X      0x02
.ram Y      0x03
.ram END    0x04
.ram M      0x05
.ram I      0x06
.ram DX     0x07
.ram DY     0x08
.ram PX     0x09
.ram PY     0x0A
.ram NPX    0x0B
.ram NPY    0x0C
.ram K      0x0D
.ram PECA   0x0E
.ram PROX   0x0F
.ram SORTE  0x10
.ram TECLAS 0x11
.ram TEMPO  0x12
.ram VEL    0x13
.ram DEZ    0x14
.ram UNI    0x15
.ram FALHOU 0x16
.ram APAGA  0x17
.ram FL     0x18
.ram FH     0x19
.ram LIN    0x1A
.ram LO     0x1B
.ram HI     0x1C
.ram RTEN   0x1D
.ram RTES   0x1E
.ram RAPL   0x1F
.ram RDSN   0x20
.ram RCAR   0x21
.ram D0     0x22
.ram D1     0x23
.ram D2     0x24
.ram D3     0x25
.ram VEND   0x26
.ram RDES   0x27
.ram HEND   0x28
.ram PQ     0x29

.ram CEL    0x30
.ram C0X    0x30
.ram C0Y    0x31
.ram C1X    0x32
.ram C1Y    0x33
.ram C2X    0x34
.ram C2Y    0x35
.ram C3X    0x36
.ram C3Y    0x37
.ram NOV    0x38
.ram N0X    0x38
.ram N0Y    0x39
.ram N1X    0x3A
.ram N1Y    0x3B
.ram N2X    0x3C
.ram N2Y    0x3D
.ram N3X    0x3E
.ram N3Y    0x3F
.ram COL    0x40
.ram COLFIM 0x54
.ram BIT    0x60
.ram M2     0x68
.ram DUP    0x70
.ram XT     0x80
.ram FORMA  0x90
.ram KT     0xB0
.ram FONTE  0xC0
.ram LIXO   0xFF

; ================= LIGA: SEMENTE E TABELAS =================
INICIO:
    LD   LIXO        ; RAM liga com lixo: semente do sorteio
    ORI  1           ; nunca 0 (o LFSR pararia)
    ST   SORTE

    LDI  BIT         ; BIT[n] = 1 << n
    PTR
    LDI  1
BI_L:
    STP
    ST   T
    ADD  T           ; A = 2A, C = 1 depois do 128
    JNC  BI_L

    LDI  XT          ; XT[c] = 8c + 4
    PTR
    LDI  4
XT_L:
    STP
    ADDI 8
    CMPI 124
    JNZ  XT_L

    LDI  M2
    PTR
    LDI  3
    STP
    LDI  12
    STP
    LDI  48
    STP
    LDI  192
    STP

    LDI  DUP         ; 4 bits -> cada bit vira 2 pixels
    PTR
    LDI  0
    STP
    LDI  3
    STP
    LDI  12
    STP
    LDI  15
    STP
    LDI  48
    STP
    LDI  51
    STP
    LDI  60
    STP
    LDI  63
    STP
    LDI  192
    STP
    LDI  195
    STP
    LDI  204
    STP
    LDI  207
    STP
    LDI  240
    STP
    LDI  243
    STP
    LDI  252
    STP
    LDI  255
    STP

    LDI  FORMA       ; celula = x << 2 | y
    PTR
    LDI  1           ; I
    STP
    LDI  5
    STP
    LDI  9
    STP
    LDI  13
    STP
    LDI  0           ; O
    STP
    LDI  4
    STP
    LDI  1
    STP
    LDI  5
    STP
    LDI  4           ; T
    STP
    LDI  1
    STP
    LDI  5
    STP
    LDI  9
    STP
    LDI  4           ; S
    STP
    LDI  8
    STP
    LDI  1
    STP
    LDI  5
    STP
    LDI  0           ; Z
    STP
    LDI  4
    STP
    LDI  5
    STP
    LDI  9
    STP
    LDI  0           ; J
    STP
    LDI  1
    STP
    LDI  5
    STP
    LDI  9
    STP
    LDI  8           ; L
    STP
    LDI  1
    STP
    LDI  5
    STP
    LDI  9
    STP

    LDI  KT          ; caixa de giro: I O T S Z J L
    PTR
    LDI  3
    STP
    LDI  1
    STP
    LDI  2
    STP
    STP
    STP
    STP
    STP

    LDI  FONTE       ; digitos 3 x 5, colunas com a moldura (bits 0 e 7)
    PTR
    LDI  253         ; 0
    STP
    LDI  197
    STP
    LDI  253
    STP
    LDI  201         ; 1
    STP
    LDI  253
    STP
    LDI  193
    STP
    LDI  245         ; 2
    STP
    LDI  213
    STP
    LDI  221
    STP
    LDI  197         ; 3
    STP
    LDI  213
    STP
    LDI  253
    STP
    LDI  157         ; 4
    STP
    LDI  145
    STP
    LDI  253
    STP
    LDI  221         ; 5
    STP
    LDI  213
    STP
    LDI  245
    STP
    LDI  253         ; 6
    STP
    LDI  213
    STP
    LDI  245
    STP
    LDI  133         ; 7
    STP
    LDI  245
    STP
    LDI  141
    STP
    LDI  253         ; 8
    STP
    LDI  213
    STP
    LDI  253
    STP
    LDI  221         ; 9
    STP
    LDI  213
    STP
    LDI  253
    STP

; ================= TELA: PAREDES E MOLDURAS =================
    LDI  0
    VPOS
    LDI  128
    ST   I
LZ:
    LDI  0
    VOUT
    LD   I
    SUBI 1
    ST   I
    JNZ  LZ

    LDI  0           ; parede esquerda (x = 0)
    VPOS
    LDI  255
    VOUT
    VOUT
    VOUT
    VOUT
    LDI  84          ; parede direita (x = 21)
    VPOS
    LDI  255
    VOUT
    VOUT
    VOUT
    VOUT
    LDI  124         ; borda do painel (x = 31)
    VPOS
    LDI  255
    VOUT
    VOUT
    VOUT
    VOUT

    LDI  88          ; molduras de cima e de baixo (x = 22..30)
    ST   T
FR_L:
    LD   T
    VPOS
    LDI  0x81
    VOUT
    LD   T
    ADDI 3
    VPOS
    LDI  0x81
    VOUT
    LD   T
    ADDI 4
    ST   T
    CMPI 124
    JNZ  FR_L

; ================= NOVO JOGO =================
JOGO:
    LDI  COL         ; poco vazio
    PTR
    LDI  20
    ST   I
ZC:
    LDI  0
    STP
    LD   I
    SUBI 1
    ST   I
    JNZ  ZC
    LDI  0
    ST   DEZ
    ST   UNI
    LDI  40
    ST   VEL
SO_J:
    LD   SORTE       ; primeira "proxima peca"
    SHR
    JNC  SO_J1
    XORI 0xB8
SO_J1:
    ST   SORTE
    ANDI 7
    CMPI 7
    JZ   SO_J
    ST   PROX
    JMP  REDESENHA

; ================= LACO PRINCIPAL =================
LACO:
    LD   SORTE       ; gira o sorteio a cada volta
    SHR
    JNC  LA_S
    XORI 0xB8
LA_S:
    ST   SORTE
    LDI  40          ; espera curta (so A, sem RAM)
LA_E:
    SUBI 1
    JNZ  LA_E

    IN
    TST
    JZ   GRAV
    ST   TECLAS
    ANDI 4           ; A: esquerda
    JZ   K_DIR
    LDI  255
    ST   DX
    LDI  0
    ST   DY
    LDI  1
    ST   RTEN
    JMP  TENTA
K_DIR:
    LD   TECLAS
    ANDI 8           ; D: direita
    JZ   K_ROT
    LDI  1
    ST   DX
    LDI  0
    ST   DY
    LDI  2
    ST   RTEN
    JMP  TENTA
K_ROT:
    LD   TECLAS
    ANDI 1           ; W: gira
    JZ   K_BAIXO
    LDI  NOV         ; NOV = (PX + ry, PY + K - rx)
    PTR
    LDI  0
    ST   I
RO_L:
    LD   I
    ADDI CEL
    LDR
    SUB  PX
    ST   T           ; rx
    LD   I
    ADDI C0Y
    LDR
    SUB  PY          ; ry
    ADD  PX
    STP
    LD   K
    SUB  T
    ADD  PY
    STP
    LD   I
    ADDI 2
    ST   I
    CMPI 8
    JNZ  RO_L
    LD   PX
    ST   NPX
    LD   PY
    ST   NPY
    LDI  3
    ST   RTEN
    JMP  TENTA_NOV
K_BAIXO:
    LD   TECLAS
    ANDI 2           ; S: desce 1
    JNZ  DESCE
    LD   TECLAS
    ANDI 16          ; M: solta
    JNZ  DURO

GRAV:
    LD   TEMPO
    SUBI 1
    ST   TEMPO
    JNZ  LACO
DESCE:
    LD   VEL
    ST   TEMPO
    LDI  0
    ST   DX
    LDI  1
    ST   DY
    LDI  4
    ST   RTEN
    JMP  TENTA
DESCEU:
    LD   FALHOU
    TST
    JNZ  FIXA        ; bateu embaixo: a peca para
    JMP  LACO

; ================= SOLTA: desce ate bater, desenha 1 vez =================
DURO:
    LDI  0
    ST   DX
    LDI  1
    ST   DY
DU_L:
    LDI  2
    ST   RDES
    JMP  DESLOCA
RS2:
    LDI  3
    ST   RTES
    JMP  TESTA
RT3:
    LD   FALHOU
    TST
    JNZ  DU_FIM
    LD   DY
    ADDI 1
    ST   DY
    JMP  DU_L
DU_FIM:
    LD   DY
    SUBI 1
    ST   DY
    JZ   FIXA
    LDI  3
    ST   RDES
    JMP  DESLOCA
RS3:
    LDI  4
    ST   RAPL
    JMP  APLICA
RA4:
    JMP  FIXA

; ================= TENTA: desloca, testa e aplica =================
; entra com DX, DY (ou em TENTA_NOV com NOV pronto). Volta por RTEN.
TENTA:
    LDI  1
    ST   RDES
    JMP  DESLOCA
RS1:
TENTA_NOV:
    LDI  2
    ST   RTES
    JMP  TESTA
RT2:
    LD   FALHOU
    TST
    JNZ  TN_RET
    LDI  3
    ST   RAPL
    JMP  APLICA
RA3:
TN_RET:
    LD   RTEN
    CMPI 1
    JZ   K_DIR
    CMPI 2
    JZ   K_ROT
    CMPI 3
    JZ   K_BAIXO
    JMP  DESCEU

; ================= DESLOCA: NOV = CEL + (DX, DY) =================
DESLOCA:
    LDI  NOV
    PTR
    LDI  0
    ST   I
DE_L:
    LD   I
    ADDI CEL
    LDR
    ADD  DX
    STP
    LD   I
    ADDI C0Y
    LDR
    ADD  DY
    STP
    LD   I
    ADDI 2
    ST   I
    CMPI 8
    JNZ  DE_L
    LD   PX
    ADD  DX
    ST   NPX
    LD   PY
    ADD  DY
    ST   NPY
    LD   RDES
    CMPI 1
    JZ   RS1
    CMPI 2
    JZ   RS2
    JMP  RS3

; ================= TESTA: NOV bate em parede, fundo ou poco? =================
TESTA:
    LDI  NOV
    PTR
    LDI  4
    ST   I
TS_L:
    LDP
    ST   X
    CMPI 10          ; x >= 10 (ou -1 = 255): parede
    JC   TS_FALHA
    LDP
    ST   Y
    CMPI 16          ; y >= 16: fundo
    JC   TS_FALHA
    ANDI 7
    ADDI BIT
    LDR
    ST   M           ; M = 1 << (y AND 7)
    LD   Y
    SHR
    SHR
    SHR
    ADD  X
    ADD  X
    ADDI COL
    LDR              ; A = COL[2x + y/8]
    AND  M
    JNZ  TS_FALHA
    LD   I
    SUBI 1
    ST   I
    JNZ  TS_L
    LDI  0
    ST   FALHOU
    JMP  TS_RET
TS_FALHA:
    LDI  1
    ST   FALHOU
TS_RET:
    LD   RTES
    CMPI 1
    JZ   RT1
    CMPI 2
    JZ   RT2
    JMP  RT3

; ================= APLICA: apaga CEL, CEL = NOV, desenha CEL =================
APLICA:
    LD   APAGA
    TST
    JZ   AP_COPIA
    LDI  1
    ST   RDSN
    JMP  DESENHA
RD1:
AP_COPIA:
    LD   N0X
    ST   C0X
    LD   N0Y
    ST   C0Y
    LD   N1X
    ST   C1X
    LD   N1Y
    ST   C1Y
    LD   N2X
    ST   C2X
    LD   N2Y
    ST   C2Y
    LD   N3X
    ST   C3X
    LD   N3Y
    ST   C3Y
    LD   NPX
    ST   PX
    LD   NPY
    ST   PY
    LDI  2
    ST   RDSN
    JMP  DESENHA
RD2:
    LDI  1
    ST   APAGA
    LD   RAPL
    CMPI 1
    JZ   RA1
    CMPI 2
    JZ   RA2
    CMPI 3
    JZ   RA3
    JMP  RA4

; ================= DESENHA: inverte (XOR) as 4 celulas de CEL =================
DESENHA:
    LDI  CEL
    PTR
    LDI  4
    ST   I
DS_L:
    LDP
    ADDI XT
    LDR
    ST   END         ; END = 8x + 4
    LDP
    ST   Y
    SHR
    SHR
    ADD  END
    ST   END         ; + pagina (y / 4)
    LD   Y
    ANDI 3
    ADDI M2
    LDR
    ST   M           ; 2 pixels da celula no byte
    LD   END
    VPOS
    VIN
    XOR  M
    VOUT             ; coluna da esquerda
    LD   END
    ADDI 4
    VPOS
    VIN
    XOR  M
    VOUT             ; coluna da direita
    LD   I
    SUBI 1
    ST   I
    JNZ  DS_L
    LD   RDSN
    CMPI 1
    JZ   RD1
    JMP  RD2

; ================= CARREGA: NOV = FORMA[PQ] + (NPX, NPY) =================
CARREGA:
    LD   PQ
    ADD  PQ
    ST   T
    ADD  T
    ADDI FORMA
    ST   END
    LDI  NOV
    PTR
    LDI  4
    ST   I
CA_L:
    LD   END
    LDR
    ST   V
    SHR
    SHR
    ADD  NPX
    STP
    LD   V
    ANDI 3
    ADD  NPY
    STP
    LD   END
    ADDI 1
    ST   END
    LD   I
    SUBI 1
    ST   I
    JNZ  CA_L
    LD   RCAR
    CMPI 1
    JZ   RC1
    JMP  RC2

; ================= FIXA: a peca vira poco =================
FIXA:
    LDI  0
    ST   I
FX_L:
    LD   I
    ADDI CEL
    LDR
    ST   X
    LD   I
    ADDI C0Y
    LDR
    ST   Y
    ANDI 7
    ADDI BIT
    LDR
    ST   M
    LD   Y
    SHR
    SHR
    SHR
    ADD  X
    ADD  X
    ADDI COL
    ST   END
    PTR
    LD   END
    LDR
    OR   M
    STP              ; COL[2x + y/8] |= M
    LD   I
    ADDI 2
    ST   I
    CMPI 8
    JNZ  FX_L

    LD   0x40        ; linhas cheias 0..7 = AND das 10 colunas
    AND  0x42
    AND  0x44
    AND  0x46
    AND  0x48
    AND  0x4A
    AND  0x4C
    AND  0x4E
    AND  0x50
    AND  0x52
    ST   FL
    LD   0x41        ; linhas cheias 8..15
    AND  0x43
    AND  0x45
    AND  0x47
    AND  0x49
    AND  0x4B
    AND  0x4D
    AND  0x4F
    AND  0x51
    AND  0x53
    ST   FH
    OR   FL
    JZ   NOVA

; ---- tira as linhas cheias 0..7 (de cima para baixo) ----
    LDI  0
    ST   LIN
CL_L:
    LD   FL
    SHR
    ST   FL
    JNC  CL_PROX
    LD   LIN
    ADDI BIT
    LDR
    ST   M
    SUBI 1
    ST   LO          ; bits acima da linha (sobem 1)
    ADD  M
    NOT
    ST   HI          ; bits abaixo da linha (ficam)
    LDI  COL
    ST   END
CLB_L:
    LD   END
    LDR
    ST   V
    AND  LO
    ST   T
    ADD  T
    ST   T
    LD   V
    AND  HI
    OR   T
    ST   T
    LD   END
    PTR
    LD   T
    STP
    LD   END
    ADDI 2
    ST   END
    CMPI COLFIM
    JNZ  CLB_L
    LD   UNI         ; conta a linha
    ADDI 1
    ST   UNI
    CMPI 10
    JNZ  CL_V
    LDI  0
    ST   UNI
    LD   DEZ
    ADDI 1
    ST   DEZ
    CMPI 10
    JNZ  CL_V
    LDI  0
    ST   DEZ
CL_V:
    LD   VEL         ; acelera ate 8
    CMPI 9
    JNC  CL_PROX
    SUBI 1
    ST   VEL
CL_PROX:
    LD   LIN
    ADDI 1
    ST   LIN
    CMPI 8
    JNZ  CL_L

; ---- tira as linhas cheias 8..15 (o bit 7 do byte de cima desce) ----
    LDI  0
    ST   LIN
CH_L:
    LD   FH
    SHR
    ST   FH
    JNC  CH_PROX
    LD   LIN
    ADDI BIT
    LDR
    ST   M
    SUBI 1
    ST   LO
    ADD  M
    NOT
    ST   HI
    LDI  COL
    ST   END
CHB_L:
    LD   END
    ADDI 1
    ST   HEND
    LDR
    ST   V           ; V = byte de baixo (linhas 8..15)
    AND  LO
    ST   T
    ADD  T
    ST   T           ; T = (V AND LO) << 1
    LD   END
    LDR
    ST   X           ; X = byte de cima (linhas 0..7)
    ANDI 128
    JZ   CH_SC
    LD   T
    ORI  1           ; linha 7 desce para a linha 8
    ST   T
CH_SC:
    LD   V
    AND  HI
    OR   T
    ST   T
    LD   HEND
    PTR
    LD   T
    STP
    LD   X
    ADD  X
    ST   T
    LD   END
    PTR
    LD   T
    STP              ; byte de cima << 1
    LD   END
    ADDI 2
    ST   END
    CMPI COLFIM
    JNZ  CHB_L
    LD   UNI
    ADDI 1
    ST   UNI
    CMPI 10
    JNZ  CH_V
    LDI  0
    ST   UNI
    LD   DEZ
    ADDI 1
    ST   DEZ
    CMPI 10
    JNZ  CH_V
    LDI  0
    ST   DEZ
CH_V:
    LD   VEL
    CMPI 9
    JNC  CH_PROX
    SUBI 1
    ST   VEL
CH_PROX:
    LD   LIN
    ADDI 1
    ST   LIN
    CMPI 8
    JNZ  CH_L

; ================= REDESENHA O POCO (10 colunas x 4 paginas) =================
REDESENHA:
    LDI  COL
    ST   END
    LDI  4
    ST   VEND
RD_L:
    LD   END
    LDR
    ST   V
    ANDI 15
    ADDI DUP
    LDR
    ST   D0
    LD   V
    SHR
    SHR
    SHR
    SHR
    ADDI DUP
    LDR
    ST   D1
    LD   END
    ADDI 1
    LDR
    ST   V
    ANDI 15
    ADDI DUP
    LDR
    ST   D2
    LD   V
    SHR
    SHR
    SHR
    SHR
    ADDI DUP
    LDR
    ST   D3
    LD   VEND
    VPOS
    LD   D0          ; 4 paginas da coluna da esquerda...
    VOUT
    LD   D1
    VOUT
    LD   D2
    VOUT
    LD   D3
    VOUT
    LD   D0          ; ...e as mesmas na coluna da direita
    VOUT
    LD   D1
    VOUT
    LD   D2
    VOUT
    LD   D3
    VOUT
    LD   VEND
    ADDI 8
    ST   VEND
    LD   END
    ADDI 2
    ST   END
    CMPI COLFIM
    JNZ  RD_L

; ================= PLACAR: linhas em 2 digitos =================
PLACAR:
    LD   DEZ
    ADD  DEZ
    ADD  DEZ
    ADDI FONTE
    ST   END
    LDI  99          ; x = 24, pagina 3
    VPOS
    LD   END
    LDR
    VOUT
    LDI  103
    VPOS
    LD   END
    ADDI 1
    LDR
    VOUT
    LDI  107
    VPOS
    LD   END
    ADDI 2
    LDR
    VOUT
    LD   UNI
    ADD  UNI
    ADD  UNI
    ADDI FONTE
    ST   END
    LDI  115         ; x = 28, pagina 3
    VPOS
    LD   END
    LDR
    VOUT
    LDI  119
    VPOS
    LD   END
    ADDI 1
    LDR
    VOUT
    LDI  123
    VPOS
    LD   END
    ADDI 2
    LDR
    VOUT

; ================= NOVA PECA =================
NOVA:
    LD   PROX
    ST   PECA
SO_N:
    LD   SORTE
    SHR
    JNC  SO_N1
    XORI 0xB8
SO_N1:
    ST   SORTE
    ANDI 7
    CMPI 7
    JZ   SO_N
    ST   PROX

    LDI  92          ; limpa a previa (x = 23..30, pagina 0)
    ST   T
PV_L:
    LD   T
    VPOS
    LDI  0x81
    VOUT
    LD   T
    ADDI 4
    ST   T
    CMPI 124
    JNZ  PV_L

    LD   PROX        ; previa: celulas 11..14, linha 1
    ST   PQ
    LDI  11
    ST   NPX
    LDI  1
    ST   NPY
    LDI  1
    ST   RCAR
    JMP  CARREGA
RC1:
    LDI  0
    ST   APAGA
    LDI  1
    ST   RAPL
    JMP  APLICA
RA1:
    LD   PECA        ; peca no alto do poco
    ST   PQ
    LDI  3
    ST   NPX
    LDI  0
    ST   NPY
    LDI  2
    ST   RCAR
    JMP  CARREGA
RC2:
    LD   PECA
    ADDI KT
    LDR
    ST   K
    LDI  1
    ST   RTES
    JMP  TESTA
RT1:
    LD   FALHOU
    TST
    JNZ  FIM_JOGO    ; nao cabe: fim de jogo
    LDI  0
    ST   APAGA
    LDI  2
    ST   RAPL
    JMP  APLICA
RA2:
    LD   VEL
    ST   TEMPO
    JMP  LACO

; ================= FIM DE JOGO: enche o poco, espera uma tecla =================
FIM_JOGO:
    LDI  4
    VPOS
    LDI  80
    ST   I
FJ_L:
    LDI  255
    VOUT
    LD   I
    SUBI 1
    ST   I
    JNZ  FJ_L
    IN               ; descarta teclas antigas
FJ_E:
    IN
    TST
    JZ   FJ_E
    JMP  JOGO
"""


if __name__ == "__main__":
    pc = Computador()

    #print(montar_binario(PROGRAMA))

    pc.display.ajuda = "A/D mover  W girar  S descer  M soltar  Q desliga"
    pc.gravar_rom(montar(PROGRAMA))
    pc.ligar()
