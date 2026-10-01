# 02 · Somador de 8 bits (ripple-carry)

Soma dois bytes. São **8 somadores completos** (arquivo 01) ligados em cadeia:
o `COUT` de cada bit entra no `CIN` do bit seguinte.

## Pinos

| Pino     | Direção | Largura | Descrição                                                  |
|----------|---------|---------|------------------------------------------------------------|
| `A[7:0]` | entrada | 8       | primeiro número                                            |
| `B[7:0]` | entrada | 8       | segundo número                                             |
| `CIN`    | entrada | 1       | vai-um de entrada (vem do circuito CIN da ULA, arquivo 07) |
| `S[7:0]` | saída   | 8       | resultado (só os 8 bits de baixo)                          |
| `COUT`   | saída   | 1       | vai-um final (vai para a flag C, arquivos 07 e 09)         |

## Ligação

```
 CIN ─► [SC0] ─c1─► [SC1] ─c2─► [SC2] ─c3─► ... ─c7─► [SC7] ─► COUT
         A0 B0       A1 B1       A2 B2                 A7 B7
          │           │           │                     │
          S0          S1          S2                    S7
```

Cada `[SCn]` é um somador completo do arquivo 01.
Portas: 8 × 5 = 40 (16 XOR + 16 AND + 8 OR).

## Testes

Com `CIN = 0` (soma normal):

| A              | B              | S              | COUT |
|----------------|----------------|----------------|------|
| 0 (00000000)   | 0 (00000000)   | 0 (00000000)   | 0    |
| 1 (00000001)   | 1 (00000001)   | 2 (00000010)   | 0    |
| 5 (00000101)   | 3 (00000011)   | 8 (00001000)   | 0    |
| 15 (00001111)  | 240 (11110000) | 255 (11111111) | 0    |
| 170 (10101010) | 85 (01010101)  | 255 (11111111) | 0    |
| 63 (00111111)  | 63 (00111111)  | 126 (01111110) | 0    |
| 200 (11001000) | 100 (01100100) | 44 (00101100)  | 1    |
| 128 (10000000) | 128 (10000000) | 0 (00000000)   | 1    |
| 255 (11111111) | 1 (00000001)   | 0 (00000000)   | 1    |
| 255 (11111111) | 255 (11111111) | 254 (11111110) | 1    |

Com `CIN = 1` (soma + 1):

| A   | B              | S   | COUT |
|-----|----------------|-----|------|
| 0   | 0              | 1   | 0    |
| 255 | 0              | 0   | 1    |
| 5   | 252 (11111100) | 2   | 1    |

O caso `255 + 1` é o **pior caso de atraso**: o vai-um precisa atravessar os
8 bits. Teste esse caso por último e confira se todos os LEDs de S apagam
e COUT acende.

## Como testar sozinho

- 16 chaves (A e B) + 1 chave (CIN), 9 LEDs (S e COUT).
- Primeiro teste só o bit 0 e o bit 7 isolados; depois a tabela inteira.

## Tempo

**0 × CLOCK** (combinacional), mas é o bloco **mais lento** da CPU: no pior
caso o vai-um atravessa 8 somadores em fila (8 × 3 = 24 portas).

Por isso ele é o que mais pesa no menor CLOCK possível (arquivo 20). Se um
dia o CLOCK ficar curto demais, o primeiro sintoma é `255 + 1` dar errado.
