# -*- coding: utf-8 -*-
"""
BOLA QUICANDO - PROGRAMA DE TESTE DA ROM (display 32 x 32)

Programa minimo para testar o hardware de hardware.py sem o labirinto.
Usa o MESMO hardware e o MESMO conjunto de instrucoes; so troca o que vai
gravado na ROM. Nao le o teclado (nunca executa IN): roda sozinho.
Ctrl+C desliga.

Um pixel (a bola) anda na diagonal. Ao chegar numa borda, o sentido
daquele eixo e invertido.

------------------------------------------------------------------
MAPA DA RAM
------------------------------------------------------------------
  0x00 BX  : coluna da bola (0..31)
  0x01 BY  : linha da bola  (0..31)
  0x02 DX  : passo em x (+1 = 1, -1 = 255)
  0x03 DY  : passo em y (+1 = 1, -1 = 255)
  0x04 END : endereco da VRAM do byte da bola (= 4 x BX + BY / 8)
  0x05 M   : bit da bola dentro do byte (= 1 << (BY & 7))
  0x06 T   : temporario

------------------------------------------------------------------
IDEIAS
------------------------------------------------------------------
  1) A tela e uma memoria: o quadro NAO e redesenhado. So o byte da bola
     muda: ~75 instrucoes por passo (fora a espera), contra ~300 do
     quadro inteiro.
  2) Desenhar e apagar sao a MESMA coisa: VIN, XOR M, VOUT (inverte o
     bit da bola). Igual ao CHIP-8: desenhar de novo apaga.
  3) Pagina da bola = BY / 8 = tres SHR. Endereco = 4 x BX + pagina
     (4 x BX = BX + BX, duas vezes).
  4) Bater na borda com a flag C: CMPI 1 / JNC = "BX < 1" (BX = 0) e
     CMPI 31 / JNC = "BX < 31" (ainda nao chegou na direita).
  5) A bola fica acesa durante a espera (laco so em A, sem RAM) e fica
     apagada so durante as contas do proximo passo.
"""

from hardware import Computador, montar, montar_binario

PROGRAMA = """
; ================= VARIAVEIS NA RAM =================
.ram BX  0x00
.ram BY  0x01
.ram DX  0x02
.ram DY  0x03
.ram END 0x04
.ram M   0x05
.ram T   0x06

; ================= LIGA: LIMPA A TELA =================
INICIO:
    LDI  0
    VPOS             ; cursor = 0
    LDI  128
    ST   T
LIMPA:
    LDI  0
    VOUT             ; 8 pixels apagados, cursor + 1
    LD   T
    SUBI 1
    ST   T
    JNZ  LIMPA

; ================= POSICAO E SENTIDO INICIAIS =================
    LDI  5
    ST   BX
    LDI  11
    ST   BY
    LDI  1           ; direita
    ST   DX
    ST   DY          ; baixo

; ================= UM PASSO DA BOLA =================
PASSO:
    ; ---- END = 4 x BX + BY / 8 ----
    LD   BY
    SHR
    SHR
    SHR              ; A = pagina (0..3)
    ST   T
    LD   BX
    ADD  BX          ; 2 x BX
    ST   END
    ADD  END         ; 4 x BX
    ADD  T
    ST   END

    ; ---- M = 1 << (BY & 7) ----
    LD   BY
    ANDI 7
    ST   T
    LDI  1
    ST   M
M_LACO:
    LD   T
    TST              ; Z = (T == 0)
    JZ   M_FIM
    SUBI 1
    ST   T
    LD   M
    ADD  M           ; M = M + M
    ST   M
    JMP  M_LACO
M_FIM:

    ; ---- acende: inverte o bit da bola ----
    LD   END
    VPOS
    VIN
    XOR  M
    VOUT

    ; ---- espera (so A, sem RAM: 256 voltas) ----
    LDI  0
ESPERA:
    SUBI 1
    JNZ  ESPERA

    ; ---- apaga: inverte de novo o mesmo bit ----
    LD   END
    VPOS
    VIN
    XOR  M
    VOUT

; ================= MOVE A BOLA =================
    LD   BX
    ADD  DX
    ST   BX
    CMPI 1           ; BX < 1? (bateu na esquerda)
    JNC  INV_X
    CMPI 31          ; BX < 31? (ainda nao bateu na direita)
    JNC  MOVE_Y
INV_X:
    LDI  0
    SUB  DX          ; DX = -DX
    ST   DX
MOVE_Y:
    LD   BY
    ADD  DY
    ST   BY
    CMPI 1           ; BY < 1? (bateu em cima)
    JNC  INV_Y
    CMPI 31          ; BY < 31? (ainda nao bateu embaixo)
    JNC  PASSO
INV_Y:
    LDI  0
    SUB  DY          ; DY = -DY
    ST   DY
    JMP  PASSO
"""


if __name__ == "__main__":
    pc = Computador()

    #print(montar_binario(PROGRAMA))

    pc.gravar_rom(montar(PROGRAMA))
    pc.ligar()
