# -*- coding: utf-8 -*-
"""
LABIRINTO 3D - PROGRAMA DA ROM (display 32 x 32)

Este arquivo contem SO o programa em assembly do hardware de hardware.py.
Nao ha logica em Python aqui: o texto e montado, gravado na ROM e o
computador e ligado. Sem tabelas e sem constantes: todos os numeros estao
fixos dentro das proprias instrucoes. Os nomes .ram so existem no texto;
na ROM vai o endereco numerico.

------------------------------------------------------------------
IDEIAS QUE DEIXAM TUDO RAPIDO E O HARDWARE MINIMO
------------------------------------------------------------------
  1) Labirinto 13 x 13 com a regra: nenhuma linha reta tem mais de 3
     celulas livres seguidas. A parede da frente fica sempre a no maximo
     3 celulas (F = 0, 1 ou 2): so 3 profundidades para analisar.

  2) 1 byte de RAM por celula: parede = 255 (0xFF), livre = 0.
       - consultar uma celula = LDR;
       - como parede e 0xFF, ANDI 2^d pega direto o "bit da profundidade d";
       - no mapa, ANDI 3 / 12 / 48 / 192 poe a celula na posicao certa do
         byte do display.
     Celula (x, y) fica no endereco 13*y + x. Andar = somar FW.

  3) Girar sem tabela: FW = passo para frente, LW = passo para a esquerda.
       girar a esquerda: (FW, LW) <- (LW, -FW)
       girar a direita : (FW, LW) <- (-LW, FW)

  4) Display: 32 colunas x 4 paginas = 128 bytes. Cada VOUT grava 1 byte
     (8 pixels em pe) e o cursor da VRAM avanca sozinho. TODA tela (3D,
     mapa, vitoria) escreve exatamente 128 bytes, entao o cursor volta a 0
     no fim de cada quadro sem precisar de VPOS.

  5) As faixas do 3D estao escritas por extenso: cada situacao ja tem os
     4 bytes da coluna dentro de LDI. Desenhar = LDI + VOUT, sem contas.

  6) Ao ligar, o labirinto vem compactado (1 bit por celula, 22 bytes) e
     um laco com LDR + SHR + STP o desenrola: 69 instrucoes na ROM em vez
     de 171. Bloco gerado por gerar_mapa.py.

------------------------------------------------------------------
MAPA DA RAM
------------------------------------------------------------------
  0x00..0xA8 : labirinto 13x13 (169 bytes)
  0xA9..0xAF : sobra do desenrolar (sem uso)
  0xB0..0xBE : variaveis
  0xC0..0xD5 : labirinto compactado (so usado ao ligar)
  0xD6..0xD8 : variaveis do desenrolar

------------------------------------------------------------------
FAIXAS DE PROFUNDIDADE (metade esquerda, coluna x = 0..15)
------------------------------------------------------------------
      coluna x :  0..4   5..9   10..12   13..15
      faixa    :   0      1       2        3 (sempre atras da parede)

  Analise da visao:
     LBE bit d = 1 se ha parede colada a ESQUERDA na profundidade d
     LBD bit d = 1 se ha parede colada a DIREITA  na profundidade d
     (bit d+1 = parede no fundo de uma abertura na profundidade d)
     F = profundidade da parede frontal (0, 1 ou 2)

  Desenho: coluna 0 a 31 em sequencia. Metade esquerda: faixas 0,1,2,3.
  Metade direita: faixas 3,2,1,0 (colunas espelhadas).
  Byte da coluna: bit 0 = pixel de cima da pagina. As paginas 2 e 3 sao
  as paginas 1 e 0 de cabeca para baixo (a parede e simetrica).
"""

from hardware import Computador, montar, montar_binario

PROGRAMA = """
; ================= VARIAVEIS NA RAM =================
.ram P     0xB0   ; celula do jogador (13*y + x)
.ram FW    0xB1   ; passo para frente   (+1, -1=255, +13, -13=243)
.ram LW    0xB2   ; passo para a esquerda (direita = -LW)
.ram Q     0xB3   ; celula sendo analisada
.ram T0    0xB4   ; temporario
.ram LBE   0xB5   ; bits de parede a esquerda por profundidade
.ram LBD   0xB6   ; bits de parede a direita por profundidade
.ram F     0xB7   ; profundidade da parede frontal (0..2)
.ram KEY   0xB8
.ram MAPA  0xB9   ; 1 = mostrando mapa
.ram BI    0xBA   ; mapa: celula (cx, 0) da coluna atual
.ram A0    0xBB   ; mapa: bytes das paginas 0, 1 e 2
.ram A1    0xBC
.ram A2    0xBD
.ram X     0xBE   ; vitoria: contador de colunas
.ram MSRC  0xD6   ; ligar: endereco do byte compactado (0xC0..0xD5)
.ram MBYTE 0xD7   ; ligar: byte compactado sendo desenrolado
.ram MCNT  0xD8   ; ligar: bits que faltam no byte

; ================= LIGA: GRAVA O LABIRINTO NA RAM =================
INICIO:
    ; labirinto compactado: bit k do byte j = celula 8*j + k (1 = parede)
    LDI  0b11111111   ; celulas   7..  0
    ST   0xC0
    LDI  0b10111111   ; celulas  15..  8
    ST   0xC1
    LDI  0b10001000   ; celulas  23.. 16
    ST   0xC2
    LDI  0b01000110   ; celulas  31.. 24
    ST   0xC3
    LDI  0b11000100   ; celulas  39.. 32
    ST   0xC4
    LDI  0b01010010   ; celulas  47.. 40
    ST   0xC5
    LDI  0b11111101   ; celulas  55.. 48
    ST   0xC6
    LDI  0b00101011   ; celulas  63.. 56
    ST   0xC7
    LDI  0b10001111   ; celulas  71.. 64
    ST   0xC8
    LDI  0b01101000   ; celulas  79.. 72
    ST   0xC9
    LDI  0b01000100   ; celulas  87.. 80
    ST   0xCA
    LDI  0b10101100   ; celulas  95.. 88
    ST   0xCB
    LDI  0b11100110   ; celulas 103.. 96
    ST   0xCC
    LDI  0b00111001   ; celulas 111..104
    ST   0xCD
    LDI  0b01110011   ; celulas 119..112
    ST   0xCE
    LDI  0b00010010   ; celulas 127..120
    ST   0xCF
    LDI  0b00010111   ; celulas 135..128
    ST   0xD0
    LDI  0b11001001   ; celulas 143..136
    ST   0xD1
    LDI  0b10001000   ; celulas 151..144
    ST   0xD2
    LDI  0b11110011   ; celulas 159..152
    ST   0xD3
    LDI  0b11111111   ; celulas 167..160
    ST   0xD4
    LDI  0b00000001   ; celulas 175..168
    ST   0xD5
    ; desenrola: cada bit vira 1 byte (parede = 255, livre = 0)
    LDI  0
    PTR              ; ponteiro = celula 0
    LDI  0xC0
    ST   MSRC
DESCOMPACTA:
    LD   MSRC
    LDR              ; A = byte compactado
    ST   MBYTE
    LDI  8
    ST   MCNT
DESC_BIT:
    LD   MBYTE
    SHR              ; C = bit da celula
    ST   MBYTE
    LDI  0           ; livre (LDI e ST nao mudam C)
    JNC  DESC_GRAVA
    LDI  255         ; parede
DESC_GRAVA:
    STP              ; RAM[ponteiro] = A, ponteiro + 1
    LD   MCNT
    SUBI 1
    ST   MCNT
    JNZ  DESC_BIT
    LD   MSRC
    ADDI 1
    ST   MSRC
    CMPI 0xD6
    JNZ  DESCOMPACTA

    LDI  14          ; jogador em (1,1) = 13*1 + 1
    ST   P
    LDI  13          ; olhando para o sul: frente +13
    ST   FW
    LDI  1           ; esquerda de quem olha para o sul = leste (+1)
    ST   LW
    LDI  0
    ST   MAPA

; ================= LACO PRINCIPAL =================
QUADRO:
    LD   MAPA
    CMPI 0
    JNZ  DESENHA_MAPA

; ---------- 1) analise da visao (no maximo 3 celulas) ----------
    LD   P
    ST   Q
    ADD  LW          ; profundidade 0
    LDR
    ANDI 1           ; parede = 255 -> sobra so o bit 0
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 1
    ST   LBD
    LD   Q
    ADD  FW
    ST   Q
    LDR
    CMPI 0
    JNZ  AN_F0
    LD   Q           ; profundidade 1
    ADD  LW
    LDR
    ANDI 2
    ADD  LBE
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 2
    ADD  LBD
    ST   LBD
    LD   Q
    ADD  FW
    ST   Q
    LDR
    CMPI 0
    JNZ  AN_F1
    LD   Q           ; profundidade 2 (a frente e parede com certeza)
    ADD  LW
    LDR
    ANDI 4
    ADD  LBE
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 4
    ADD  LBD
    ST   LBD
    LD   Q           ; laterais da parede frontal (fundo das aberturas)
    ADD  FW
    ST   Q
    ADD  LW
    LDR
    ANDI 8
    ADD  LBE
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 8
    ADD  LBD
    ST   LBD
    LDI  2
    ST   F
    JMP  DESENHO
AN_F0:               ; parede logo a frente: so falta o fundo das aberturas
    LD   Q
    ADD  LW
    LDR
    ANDI 2
    ADD  LBE
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 2
    ADD  LBD
    ST   LBD
    LDI  0
    ST   F
    JMP  DESENHO
AN_F1:
    LD   Q
    ADD  LW
    LDR
    ANDI 4
    ADD  LBE
    ST   LBE
    LD   Q
    SUB  LW
    LDR
    ANDI 4
    ADD  LBD
    ST   LBD
    LDI  1
    ST   F

; ---------- 2) desenho: 32 colunas x 4 bytes = 128 VOUT ----------
DESENHO:
; ----- lado esquerda, faixa 0 (x = 0..4) -----
    LD   LBE
    ANDI 3           ; bits 0 (parede) e 1 (parede no fundo da abertura)
    JZ   E0_VAZIA
    CMPI 2
    JZ   E0_FACE
    ; parede lateral (diagonal)
    LDI  1
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  128
    VOUT
    LDI  2
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  64
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  8
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  16
    VOUT
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  8
    VOUT
    JMP  E0_FIM
E0_FACE:
    ; parede vista pela abertura (T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  E0_FIM
E0_VAZIA:
    ; nada
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
E0_FIM:
; ----- lado esquerda, faixa 1 (x = 5..9) -----
    LD   F
    CMPI 0
    JNZ  E1_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  E1_FIM
E1_F0_N:
    LD   LBE
    ANDI 7          ; bits 0, 1 e 2
    CMPI 2
    JZ   E1_X_DIAG
    CMPI 3
    JZ   E1_X_DIAG
    CMPI 6
    JZ   E1_X_DIAG
    CMPI 7
    JZ   E1_X_DIAG
    CMPI 0
    JZ   E1_Z_Z
    CMPI 1
    JZ   E1_X_Z
    CMPI 4
    JZ   E1_XE_FACE
    ; quina no inicio, parede vista pela abertura
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    JMP  E1_FIM
E1_X_DIAG:
    ; quina no inicio, parede lateral
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    LDI  64
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  2
    VOUT
    LDI  128
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  1
    VOUT
    LDI  0
    VOUT
    LDI  1
    VOUT
    LDI  128
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  2
    VOUT
    LDI  64
    VOUT
    LDI  0
    VOUT
    JMP  E1_FIM
E1_Z_Z:
    ; sem quina, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  E1_FIM
E1_X_Z:
    ; quina no inicio, sem quina
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  E1_FIM
E1_XE_FACE:
    ; quina da parede do fundo, parede vista pela abertura
    LDI  0
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
E1_FIM:
; ----- lado esquerda, faixa 2 (x = 10..12) -----
    LD   F
    CMPI 0
    JNZ  E2_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  E2_FIM
E2_F0_N:
    CMPI 1
    JNZ  E2_F1_N
    ; atras da parede frontal (F = 1, T = 10)
    LDI  0
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    JMP  E2_FIM
E2_F1_N:
    LD   LBE
    ANDI 14          ; bits 1, 2 e 3
    CMPI 4
    JZ   E2_X_DIAG
    CMPI 6
    JZ   E2_X_DIAG
    CMPI 12
    JZ   E2_X_DIAG
    CMPI 14
    JZ   E2_X_DIAG
    CMPI 0
    JZ   E2_Z_Z
    CMPI 2
    JZ   E2_X_Z
    CMPI 8
    JZ   E2_XE_FACE
    ; quina no inicio, parede vista pela abertura
    LDI  0
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    JMP  E2_FIM
E2_X_DIAG:
    ; quina no inicio, parede lateral
    LDI  0
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  8
    VOUT
    LDI  16
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  16
    VOUT
    LDI  8
    VOUT
    LDI  0
    VOUT
    JMP  E2_FIM
E2_Z_Z:
    ; sem quina, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  E2_FIM
E2_X_Z:
    ; quina no inicio, sem quina
    LDI  0
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  E2_FIM
E2_XE_FACE:
    ; quina da parede do fundo, parede vista pela abertura
    LDI  0
    VOUT
    LDI  224
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
E2_FIM:
; ----- lado esquerda, faixa 3 (x = 13..15) -----
    LD   F
    CMPI 0
    JNZ  E3_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  E3_FIM
E3_F0_N:
    CMPI 1
    JNZ  E3_F1_N
    ; atras da parede frontal (F = 1, T = 10)
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    JMP  E3_FIM
E3_F1_N:
    ; atras da parede frontal (F = 2, T = 13)
    LDI  0
    VOUT
    LDI  224
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    JMP  E3_FIM
E3_FIM:
; ----- lado direita, faixa 3 (x = 13..15) -----
    LD   F
    CMPI 0
    JNZ  D3_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  D3_FIM
D3_F0_N:
    CMPI 1
    JNZ  D3_F1_N
    ; atras da parede frontal (F = 1, T = 10)
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    JMP  D3_FIM
D3_F1_N:
    ; atras da parede frontal (F = 2, T = 13)
    LDI  0
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  224
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
    JMP  D3_FIM
D3_FIM:
; ----- lado direita, faixa 2 (x = 10..12) -----
    LD   F
    CMPI 0
    JNZ  D2_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  D2_FIM
D2_F0_N:
    CMPI 1
    JNZ  D2_F1_N
    ; atras da parede frontal (F = 1, T = 10)
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    JMP  D2_FIM
D2_F1_N:
    LD   LBD
    ANDI 14          ; bits 1, 2 e 3
    CMPI 4
    JZ   D2_X_DIAG
    CMPI 6
    JZ   D2_X_DIAG
    CMPI 12
    JZ   D2_X_DIAG
    CMPI 14
    JZ   D2_X_DIAG
    CMPI 0
    JZ   D2_Z_Z
    CMPI 2
    JZ   D2_X_Z
    CMPI 8
    JZ   D2_XE_FACE
    ; quina no inicio, parede vista pela abertura
    LDI  0
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    JMP  D2_FIM
D2_X_DIAG:
    ; quina no inicio, parede lateral
    LDI  0
    VOUT
    LDI  16
    VOUT
    LDI  8
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  8
    VOUT
    LDI  16
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    JMP  D2_FIM
D2_Z_Z:
    ; sem quina, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  D2_FIM
D2_X_Z:
    ; quina no inicio, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
    JMP  D2_FIM
D2_XE_FACE:
    ; quina da parede do fundo, parede vista pela abertura
    LDI  0
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  224
    VOUT
    LDI  7
    VOUT
    LDI  0
    VOUT
D2_FIM:
; ----- lado direita, faixa 1 (x = 5..9) -----
    LD   F
    CMPI 0
    JNZ  D1_F0_N
    ; atras da parede frontal (F = 0, T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    JMP  D1_FIM
D1_F0_N:
    LD   LBD
    ANDI 7          ; bits 0, 1 e 2
    CMPI 2
    JZ   D1_X_DIAG
    CMPI 3
    JZ   D1_X_DIAG
    CMPI 6
    JZ   D1_X_DIAG
    CMPI 7
    JZ   D1_X_DIAG
    CMPI 0
    JZ   D1_Z_Z
    CMPI 1
    JZ   D1_X_Z
    CMPI 4
    JZ   D1_XE_FACE
    ; quina no inicio, parede vista pela abertura
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    JMP  D1_FIM
D1_X_DIAG:
    ; quina no inicio, parede lateral
    LDI  0
    VOUT
    LDI  2
    VOUT
    LDI  64
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  1
    VOUT
    LDI  128
    VOUT
    LDI  0
    VOUT
    LDI  128
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  1
    VOUT
    LDI  64
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  2
    VOUT
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    JMP  D1_FIM
D1_Z_Z:
    ; sem quina, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  D1_FIM
D1_X_Z:
    ; quina no inicio, sem quina
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    LDI  224
    VOUT
    LDI  255
    VOUT
    VOUT
    LDI  7
    VOUT
    JMP  D1_FIM
D1_XE_FACE:
    ; quina da parede do fundo, parede vista pela abertura
    LDI  0
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  252
    VOUT
    LDI  63
    VOUT
    LDI  0
    VOUT
D1_FIM:
; ----- lado direita, faixa 0 (x = 0..4) -----
    LD   LBD
    ANDI 3           ; bits 0 (parede) e 1 (parede no fundo da abertura)
    JZ   D0_VAZIA
    CMPI 2
    JZ   D0_FACE
    ; parede lateral (diagonal)
    LDI  16
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  8
    VOUT
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  16
    VOUT
    LDI  4
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  32
    VOUT
    LDI  2
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  64
    VOUT
    LDI  1
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  128
    VOUT
    JMP  D0_FIM
D0_FACE:
    ; parede vista pela abertura (T = 5)
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    LDI  32
    VOUT
    LDI  0
    VOUT
    VOUT
    LDI  4
    VOUT
    JMP  D0_FIM
D0_VAZIA:
    ; nada
    LDI  0
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
D0_FIM:
    JMP  LE_TECLA

; ---------- mapa 2D: 13x13 celulas de 2x2 pixels, centrado ----------
; Coluna por coluna, como o 3D. Pagina p = linhas de celula 4p..4p+3.
DESENHA_MAPA:
    LDI  0           ; margem esquerda: 3 colunas apagadas (12 bytes)
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    ST   BI          ; BI = celula (cx, 0)
M_COL:
    ; pagina 0: linhas 0..3, 2 bits por celula (parede = 255)
    LD   BI
    LDR
    ANDI 3
    ST   A0
    LD   BI
    ADDI 13
    LDR
    ANDI 12
    ADD  A0
    ST   A0
    LD   BI
    ADDI 26
    LDR
    ANDI 48
    ADD  A0
    ST   A0
    LD   BI
    ADDI 39
    LDR
    ANDI 192
    ADD  A0
    ST   A0
    ; pagina 1: linhas 4..7, 2 bits por celula (parede = 255)
    LD   BI
    ADDI 52
    LDR
    ANDI 3
    ST   A1
    LD   BI
    ADDI 65
    LDR
    ANDI 12
    ADD  A1
    ST   A1
    LD   BI
    ADDI 78
    LDR
    ANDI 48
    ADD  A1
    ST   A1
    LD   BI
    ADDI 91
    LDR
    ANDI 192
    ADD  A1
    ST   A1
    ; pagina 2: linhas 8..11, 2 bits por celula (parede = 255)
    LD   BI
    ADDI 104
    LDR
    ANDI 3
    ST   A2
    LD   BI
    ADDI 117
    LDR
    ANDI 12
    ADD  A2
    ST   A2
    LD   BI
    ADDI 130
    LDR
    ANDI 48
    ADD  A2
    ST   A2
    LD   BI
    ADDI 143
    LDR
    ANDI 192
    ADD  A2
    ST   A2
    LD   P           ; o jogador esta nesta coluna? (P - BI = 13 x linha)
    SUB  BI
    CMPI 13
    JZ   M_J1
    CMPI 26
    JZ   M_J2
    CMPI 39
    JZ   M_J3
    CMPI 52
    JZ   M_J4
    CMPI 65
    JZ   M_J5
    CMPI 78
    JZ   M_J6
    CMPI 91
    JZ   M_J7
    CMPI 104
    JZ   M_J8
    CMPI 117
    JZ   M_J9
    CMPI 130
    JZ   M_J10
    CMPI 143
    JZ   M_J11
    ; coluna de pixels 1 da celula (sem jogador)
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J1:           ; jogador na linha 1: 1 pixel aceso
    LD   A0
    ADDI 4
    VOUT
    LD   A1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J2:           ; jogador na linha 2: 1 pixel aceso
    LD   A0
    ADDI 16
    VOUT
    LD   A1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J3:           ; jogador na linha 3: 1 pixel aceso
    LD   A0
    ADDI 64
    VOUT
    LD   A1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J4:           ; jogador na linha 4: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    ADDI 1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J5:           ; jogador na linha 5: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    ADDI 4
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J6:           ; jogador na linha 6: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    ADDI 16
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J7:           ; jogador na linha 7: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    ADDI 64
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J8:           ; jogador na linha 8: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    ADDI 1
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J9:           ; jogador na linha 9: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    ADDI 4
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J10:           ; jogador na linha 10: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    ADDI 16
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    JMP  M_COL2
M_J11:           ; jogador na linha 11: 1 pixel aceso
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    ADDI 64
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
M_COL2:             ; coluna de pixels 2 da celula
    LD   A0
    VOUT
    LD   A1
    VOUT
    LD   A2
    VOUT
    LDI  3           ; pagina 3: linha 12 (parede)
    VOUT
    LD   BI
    ADDI 1
    ST   BI
    CMPI 13
    JNZ  M_COL
    LDI  0           ; margem direita: 3 colunas (12 bytes)
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    VOUT
    JMP  LE_TECLA

; ---------- le o teclado ----------
LE_TECLA:
    IN
    ST   KEY
    ANDI 1
    JZ   K2
    LD   P           ; frente
    ADD  FW
    ST   T0
    LDR
    CMPI 0
    JNZ  K_FIM
    LD   T0
    ST   P
    JMP  K_FIM
K2:
    LD   KEY
    ANDI 2
    JZ   K3
    LD   P           ; tras
    SUB  FW
    ST   T0
    LDR
    CMPI 0
    JNZ  K_FIM
    LD   T0
    ST   P
    JMP  K_FIM
K3:
    LD   KEY
    ANDI 4
    JZ   K4
    LD   FW          ; gira a esquerda: (FW, LW) <- (LW, -FW)
    ST   T0
    LD   LW
    ST   FW
    LDI  0
    SUB  T0
    ST   LW
    JMP  K_FIM
K4:
    LD   KEY
    ANDI 8
    JZ   K5
    LD   FW          ; gira a direita: (FW, LW) <- (-LW, FW)
    ST   T0
    LDI  0
    SUB  LW
    ST   FW
    LD   T0
    ST   LW
    JMP  K_FIM
K5:
    LD   KEY
    ANDI 16
    JZ   K_FIM
    LDI  1           ; liga/desliga mapa
    SUB  MAPA
    ST   MAPA
K_FIM:
    LD   P           ; chegou na saida (12,11) = 13*11 + 12?
    CMPI 155
    JNZ  QUADRO

; ---------- vitoria: xadrez 4x4, espera tecla, reinicia ----------
    LDI  0
    ST   X
V_COL:
    LD   X
    ANDI 4
    JZ   V_0
    LDI  240         ; 4 pixels de baixo de cada pagina
    JMP  V_S
V_0:
    LDI  15          ; 4 pixels de cima de cada pagina
V_S:
    VOUT
    VOUT
    VOUT
    VOUT
    LD   X
    ADDI 1
    ST   X
    CMPI 32
    JNZ  V_COL
V_ESPERA:
    IN               ; sem tecla, IN devolve 0
    TST
    JZ   V_ESPERA
    JMP  INICIO
"""


if __name__ == "__main__":
    pc = Computador()
    
    #print(montar_binario(PROGRAMA))

    pc.gravar_rom(montar(PROGRAMA))
    pc.ligar()
