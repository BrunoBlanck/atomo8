# 17 · Decodificador de instruções (unidade de controle)

Transforma o opcode `OP` e o campo `F` da instrução em **todos os sinais de
controle**. É combinacional: não tem relógio nem estado, porque cada
instrução leva um único ciclo. Só portas: NOT, AND e OR.

## Pinos

| Pino               | Direção | Largura                                  |
|--------------------|---------|------------------------------------------|
| `OP[3:0]`          | entrada | 4 (bits 15..12 da ROM)                   |
| `F[3:0]`           | entrada | 4 (bits 11..8 da ROM)                    |
| sinais de controle | saída   | 25 (tabela abaixo; `CUR_INC` = `VID_WR`) |

## Passo 1: decodificador 4 → 16

Uma linha `Lk` por opcode; só uma fica em 1. Cada linha é um AND de 4
entradas, com os bits de OP invertidos ou não.

```
OP3 ──┬─────────────── OP3        L5  = /OP3 ·  OP2 · /OP1 ·  OP0   (0101)
      └──[NOT]──────── /OP3       L14 =  OP3 ·  OP2 ·  OP1 · /OP0   (1110)
 (o mesmo para OP2, OP1, OP0)

/OP3 ─┐
 OP2 ─┤
/OP1 ─┤ AND ── L5
 OP0 ─┘
```

Portas: **4 NOT + 16 AND de 4 entradas**.

## Passo 2: os sinais

`+` = OR, `·` = AND, `/X` = NOT X. Cópia exata de `decodifica()` em `hardware.py`.

```
ARIT      = L4 + L5                    grupos
LOGICA    = L6 + L7
MEM       = L14

M_GRAVA   = MEM · /F1 · /F0            subfunção do MEM (F1 F0)
M_LE      = MEM · /F1 ·  F0
M_CARREGA = MEM ·  F1 · /F0

A_WE      = L0 + L1 + L3 + ARIT·/F3 + LOGICA + L13 + M_LE
A_SRC0    = L1 + L3 + L13 + MEM
A_SRC1    = ARIT + LOGICA + L13
MEM_VID   = MEM · /F2
RAM_WE    = L2 + M_GRAVA·F2
END_SRC0  = L3
END_SRC1  = MEM
B_IMED    = L5 + L7
SUB       = ARIT · F0
USA_C     = ARIT · F1
SHR       = ARIT · F2
LOGICA    = L6 + L7                    (o grupo já é o sinal)
Z_WE      = ARIT + LOGICA
C_WE      = ARIT
SALTO = L8   SE_Z = L9   SE_NZ = L10   SE_C = L11   SE_NC = L12
TEC_RD    = L13
VID_WR    = M_GRAVA · /F2
CUR_INC   = M_GRAVA · /F2              (mesmo fio que VID_WR)
CUR_LD    = M_CARREGA · /F2
PTR_LD    = M_CARREGA ·  F2
PTR_INC   = MEM · F2 · /F1             (STP e LDP)
```

## Tabela completa (célula vazia = 0)

| OP | F      | Instr.  | A_WE | A_SRC | MEM_VID | RAM_WE | END_SRC | B_IMED | SUB | USA_C | SHR | LOGICA | Z_WE | C_WE | SALTO | SE_Z | SE_NZ | SE_C | SE_NC | TEC_RD | VID_WR | CUR_INC | CUR_LD | PTR_LD | PTR_INC |
|----|--------|---------|------|-------|---------|--------|---------|--------|-----|-------|-----|--------|------|------|-------|------|-------|------|-------|--------|--------|---------|--------|--------|---------|
| 0  | —      | LDI     | 1    |       |         |        |         |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |
| 1  | —      | LD      | 1    | 01    |         |        |         |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |
| 2  | —      | ST      |      |       |         | 1      |         |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |
| 3  | —      | LDR     | 1    | 01    |         |        | 01      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |
| 4  | 0000   | ADD     | 1    | 10    |         |        |         |        |     |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 4  | 0001   | SUB     | 1    | 10    |         |        |         |        | 1   |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 4  | 0010   | ADC     | 1    | 10    |         |        |         |        |     | 1     |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 4  | 0011   | SBC     | 1    | 10    |         |        |         |        | 1   | 1     |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 4  | 1001   | CMP     |      | 10    |         |        |         |        | 1   |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 0000   | ADDI    | 1    | 10    |         |        |         | 1      |     |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 0001   | SUBI    | 1    | 10    |         |        |         | 1      | 1   |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 0010   | ADCI    | 1    | 10    |         |        |         | 1      |     | 1     |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 0011   | SBCI    | 1    | 10    |         |        |         | 1      | 1   | 1     |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 0100   | SHR     | 1    | 10    |         |        |         | 1      |     |       | 1   |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 5  | 1001   | CMPI    |      | 10    |         |        |         | 1      | 1   |       |     |        | 1    | 1    |       |      |       |      |       |        |        |         |        |        |         |
| 6  | tabela | LOG m   | 1    | 10    |         |        |         |        |     |       |     | 1      | 1    |      |       |      |       |      |       |        |        |         |        |        |         |
| 7  | tabela | LOGI n  | 1    | 10    |         |        |         | 1      |     |       |     | 1      | 1    |      |       |      |       |      |       |        |        |         |        |        |         |
| 8  | dest.  | JMP     |      |       |         |        |         |        |     |       |     |        |      |      | 1     |      |       |      |       |        |        |         |        |        |         |
| 9  | dest.  | JZ      |      |       |         |        |         |        |     |       |     |        |      |      |       | 1    |       |      |       |        |        |         |        |        |         |
| 10 | dest.  | JNZ     |      |       |         |        |         |        |     |       |     |        |      |      |       |      | 1     |      |       |        |        |         |        |        |         |
| 11 | dest.  | JC      |      |       |         |        |         |        |     |       |     |        |      |      |       |      |       | 1    |       |        |        |         |        |        |         |
| 12 | dest.  | JNC     |      |       |         |        |         |        |     |       |     |        |      |      |       |      |       |      | 1     |        |        |         |        |        |         |
| 13 | —      | IN      | 1    | 11    |         |        |         |        |     |       |     |        |      |      |       |      |       |      |       | 1      |        |         |        |        |         |
| 14 | 0000   | VOUT    |      | 01    | 1       |        | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        | 1      | 1       |        |        |         |
| 14 | 0001   | VIN     | 1    | 01    | 1       |        | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |
| 14 | 0010   | VPOS    |      | 01    | 1       |        | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         | 1      |        |         |
| 14 | 0100   | STP     |      | 01    |         | 1      | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        | 1       |
| 14 | 0101   | LDP     | 1    | 01    |         |        | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        | 1       |
| 14 | 0110   | PTR     |      | 01    |         |        | 10      |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        | 1      |         |
| 15 | —      | (livre) |      |       |         |        |         |        |     |       |     |        |      |      |       |      |       |      |       |        |        |         |        |        |         |

- `—` = F não importa; `tabela` = qualquer tabela-verdade; `dest.` = bits do destino.
- O código 15 não faz nada (o PC só avança). É o que preenche a ROM vazia (F000).
- Em VOUT, VPOS, STP, PTR e CMP o `A_SRC` sai diferente de 00, mas não importa: `A_WE` = 0.
- Códigos de MEM fora da tabela (0011, 0111) não fazem nada; F3 é ignorado no MEM. Não use.

## Por que F vai direto (sem decodificar)

| Instrução | F é…               | Como é usado                                                  |
|-----------|--------------------|---------------------------------------------------------------|
| ARIT      | 4 chaves da ULA    | F0 → SUB, F1 → USA_C, F2 → SHR, F3 → não grava A: 1 AND cada  |
| LOG       | a própria tabela   | F3..F0 vão em fio direto para os dados da unidade lógica (04) |
| MEM       | memória + operação | 3 grupos (M_GRAVA, M_LE, M_CARREGA) × F2                      |
| saltos    | bits do destino    | nenhum sinal usa F sem passar por ARIT ou MEM: ficam em 0     |

Cada bit de F já é o sinal que a ULA precisa. Isso dispensa um decodificador
por subfunção e libera instruções novas (ADC, SBC, SHR, OR, XOR, NOT, TST) a
custo zero no decodificador.

## Contagem de portas

| Parte                                                                  | Portas                                 |
|------------------------------------------------------------------------|----------------------------------------|
| passo 1 (4 → 16)                                                       | 4 NOT + 16 AND de 4 entradas           |
| inversores de F (/F0, /F1, /F2, /F3)                                   | 4 NOT                                  |
| grupos ARIT, LOGICA                                                    | 2 OR                                   |
| M_GRAVA, M_LE, M_CARREGA, PTR_INC                                      | 4 AND de 3 entradas                    |
| ARIT·/F3, MEM_VID, M_GRAVA·F2, SUB, USA_C, SHR, VID_WR, CUR_LD, PTR_LD | 9 AND de 2 entradas                    |
| A_WE (7 termos)                                                        | 6 OR                                   |
| A_SRC0 (4), A_SRC1 (3)                                                 | 3 OR + 2 OR                            |
| RAM_WE, B_IMED, Z_WE                                                   | 3 OR                                   |
| **Total**                                                              | **8 NOT + 29 AND + 16 OR = 53 portas** |

MEM, END_SRC0/1, C_WE, saltos e TEC_RD são fios direto de uma linha `Lk` ou
de um grupo: custo zero.

## Pulsos de escrita

`RAM_WE` e `VID_WR` dizem **se** a instrução grava. O pulso de verdade só
acontece na metade baixa do relógio, quando endereço e dado já pararam:

```
/WE da RAM    = NOT (RAM_WE AND CLK_BAIXO)
grava na VRAM = VID_WR AND CLK_BAIXO
```

(arquivo 20)

## Testes

8 chaves (4 em OP, 4 em F) e 25 LEDs nas saídas. Dica: cole uma etiqueta com
o nome do sinal em cada LED.

1. Percorra a tabela acima linha por linha e compare os LEDs.
2. Nos saltos (OP 8..12), mexa nas 4 chaves de F: só o LED do salto pode
   acender.
3. Em OP = 6 e 7, mexa em F: os LEDs não podem mudar.
4. Em OP = 4, ponha F3 = 1: `A_WE` apaga, `Z_WE` e `C_WE` continuam acesos.
5. Em OP = 15, todos os LEDs apagados para qualquer F.

## Tempo

**0 × CLOCK** (combinacional). Fica logo depois da ROM na fila que precisa
caber em ½ × CLOCK.

| Sinal                           | Portas em fila                             |
|---------------------------------|--------------------------------------------|
| `END_SRC1`, saltos, `TEC_RD`    | 2 (NOT → AND4)                             |
| `B_IMED`, `SUB`, `USA_C`, `SHR` | 3 a 4 (NOT → AND4 → OR → AND)              |
| `A_WE` (o mais longo)           | 7 (NOT → AND4 → OR → AND → 3 níveis de OR) |

Os sinais do caminho crítico (endereço da RAM, mux B, SUB) saem em 2 a 4
portas. `A_WE` só precisa estar pronto no ↑CLK.
