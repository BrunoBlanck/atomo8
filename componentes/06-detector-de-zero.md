# 06 · Detector de zero (flag Z)

Diz se um byte é **zero**. A saída é 1 somente quando os 8 bits são 0.

## Pinos

| Pino     | Direção | Largura | Descrição         |
|----------|---------|---------|-------------------|
| `R[7:0]` | entrada | 8       | resultado da ULA  |
| `Z`      | saída   | 1       | 1 se R = 00000000 |

## Equação

```
Z = NOT (R0 OR R1 OR R2 OR R3 OR R4 OR R5 OR R6 OR R7)     (NOR de 8 entradas)
```

## Circuito com portas de 2 entradas

```
R0 ─┐OR─┐
R1 ─┘   │OR─┐
R2 ─┐OR─┘   │
R3 ─┘       │OR──┐
R4 ─┐OR─┐   │    │  ┌───┐
R5 ─┘   │OR─┘    └──┤NOT├── Z
R6 ─┐OR─┘           └───┘
R7 ─┘
```

7 portas OR em árvore + 1 NOT = 8 portas (3 níveis de OR em vez de 7 em fila = mais rápido).

## Testes

| R        | Z   |
|----------|-----|
| 00000000 | 1   |
| 00000001 | 0   |
| 10000000 | 0   |
| 00010000 | 0   |
| 11111111 | 0   |

Teste também ligando **um bit por vez** (8 testes): Z tem que apagar em todos.

## Tempo

**0 × CLOCK** (combinacional). 4 portas em fila: 3 níveis de OR + 1 NOT.
