# 13 · Multiplexador do próximo PC (2 × 1 de 11 bits)

Decide para onde o programa vai depois da instrução atual.

| `TOMA` (arquivo 14) | Próximo PC                       |
|---------------------|----------------------------------|
| 0                   | `PC + 1` (arquivo 11)            |
| 1                   | `DEST` = bits 10..0 da instrução |

Não há sub-rotinas nem endereço de retorno: só estas duas opções.

## Pinos

| Pino         | Direção | Largura | Descrição                  |
|--------------|---------|---------|----------------------------|
| `INC[10:0]`  | entrada | 11      | PC + 1                     |
| `DEST[10:0]` | entrada | 11      | fios 10..0 da saída da ROM |
| `TOMA`       | entrada | 1       | salto aceito               |
| `Y[10:0]`    | saída   | 11      | vai para o D do PC         |

## De onde vem DEST

A instrução tem 16 bits: `[OP 15..12][0][PÁGINA 10..8][N 7..0]`.
`DEST` são simplesmente os **fios 10 a 0 da saída da ROM**. Não há conta.

## Circuito

É o mesmo multiplexador 2 × 1 do arquivo 05, só que com 11 bits em vez de 8:

```
Yn = (INCn AND NOT TOMA) OR (DESTn AND TOMA)
```

Portas: 1 NOT + 22 AND + 11 OR.

## Testes

`INC = 00000000001`, `DEST = 10100000000`:

| TOMA | Y           |
|------|-------------|
| 0    | 00000000001 |
| 1    | 10100000000 |

Depois troque para `INC = 11111111111`, `DEST = 00000000000` e repita
(confirma que nenhum bit está preso).

## Tempo

**0 × CLOCK** (combinacional).
