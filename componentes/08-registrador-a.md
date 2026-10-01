# 08 · Registrador A (acumulador, 8 bits)

O único registrador de dados da CPU. Guarda 1 byte. Só muda na **borda de
subida do relógio** e só se `A_WE = 1`.

## Pinos

| Pino     | Direção | Largura | Descrição                               |
|----------|---------|---------|-----------------------------------------|
| `D[7:0]` | entrada | 8       | valor novo (vem do mux 4×1, arquivo 10) |
| `WE`     | entrada | 1       | 1 = grava na próxima ↑CLK (`A_WE`)      |
| `CLK`    | entrada | 1       | relógio                                 |
| `Q[7:0]` | saída   | 8       | valor guardado (sempre disponível)      |

## Circuito de 1 bit (repita 8 vezes)

```
           ┌──────────────┐
Dn ──► D1  │  MUX 2x1     │         ┌──────────┐
Qn ──► D0  │  SEL = WE    ├── d ───►│ D   FF   │── Qn ──┐
           └──────────────┘         │    ↑CLK  │        │
                                    └──────────┘        │
            ▲                                           │
            └─────────── realimentação ─────────────────┘
```

Quando WE = 0, o flip-flop regrava o próprio valor (não muda).
**Não** faça "AND do relógio com WE" (clock gating): gera pulsos falsos.

Portas: 8 flip-flops D + mux 2×1 de 8 bits (arquivo 05: 1 NOT + 16 AND + 8 OR).

## O flip-flop D por dentro (8 NAND + 1 NOT)

O mesmo flip-flop é usado em todos os registradores (A, flags, PC, ponteiro,
cursor, teclado). São **2 latches D em fila** (mestre e escravo):

```
latch D (4 NAND):   S' = NAND(D, EN)      Q  = NAND(S', /Q)
                    R' = NAND(S', EN)     /Q = NAND(R', Q)

mestre: D = entrada,   EN = NOT CLK   → copia D enquanto CLK = 0
escravo: D = Q mestre, EN = CLK       → copia o mestre quando CLK = 1
```

Resultado: Q só muda na **borda de subida** do CLK, com o valor que D tinha
logo antes. Clear (PC, cursor): `/CLR = 0` força Q = 0 sem esperar o relógio.

No esquema interativo (`esquema/`), botão **Visualizar em portas lógicas**
mostra este circuito e deixa trocar D e CLK com chaves.

## De onde vem D

O mux 4×1 de A (arquivo 10) escolhe:

| A_SRC | Entrada                                      |
|-------|----------------------------------------------|
| 00    | N (imediato da instrução)                    |
| 01    | MEMÓRIA: RAM ou VRAM (mux 2×1 `MEM_VID`, 05) |
| 10    | resultado da ULA                             |
| 11    | teclado                                      |

## Estado ao ligar

Aleatório. O programa sempre grava A antes de usar, não precisa de reset.

## Testes

| Passo | D        | WE  | Ação      | Q esperado                  |
|-------|----------|-----|-----------|-----------------------------|
| 1     | 10101010 | 1   | ↑CLK      | 10101010                    |
| 2     | 11110000 | 0   | ↑CLK      | 10101010 (não mudou)        |
| 3     | 11110000 | 1   | sem pulso | 10101010 (só muda na borda) |
| 4     | 11110000 | 1   | ↑CLK      | 11110000                    |
| 5     | 00000000 | 1   | ↑CLK      | 00000000                    |

Use um **botão com debounce** como relógio (arquivo 20), ou um 555 lento.

## Tempo

- **Gravar: 1 × CLOCK.** O valor em D entra na borda de subida; o novo Q já
  vale para a instrução seguinte.
- D precisa estar estável **antes** da borda: por isso a ULA e os muxes têm
  a metade alta do pulso (½ × CLOCK) para se acertar.
