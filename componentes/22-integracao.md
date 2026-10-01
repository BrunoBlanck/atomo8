# 22 · Integração: juntando tudo

Só faça esta etapa depois que **cada componente (01–21) passou nos testes
sozinho**. Junte em partes pequenas e teste a cada passo.

## Lista de ligações

| De                     | Sinal                      | Para                                                                               |
|------------------------|----------------------------|------------------------------------------------------------------------------------|
| PC (12) `Q[10:0]`      | endereço                   | ROM (15), incrementador (11)                                                       |
| ROM `[15:12]`          | `OP`                       | decodificador (17)                                                                 |
| ROM `[11:8]`           | `F`                        | decodificador (17), unidade lógica da ULA (04, tabela `T3..T0`)                    |
| ROM `[10:0]`           | `DEST`                     | mux do próximo PC (13)                                                             |
| ROM `[7:0]`            | `N`                        | mux end. RAM (10, entrada 00), mux B (05, entrada 1), mux de A (10, entrada 00)    |
| incrementador (11)     | `PC+1`                     | mux do próximo PC (13)                                                             |
| mux do próximo PC (13) | próximo PC                 | PC (12) `D`                                                                        |
| A (08) `Q`             | `A`                        | ULA `A`, RAM `DIN`, VRAM `DIN`, mux end. RAM (entrada 01), ponteiro e cursor `D_A` |
| ponteiro (21, 8 bits)  | `PONTEIRO`                 | mux end. RAM (entrada 10)                                                          |
| cursor (21, 7 bits)    | `CURSOR`                   | endereço da VRAM, lado da CPU (18)                                                 |
| mux end. RAM (10, 4×1) | endereço                   | RAM (16)                                                                           |
| RAM (16) `DOUT`        | dado da RAM                | mux B (entrada 0), mux de memória (05, entrada 0)                                  |
| VRAM (18), lado da CPU | dado da VRAM               | mux de memória (05, entrada 1)                                                     |
| mux de memória (05)    | `MEMÓRIA`                  | mux de A (entrada 01)                                                              |
| mux B (05)             | `B`                        | ULA (07)                                                                           |
| ULA `R`                | resultado                  | mux de A (entrada 10)                                                              |
| ULA `Z`, `C`           | flags novas                | flags Z e C (09)                                                                   |
| flag Z (09)            | `Z`                        | lógica de salto (14)                                                               |
| flag C (09)            | `C`                        | lógica de salto (14), ULA (`CIN` no ADC/SBC)                                       |
| lógica de salto (14)   | `TOMA`                     | mux do próximo PC (13)                                                             |
| teclado (19)           | `SAIDA[7:0]`               | mux de A (entrada 11)                                                              |
| mux de A (10)          | valor novo                 | A (08) `D`                                                                         |
| decodificador (17)     | sinais                     | ver arquivo 17 (resumo no arquivo 00)                                              |
| relógio (20)           | `CLK`, `CLK_BAIXO`, `/RST` | A, Z, C, PC, ponteiro, cursor, teclado, RAM, VRAM                                  |

Seleções dos muxes:

| Mux                    | Seleção        | Entradas                                          |
|------------------------|----------------|---------------------------------------------------|
| endereço da RAM (4×1)  | `END_SRC[1:0]` | 00 = N, 01 = A (`LDR`), 10 = ponteiro, 11 = livre |
| memória (2×1)          | `MEM_VID`      | 0 = RAM, 1 = VRAM                                 |
| B da ULA (2×1)         | `B_IMED`       | 0 = RAM, 1 = N                                    |
| A (4×1)                | `A_SRC[1:0]`   | 00 = N, 01 = memória, 10 = ULA, 11 = teclado      |
| endereço da VRAM (2×1) | `MEM_VID`      | 0 = varredura do painel, 1 = cursor (CPU)         |

## Ordem de montagem e testes intermediários

Use o **modo passo a passo** (arquivo 20) e LEDs em PC, A, Z e C (no ponteiro
e no cursor a partir da Etapa 11). Todos os programas abaixo foram montados com
`hardware.montar` e rodados no simulador; os tempos são os medidos lá.

### Etapa 1: PC + ROM + decodificador

Grave uma ROM com `F000` (código 15, não faz nada) em tudo e `JMP 0` (`8000`)
no endereço 7.
Esperado: PC conta 0, 1, ..., 7, 0, 1...

### Etapa 2: + registrador A + mux de A (só entrada N)

```
0: LDI 5
1: LDI 170
2: JMP 0
```

Esperado: A mostra 5, 170, 170, 5...

### Etapa 3: + ULA + flags Z e C + mux B (só imediato)

```
0: LDI 0
1: ADDI 1        ; A conta 1, 2, 3...
2: JNZ 1         ; volta enquanto A != 0
3: JMP 0
```

Esperado: A conta em binário até 255; no passo seguinte vira 0, Z = 1, C = 1
e o programa chega no endereço 3. São 1 + 256 × 2 = **513 × CLOCK** até lá.
O `255 + 1` é o pior caso do somador: é este teste que mede o limite do
CLOCK (arquivo 20).

### Etapa 4: + saltos condicionais

```
0: LDI 10
1: SUBI 1
2: JNZ 1
3: JMP 3         ; fim: fica parado aqui
```

Esperado: A desce de 10 até 0 e o PC fica preso em 3.
Tempo até lá: 1 + 10 × 2 = **21 × CLOCK**.

### Etapa 5: + RAM + mux de endereço (entradas N e A)

```
0: LDI 42
1: ST 7
2: LDI 0
3: LD 7          ; A volta a ser 42
4: LDI 7
5: LDR           ; A = RAM[7] = 42
6: ADD 7         ; A = 84
7: ST 8          ; RAM[8] = 84
8: SUB 7         ; A = 42
9: JMP 9
```

Esperado: A = 42, RAM[7] = 42, RAM[8] = 84 (**9 × CLOCK**).

### Etapa 6: + comparação

```
0: LDI 3
1: CMPI 3        ; Z = 1 (igual)
2: JZ 4
3: LDI 0         ; (pulado)
4: LDI 1
5: CMPI 2        ; Z = 0 (diferente)
6: JNZ 8
7: LDI 0         ; (pulado)
8: ANDI 1        ; A = 1
9: JMP 9
```

Esperado: A termina em 1; as duas instruções `LDI 0` nunca executam
(**7 × CLOCK**).

### Etapa 7: flag C e JC / JNC

```
      LDI  5
      CMPI 3          ; 5 >= 3 -> C = 1
      JNC  ERRO
      CMPI 9          ; 5 < 9  -> C = 0
      JC   ERRO
      LDI  200
      ADDI 100        ; 300 não cabe: A = 44, C = 1
      JNC  ERRO
      ADDI 1          ; A = 45, C = 0
      JC   ERRO
      LDI  1          ; passou
FIM:  JMP  FIM
ERRO: LDI  0
ERR2: JMP  ERR2
```

Esperado: A passa por 5, 200, 44, 45 e termina em **1** no `FIM` (endereço 11)
em **11 × CLOCK**. A = 0 preso em `ERR2` = algum salto errado.

### Etapa 8: unidade lógica (LOG)

```
      LDI  0b11001010
      ANDI 0b10101010   ; A = 10001010 (138)
      ORI  0b00000101   ; A = 10001111 (143)
      XORI 0b11111111   ; A = 01110000 (112)
      NOT               ; A = 10001111 (143)
      LDI  0
      TST               ; Z = 1, A continua 0
      JNZ  ERRO
      LDI  1
FIM:  JMP  FIM
ERRO: LDI  0
ERR2: JMP  ERR2
```

Esperado: A = 202, 138, 143, 112, 143, 0, 0, 1 e para no `FIM` (endereço 9)
em **9 × CLOCK**. `TST` é o jeito de ter Z depois de `LD`, `IN` ou `VIN`.

### Etapa 9: deslocamento (SHR)

```
      LDI  0b10110101   ; 181
      SHR               ; A = 01011010 (90), C = 1
      SHR               ; A = 00101101 (45), C = 0
      SHR               ; A = 00010110 (22), C = 1
FIM:  JMP  FIM
```

Esperado: A = 181, 90, 45, 22 e C = 1, 0, 1 (**4 × CLOCK**). O bit que sai
pela direita vai para C; R7 entra sempre 0.

### Etapa 10: soma de 16 bits (ADC)

`0x01F0 + 0x0230 = 0x0420`, número baixo em RAM[0] / RAM[2], alto em RAM[1] / RAM[3]:

```
      LDI  0xF0
      ST   0          ; X baixo
      LDI  0x01
      ST   1          ; X alto
      LDI  0x30
      ST   2          ; Y baixo
      LDI  0x02
      ST   3          ; Y alto
      LD   0
      ADD  2          ; 0xF0 + 0x30 = 0x120: A = 0x20, C = 1
      ST   4
      LD   1
      ADC  3          ; 0x01 + 0x02 + C = 0x04
      ST   5
FIM:  JMP  FIM
```

Esperado: RAM[4] = `0x20`, RAM[5] = `0x04` (**14 × CLOCK**). Se der `0x03`,
o C não chegou ao `CIN`.

### Etapa 11: + ponteiro da RAM (PTR / STP / LDP)

```
      LDI  0x40
      PTR             ; ponteiro = 0x40
      LDI  10
ENCHE: STP            ; RAM[ponteiro] = A, ponteiro + 1
      SUBI 1
      JNZ  ENCHE      ; grava 10, 9, ..., 1 em 0x40..0x49
      LDI  0x40
      PTR             ; volta ao início
      LDI  0
      ST   0          ; soma = 0
SOMA: LDP             ; A = RAM[ponteiro], ponteiro + 1
      ADD  0
      ST   0
      CMPI 55
      JNZ  SOMA
FIM:  JMP  FIM
```

Esperado: RAM[0x40..0x49] = 10, 9, ..., 1; A = 55; ponteiro = `0x4A`
(**87 × CLOCK**).

### Etapa 12: + display (VOUT)

Primeiro 1 pixel (depois de um reset):

```
0: LDI 1
1: VOUT          ; byte 00000001 na coluna 0, página 0 → pixel (0,0)
2: JMP 2
```

Depois a tela inteira com listras (128 × `VOUT`, **898 × CLOCK**):

```
      LDI  0
      ST   0          ; RAM[0] = contador
L:    LDI  85         ; 01010101
      VOUT
      LD   0
      ADDI 1
      ST   0
      CMPI 128
      JNZ  L
FIM:  JMP  FIM
```

Esperado: listras horizontais de 1 pixel, e o cursor de volta em 0.

Por último uma diagonal (pixel (x, x) para x = 0..31), que testa a ordem dos
bytes e dos bits:

```
      LDI  0
      ST   0          ; RAM[0] = x
      LDI  1
      ST   1          ; RAM[1] = 1 << (x & 7)
COL:  LD   0
      ANDI 24         ; 8 × página onde está o pixel
      ST   2
      CMPI 0
      LDI  0
      JNZ  P0
      LD   1
P0:   VOUT            ; página 0
      LD   2
      CMPI 8
      LDI  0
      JNZ  P1
      LD   1
P1:   VOUT            ; página 1
      LD   2
      CMPI 16
      LDI  0
      JNZ  P2
      LD   1
P2:   VOUT            ; página 2
      LD   2
      CMPI 24
      LDI  0
      JNZ  P3
      LD   1
P3:   VOUT            ; página 3
      LD   1
      ADD  1          ; máscara × 2
      ST   1
      JNZ  SEGUE
      LDI  1          ; passou de 128: volta a 1
      ST   1
SEGUE: LD  0
      ADDI 1
      ST   0
      CMPI 32
      JNZ  COL
FIM:  JMP  FIM
```

Esperado: uma linha do canto superior esquerdo ao inferior direito, cursor
em 0 (**1 036 × CLOCK**).

### Etapa 13: VRAM lida + cursor carregado (VPOS / VIN)

Byte 5 da VRAM = coluna 1, página 1 (pixels (1,8) a (1,15)):

```
      LDI  5
      VPOS            ; cursor = 5
      LDI  0x0F
      VOUT            ; VRAM[5] = 00001111, cursor = 6
      LDI  5
      VPOS            ; cursor = 5 de novo
      VIN             ; A = 15 (cursor fica em 5)
      ORI  0xF0       ; acende os 4 pixels de baixo
      VOUT            ; VRAM[5] = 255, cursor = 6
      LDI  5
      VPOS
      VIN             ; A = 255
FIM:  JMP  FIM
```

Esperado: A = 5, 5, 15, 15, 5, 5, 15, 255, 255, 5, 5, **255**; os 8 pixels
(1,8)..(1,15) acesos; cursor = 5 (**12 × CLOCK**). É o mesmo
"ler, mudar, gravar" que a bola usa.

### Etapa 14: + teclado

```
0: IN
1: JMP 0
```

Aperte os botões e veja o bit certo aparecer em A por um pulso (o evento é
apagado quando lido). Sem tecla, `IN` devolve 0 e não espera.

### Etapa 15: os programas de verdade

| Programa | ROM           | Esperado                                                                        |
|----------|---------------|---------------------------------------------------------------------------------|
| bola     | 76 palavras   | 1 pixel quicando; ~75 × CLOCK por passo + espera de 512 × CLOCK                 |
| doom     | 1 596 / 2 048 | ~2 130 × CLOCK para desenrolar o labirinto, depois quadros de 262 a 385 × CLOCK |
| tetris   | 960 palavras  | poço 10 × 16; mover/girar ~615 × CLOCK; some linha ~1 250 a 2 190 × CLOCK       |

Grave `rom_alta.bin` / `rom_baixa.bin` (arquivo 15), aperte RESET e jogue.

## Conferindo com o simulador

O `hardware.py` roda exatamente o mesmo código. Para comparar passo a passo,
imprima o estado depois de cada instrução:

```python
import hardware, doom
hardware.CLOCK_US = 0                          # sem esperar o relógio
pc = hardware.Computador()
pc.display.mostrar = lambda *a, **k: None      # sem desenhar a tela
pc.gravar_rom(hardware.montar(doom.PROGRAMA))
for _ in range(50):
    print(pc.pc, hex(pc.rom[pc.pc]), pc.a, pc.z, pc.c, pc.ponteiro, pc.cursor)
    pc.passo()
```

Os programas de teste acima podem ser montados do mesmo jeito: basta trocar
`doom.PROGRAMA` por um texto com as instruções. `pc.ciclos` dá o tempo em
CLOCK. O ponteiro liga com lixo (como no hardware); só compare depois do `PTR`.

## Problemas comuns

| Sintoma                                   | Causa provável                                                                  |
|-------------------------------------------|---------------------------------------------------------------------------------|
| PC pula endereços                         | debounce do botão de passo; ruído no CLK (capacitor de 100 nF em cada placa)    |
| `LD` / `LDR` / `LDP` leem endereço errado | seleção `END_SRC` do mux de endereço da RAM trocada                             |
| A pega valor da VRAM no `LD`              | `MEM_VID` ligado fora das instruções de vídeo (mux de memória)                  |
| JZ nunca salta depois de LD               | certo! Z só muda em ARIT e LOG; use `TST` antes (1 × CLOCK, A não muda)         |
| C errado / SUB dá resultado +1 ou −1      | `CIN = USA_C·C + /USA_C·SUB` mal ligado                                         |
| ADC não soma o vai-um                     | `USA_C` não chega ao `CIN`, ou C gravado fora de ARIT (`C_WE`)                  |
| JC / JNC "ao contrário" depois de CMP     | certo! C = 1 quer dizer A ≥ B (sem empréstimo)                                  |
| SHR não muda C                            | mux do C novo (seleção `SHR`) sem ligar: tem que pegar A0                       |
| AND vira OR (ou outra função)             | bits F trocados na unidade lógica: bit 11 = T3 ... bit 8 = T0                   |
| VIN devolve lixo                          | mux de endereço da VRAM não escolheu a CPU (`MEM_VID` = 1 tem que dar o cursor) |
| ponteiro não avança                       | `PTR_INC` (MEM·F2·/F1) não chega no `AVANCA` do ponteiro                        |
| funciona devagar, erra rápido             | relógio acima do limite (arquivo 20) ou pulso de escrita fora da metade baixa   |
| imagem "deitada" ou espelhada             | bit 0 do byte tem que ser o pixel de CIMA da página (arquivo 18)                |
| imagem deslizando a cada quadro           | cursor avançou fora do `VOUT` (`CUR_INC`) ou não voltou a 0 no reset            |
| pixels "fantasma"                         | endereço da VRAM mudando durante o pulso de escrita (o cursor só anda no ↑CLK)  |
