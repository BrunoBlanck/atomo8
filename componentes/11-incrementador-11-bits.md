# 11 · Incrementador de 11 bits (PC + 1)

Calcula o endereço da próxima instrução. É um somador simplificado: soma 1,
então basta uma cadeia de **meio-somadores**.

## Pinos

| Pino      | Direção | Largura                                 |
|-----------|---------|-----------------------------------------|
| `P[10:0]` | entrada | 11 (valor atual do PC)                  |
| `Y[10:0]` | saída   | 11 (P + 1, voltando a 0 depois de 2047) |

## Meio-somador (1 bit)

```
Yn   = Pn XOR Cn
Cn+1 = Pn AND Cn          com C0 = 1
```

Como `C0 = 1`, o bit 0 simplifica para `Y0 = NOT P0`, `C1 = P0`.

## Ligação

```
 1 ─►[MS0]─c1─►[MS1]─c2─► ... ─c10─►[MS10]─► (vai-um descartado)
      P0         P1                   P10
      Y0         Y1                   Y10
```

Portas: 10 XOR + 10 AND + 1 NOT. Fica separado do registrador para ficar
simples de entender.

## Outros usos (k bits)

O mesmo circuito, com k meio-somadores em vez de 11, avança o
registrador-ponteiro (arquivo 21):

| Onde            | k  | Portas                  |
|-----------------|----|-------------------------|
| PC              | 11 | 10 XOR + 10 AND + 1 NOT |
| Ponteiro da RAM | 8  | 7 XOR + 7 AND + 1 NOT   |
| Cursor da VRAM  | 7  | 6 XOR + 6 AND + 1 NOT   |

## Testes

| P (decimal) | P (binário) | Y (binário) |
|-------------|-------------|-------------|
| 0           | 00000000000 | 00000000001 |
| 1           | 00000000001 | 00000000010 |
| 255         | 00011111111 | 00100000000 |
| 1023        | 01111111111 | 10000000000 |
| 1366        | 10101010110 | 10101010111 |
| 2047        | 11111111111 | 00000000000 |

`255 → 256` é importante: é a passagem de página (bits 7 → 8).

## Tempo

**0 × CLOCK** (combinacional). Pior caso 2047 → 0: o vai-um atravessa
10 portas AND em fila. Como começa junto com o ciclo e só precisa estar pronto
na borda seguinte, sobra tempo.
