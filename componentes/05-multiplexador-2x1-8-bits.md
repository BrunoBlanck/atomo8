# 05 · Multiplexador 2 × 1 de 8 bits

Uma "chave seletora" de bytes: escolhe qual de duas entradas vai para a saída.
É um componente genérico, usado em vários pontos:

| Onde                                | Entrada 0 (`SEL=0`) | Entrada 1 (`SEL=1`)       | Sinal SEL      | Bits |
|-------------------------------------|---------------------|---------------------------|----------------|------|
| Operando B da ULA                   | dado da RAM         | N (imediato da instrução) | `B_IMED`       | 8    |
| MEMÓRIA (entrada 01 do mux de A)    | dado da RAM         | dado da VRAM              | `MEM_VID`      | 8    |
| NOVO do ponteiro (arquivo 21)       | ponteiro + 1        | A                         | `PTR_LD`       | 8    |
| NOVO do cursor (arquivo 21)         | cursor + 1          | A                         | `CUR_LD`       | 7    |
| enable do registrador A (08)        | Q (segura)          | D (grava)                 | `A_WE`         | 8    |
| enable do ponteiro e do cursor (21) | Q (segura)          | NOVO (grava)              | `WE`           | 8, 7 |
| enable das flags Z e C (09)         | Q (segura)          | Z / C da ULA              | `Z_WE`, `C_WE` | 1    |
| C novo da ULA (07)                  | vai-um final        | A0                        | `SHR`          | 1    |
| próximo PC (13)                     | PC + 1              | destino                   | `TOMA`         | 11   |

O endereço da RAM e o resultado da ULA agora têm 3 opções: usam o mux 4×1
(arquivo 10).

## Pinos

| Pino      | Direção | Largura | Descrição          |
|-----------|---------|---------|--------------------|
| `D0[7:0]` | entrada | 8       | sai quando SEL = 0 |
| `D1[7:0]` | entrada | 8       | sai quando SEL = 1 |
| `SEL`     | entrada | 1       | seletor            |
| `Y[7:0]`  | saída   | 8       | dado escolhido     |

## Circuito de 1 bit (repita 8 vezes)

```
Yn = (D0n AND NOT SEL) OR (D1n AND SEL)

SEL ──┬──────────────┐
      │   ┌───┐      │
      └───┤NOT├─┐    │
          └───┘ │    │
D0n ──────────┬─┴┐   │
              │AND├──┐
              └───┘  │  ┌──┐
D1n ──────────┬──┐   ├──┤OR├── Yn
              │AND├──┘  └──┘
SEL ──────────┴──┘
```

O inversor de SEL é um só para os 8 bits.
Portas: 1 NOT + 16 AND + 8 OR = 25 portas (8 bits).

## Testes

Coloque `D0 = 01010101` e `D1 = 11110000` fixos nas chaves:

| SEL | Y esperado |
|-----|------------|
| 0   | 01010101   |
| 1   | 11110000   |

Depois troque para `D0 = 00000000`, `D1 = 11111111` e repita (confirma que
nenhum bit está preso).

## Tempo

**0 × CLOCK** (combinacional). 3 portas em fila: NOT → AND → OR.
