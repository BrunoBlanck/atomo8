# 10 · Multiplexador 4 × 1 de 8 bits (entrada do registrador A)

Escolhe de onde vem o valor novo de A. O mesmo circuito aparece em outros
pontos (ver o fim do arquivo).

| `A_SRC` | Entrada                                            | Instruções                                                              |
|---------|----------------------------------------------------|-------------------------------------------------------------------------|
| 00      | `N[7:0]` (operando da instrução)                   | LDI                                                                     |
| 01      | MEMÓRIA = RAM ou VRAM (mux 2×1 `MEM_VID`, arq. 05) | LD, LDR, LDP (RAM); VIN (VRAM)                                          |
| 10      | resultado da ULA (arquivo 07)                      | ARIT/ARITI (ADD, SUB, ADC, SBC, SHR), LOG/LOGI (AND, OR, XOR, TST, NOT) |
| 11      | teclado (arquivo 19)                               | IN                                                                      |

CMP passa pela entrada 10, mas não grava A (`A_WE = 0`).

A entrada 11 é ligada **direto** na saída do teclado: é o único dispositivo de
entrada, então não há barramento compartilhado nem número de porta.

## Pinos

| Pino                   | Direção | Largura |
|------------------------|---------|---------|
| `D0[7:0]` .. `D3[7:0]` | entrada | 4 × 8   |
| `S[1:0]`               | entrada | 2       |
| `Y[7:0]`               | saída   | 8       |

## Circuito de 1 bit (repita 8 vezes)

Primeiro decodifique `S` em 4 linhas (feito **uma vez** só para os 8 bits):

```
L0 = NOT S1 AND NOT S0
L1 = NOT S1 AND     S0
L2 =     S1 AND NOT S0
L3 =     S1 AND     S0
```

Depois, para cada bit:

```
Yn = (D0n AND L0) OR (D1n AND L1) OR (D2n AND L2) OR (D3n AND L3)
```

Portas: 2 NOT + 4 AND (decodificador) + 32 AND + 24 OR de 2 entradas
(ou 8 OR de 4 entradas) = 62 portas.

Alternativa equivalente: dois níveis de mux 2×1 do arquivo 05
(`S0` escolhe entre D0/D1 e entre D2/D3; `S1` escolhe o resultado final).

## Testes

Coloque valores diferentes e fixos:
`D0 = 00000001`, `D1 = 00000010`, `D2 = 00000100`, `D3 = 10000000`.

| S1  | S0  | Y        |
|-----|-----|----------|
| 0   | 0   | 00000001 |
| 0   | 1   | 00000010 |
| 1   | 0   | 00000100 |
| 1   | 1   | 10000000 |

Depois inverta todos os D (`11111110`, `11111101`, ...) e repita.

## Tempo

**0 × CLOCK** (combinacional). É o último bloco antes do registrador A:
precisa ficar estável antes da borda de subida.

## Outros usos do mesmo circuito

| Onde                       | S1, S0                 | 00                        | 01             | 10                              | 11      |
|----------------------------|------------------------|---------------------------|----------------|---------------------------------|---------|
| entrada do registrador A   | `A_SRC1`, `A_SRC0`     | N                         | MEMÓRIA        | ULA                             | teclado |
| endereço da RAM            | `END_SRC1`, `END_SRC0` | N (LD, ST, ARIT m, LOG m) | A (LDR)        | ponteiro (LDP, STP, arquivo 21) | sem uso |
| resultado da ULA (arq. 07) | `SHR`, `LOGICA`        | soma                      | unidade lógica | A >> 1                          | 0       |
| unidade lógica (arq. 04)   | `An`, `Bn` (por bit)   | T0                        | T1             | T2                              | T3      |

Na unidade lógica o mux é usado **ao contrário**: os bits do dado vão na
seleção e a tabela-verdade da instrução vai nas entradas. Por isso lá o
decodificador de S é refeito em cada bit.
