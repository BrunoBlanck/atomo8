# Componentes do hardware do labirinto

Esta pasta descreve, **um arquivo por componente**, tudo o que precisa ser
construído fisicamente para rodar o `doom.py` (o programa da ROM) exatamente
como o `hardware.py` simula.

**Não é um computador de uso geral.** É o hardware mínimo para este jogo, com
display de 32 × 32 pixels de 1 bit. Tudo o que o programa não usa foi retirado:
não há pilha, sub-rotinas, portas numeradas nem modos de vídeo.

**Tudo em portas lógicas** (AND, OR, NOT, XOR, NAND, NOR) e flip-flops D
feitos de portas. Custos em portas, nunca em chips.

Cada arquivo é **independente**: dá para montar o componente sozinho numa
protoboard, ligar chaves (DIP switches) nas entradas e LEDs nas saídas,
conferir a tabela de testes e só depois passar para o próximo.

## Ordem de construção sugerida

| #  | Arquivo                                                                | O que é                                          | Depende de (só para integrar) |
|----|------------------------------------------------------------------------|--------------------------------------------------|-------------------------------|
| 01 | [01-somador-completo.md](01-somador-completo.md)                       | soma de 1 bit                                    | —                             |
| 02 | [02-somador-8-bits.md](02-somador-8-bits.md)                           | 8 somadores em cadeia                            | 01                            |
| 03 | [03-inversor-controlado-8-bits.md](03-inversor-controlado-8-bits.md)   | 8 XOR (para SUB)                                 | —                             |
| 04 | [04-unidade-logica.md](04-unidade-logica.md)                           | tabela-verdade programável (AND/OR/XOR…)         | —                             |
| 05 | [05-multiplexador-2x1-8-bits.md](05-multiplexador-2x1-8-bits.md)       | escolhe entre 2 bytes                            | —                             |
| 06 | [06-detector-de-zero.md](06-detector-de-zero.md)                       | Z = resultado é zero                             | —                             |
| 07 | [07-ula.md](07-ula.md)                                                 | ULA completa (soma, lógica, SHR)                 | 02..06                        |
| 08 | [08-registrador-a.md](08-registrador-a.md)                             | acumulador 8 bits                                | —                             |
| 09 | [09-flags-z-e-c.md](09-flags-z-e-c.md)                                 | guarda as flags Z e C                            | —                             |
| 10 | [10-multiplexador-4x1-8-bits.md](10-multiplexador-4x1-8-bits.md)       | escolhe 1 de 4 bytes                             | —                             |
| 11 | [11-incrementador-11-bits.md](11-incrementador-11-bits.md)             | PC + 1                                           | —                             |
| 12 | [12-registrador-pc.md](12-registrador-pc.md)                           | contador de programa                             | —                             |
| 13 | [13-multiplexador-proximo-pc.md](13-multiplexador-proximo-pc.md)       | escolhe o próximo PC                             | —                             |
| 14 | [14-logica-de-salto.md](14-logica-de-salto.md)                         | decide se o salto acontece                       | —                             |
| 15 | [15-rom-de-programa.md](15-rom-de-programa.md)                         | 2048 × 16 bits                                   | —                             |
| 16 | [16-ram.md](16-ram.md)                                                 | 256 × 8 bits                                     | —                             |
| 17 | [17-decodificador-de-instrucoes.md](17-decodificador-de-instrucoes.md) | unidade de controle (OP e F → sinais)            | —                             |
| 18 | [18-display.md](18-display.md)                                         | VRAM de 128 bytes + varredura do painel          | —                             |
| 19 | [19-teclado.md](19-teclado.md)                                         | 5 botões → byte                                  | —                             |
| 20 | [20-relogio-e-reset.md](20-relogio-e-reset.md)                         | clock, passo a passo, reset                      | —                             |
| 21 | [21-registrador-ponteiro.md](21-registrador-ponteiro.md)               | ponteiro da RAM e cursor da VRAM (construído 2×) | —                             |
| 22 | [22-integracao.md](22-integracao.md)                                   | como ligar tudo e testar o sistema               | todos                         |

## Diagrama geral

```
                         +--------------------------------------------------+
                         |                 ROM 2048 x 16 (15)               |
   +---------+ PC[10:0]  | OP[3:0]   F[3:0]           N[7:0]     DEST[10:0] |
   | PC (12) |---------->+--------------------------------------------------+
   +---------+              |         |                 |            |
     ^    |                 v         v                 |            |
     |    |  +----------+ +--------------------+        |            |
     |    +->| INC (11) | | DECODIFICADOR (17) |        |            |
     |       +----------+ | sinais de controle |        |            |
     |          | PC+1    +--------------------+        |            |
     |          v             F[3:0] --> ULA            |            |
     |   +-------------+                                |      DEST  |
     +---| MUX PC (13) |<--------------------------------------------+
         +-------------+                                |
               ^ TOMA                                   |
         +------------+                                 |
         | SALTO (14) |<-- Z, C                         v  N para os muxes
         +------------+

   N ------------->+------------+  endereço  +-----------+
   A ------------->| MUX END.   |----------->| RAM 256x8 |<-- A (ST, STP)
   PONTEIRO (21) ->| 4x1 (10)   |            |   (16)    |
                   +------------+            +-----------+
                                                   | DADO_RAM
                                                   +--------------+
                                                   v              v
   CURSOR (21) --> +-----------+  DADO_VRAM  +-----------+   +-----------+
                   | VRAM (18) |------------>| MUX MEM.  |   | MUX B (05)|<-- N
   A (VOUT) ------>|           |             | 2x1 (05)  |   +-----------+
                   +-----------+             +-----------+         | B
                         |                         | MEMÓRIA       v
                   painel 32x32                    |   A ---> +----------+
                                                   |          | ULA (07) |<-- F[3:0]
                                                   |          +----------+
                                                   |            | R    | Z, C
                                                   |            |      v
                                                   |            |  +--------------------+
                                                   |            |  | FLAGS Z e C (09)   |
                                                   v            v  +--------------------+
   N ------------------------------------> +---------------------------+
                                           |  MUX 4x1 entrada A (10)   |<-- TECLADO (19)
                                           +---------------------------+
                                                         |
                                                         v
                                                    +--------+
                                                    | A (08) |---> RAM, VRAM, ULA,
                                                    +--------+     MUX END., PONTEIRO, CURSOR
```

## Formato da instrução (16 bits)

```
 15..12   11..8   7..0
 [ OP ]  [  F  ] [ N ]
```

| Campo        | Bits   | Uso                                                    |
|--------------|--------|--------------------------------------------------------|
| `OP`         | 15..12 | código da instrução → decodificador (17)               |
| `F`          | 11..8  | função (ARIT), tabela-verdade (LOG) ou subfunção (MEM) |
| `N`          | 7..0   | número imediato ou endereço da RAM                     |
| `DEST[10:0]` | 10..0  | só nos saltos: destino (bit 11 = 0)                    |

## Conjunto de instruções (16 códigos)

| Cód | Instrução | F         | Efeito                                          | Flags |
|-----|-----------|-----------|-------------------------------------------------|-------|
| 0   | `LDI n`   | —         | A = n                                           | —     |
| 1   | `LD m`    | —         | A = RAM[m]                                      | —     |
| 2   | `ST m`    | —         | RAM[m] = A                                      | —     |
| 3   | `LDR`     | —         | A = RAM[A]                                      | —     |
| 4   | `ARIT m`  | função    | A = A op RAM[m]                                 | Z, C  |
| 5   | `ARITI n` | função    | A = A op n                                      | Z, C  |
| 6   | `LOG m`   | tabela    | A = f(A, RAM[m]) bit a bit                      | Z     |
| 7   | `LOGI n`  | tabela    | A = f(A, n) bit a bit                           | Z     |
| 8   | `JMP e`   | (destino) | PC = e                                          | —     |
| 9   | `JZ e`    | (destino) | se Z = 1: PC = e                                | —     |
| 10  | `JNZ e`   | (destino) | se Z = 0: PC = e                                | —     |
| 11  | `JC e`    | (destino) | se C = 1: PC = e                                | —     |
| 12  | `JNC e`   | (destino) | se C = 0: PC = e                                | —     |
| 13  | `IN`      | —         | A = eventos do teclado (0 = nenhum; não espera) | —     |
| 14  | `MEM`     | subfunção | VRAM e ponteiro (tabela abaixo)                 | —     |
| 15  | —         | —         | não faz nada (preenche a ROM: F000)             | —     |

**ARIT** (4 e 5): cada bit de F liga direto num ponto da ULA.

| Bit | Nome    | Efeito                              |
|-----|---------|-------------------------------------|
| 8   | `SUB`   | inverte B e vai-um de entrada = 1   |
| 9   | `USA_C` | vai-um de entrada = flag C          |
| 10  | `SHR`   | resultado = A >> 1 (R7 = 0), C = A0 |
| 11  | `NG`    | não grava A (só as flags)           |

| Mnemônico          | F    |
|--------------------|------|
| `ADD m` / `ADDI n` | 0000 |
| `SUB m` / `SUBI n` | 0001 |
| `ADC m` / `ADCI n` | 0010 |
| `SBC m` / `SBCI n` | 0011 |
| `SHR` (ARITI, N=0) | 0100 |
| `CMP m` / `CMPI n` | 1001 |

**LOG** (6 e 7): F = tabela-verdade T3 T2 T1 T0. Bit n do resultado = T[2·An + Bn].

| Mnemônico          | Tabela | Função                |
|--------------------|--------|-----------------------|
| `AND m` / `ANDI n` | 1000   | A AND B               |
| `OR m` / `ORI n`   | 1110   | A OR B                |
| `XOR m` / `XORI n` | 0110   | A XOR B               |
| `TST` (LOGI, N=0)  | 1100   | passa A: só calcula Z |
| `NOT` (LOGI, N=0)  | 0011   | NOT A                 |

Forma genérica: `LOG t m` / `LOGI t n`.

**MEM** (14): bit 10 escolhe a memória (0 = VRAM, 1 = RAM), bits 9..8 a operação (00 grava, 01 lê, 10 carrega).

| F    | Instr. | Efeito                                         |
|------|--------|------------------------------------------------|
| 0000 | `VOUT` | VRAM[cursor] = A, cursor + 1 (`OUT` = apelido) |
| 0001 | `VIN`  | A = VRAM[cursor] (cursor não anda)             |
| 0010 | `VPOS` | cursor = A (7 bits de baixo)                   |
| 0100 | `STP`  | RAM[ponteiro] = A, ponteiro + 1                |
| 0101 | `LDP`  | A = RAM[ponteiro], ponteiro + 1                |
| 0110 | `PTR`  | ponteiro = A                                   |

Flags: só ARIT/ARITI mudam C; só ARIT/ARITI/LOG/LOGI mudam Z. Depois de
SUB/CMP, C = 1 → A ≥ B (sem empréstimo).

## Convenções usadas em todos os arquivos

- Bit 0 = menos significativo (LSB). `A[7:0]` = 8 fios, de A7 a A0.
- `1` = nível alto (5 V ou 3,3 V), `0` = GND.
- `↑CLK` = borda de subida do relógio. Todos os registradores gravam **somente** nela.
- `/X` (barra) = sinal ativo em nível baixo.

## Sinais de controle (saem do decodificador, arquivo 17)

| Sinal          | Largura | Significado                                                    |
|----------------|---------|----------------------------------------------------------------|
| `A_WE`         | 1       | grava A no próximo ↑CLK                                        |
| `A_SRC[1:0]`   | 2       | o que entra em A: 00 = N, 01 = memória, 10 = ULA, 11 = teclado |
| `MEM_VID`      | 1       | memória que vai para A: 0 = RAM, 1 = VRAM                      |
| `RAM_WE`       | 1       | grava A na RAM (ST, STP)                                       |
| `END_SRC[1:0]` | 2       | endereço da RAM: 00 = N, 01 = A (LDR), 10 = ponteiro (LDP/STP) |
| `B_IMED`       | 1       | operando B da ULA vem de N; senão vem da RAM                   |
| `SUB`          | 1       | ULA inverte B (vai-um de entrada = 1 se `USA_C` = 0)           |
| `USA_C`        | 1       | vai-um de entrada = flag C (ADC, SBC)                          |
| `SHR`          | 1       | ULA entrega A >> 1; C novo = A0                                |
| `LOGICA`       | 1       | ULA entrega a unidade lógica (tabela = F)                      |
| `Z_WE`         | 1       | grava a flag Z                                                 |
| `C_WE`         | 1       | grava a flag C                                                 |
| `SALTO`        | 1       | JMP (sempre salta)                                             |
| `SE_Z`         | 1       | JZ                                                             |
| `SE_NZ`        | 1       | JNZ                                                            |
| `SE_C`         | 1       | JC                                                             |
| `SE_NC`        | 1       | JNC                                                            |
| `TEC_RD`       | 1       | IN: teclado entrega o byte e apaga os eventos lidos            |
| `VID_WR`       | 1       | VOUT: grava A na VRAM[cursor]                                  |
| `CUR_INC`      | 1       | cursor + 1 (mesmo fio que `VID_WR`)                            |
| `CUR_LD`       | 1       | VPOS: cursor = A                                               |
| `PTR_LD`       | 1       | PTR: ponteiro = A                                              |
| `PTR_INC`      | 1       | ponteiro + 1 (STP, LDP)                                        |

Além dos sinais, `F[3:0]` vai **direto** da ROM para a ULA (tabela-verdade da
unidade lógica).

## A constante CLOCK

Todos os tempos desta pasta são escritos em função de **uma única constante**:

```
CLOCK = período do relógio (duração de 1 pulso completo)
```

O valor de CLOCK **ainda não é conhecido**: ele será medido quando o hardware
estiver montado (arquivo 20, seção "Como descobrir o CLOCK").

| Escrita     | Significado                                                     |
|-------------|-----------------------------------------------------------------|
| `1 × CLOCK` | um pulso completo de relógio                                    |
| `2 × CLOCK` | dois pulsos                                                     |
| `½ × CLOCK` | meia fase do pulso (só a parte alta ou só a baixa)              |
| `0 × CLOCK` | combinacional: o resultado sai no mesmo ciclo, sem gastar pulso |

O simulador usa a mesma constante: `CLOCK_US` no topo de `hardware.py`.

Tempos que **não** dependem do CLOCK (debounce de botão, reset ao ligar,
varredura do display) ficam indicados como tal.

## Filosofia do ciclo

Cada instrução leva exatamente **1 × CLOCK**.

1. Primeira metade (**½ × CLOCK**, relógio **alto**): o PC já aponta para a
   instrução, a ROM entrega a palavra, o decodificador gera os sinais e todos
   os caminhos combinacionais (RAM, VRAM, ULA, muxes) se estabilizam.
2. Segunda metade (**½ × CLOCK**, relógio **baixo**): se for ST, STP ou VOUT,
   o pulso de escrita (`RAM_WE` ou `VID_WR`) é liberado. Endereços e dados já
   estão estáveis.
3. Na **borda de subida**: A, Z, C, PC, ponteiro e cursor gravam seus novos
   valores ao mesmo tempo e a próxima instrução começa.

Regra de ouro: **tudo o que é combinacional em fila** precisa caber em
½ × CLOCK. O caminho mais longo:

```
ROM → decodificador → mux de endereço (4x1) → RAM → mux B → XOR (SUB)
    → somador (vai-um em cadeia) → mux de resultado (4x1) → mux de A → A
```

## Desempenho do jogo

| O quê                         | Tempo                          |
|-------------------------------|--------------------------------|
| qualquer instrução            | 1 × CLOCK                      |
| ligar (desenrola o labirinto) | ~2 130 × CLOCK                 |
| quadro 3D                     | 262 a 385 × CLOCK (média ~318) |
| quadro do mapa                | ~1 496 × CLOCK                 |

Todo quadro grava 128 bytes no display. ROM: `doom.py` usa 1 596 de 2048
palavras, `bola.py` 76, `tetris.py` 960. Detalhes e quadros por segundo no arquivo 20.
