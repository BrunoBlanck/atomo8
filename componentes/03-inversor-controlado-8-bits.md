# 03 · Inversor controlado de 8 bits (8 × XOR)

Permite que o mesmo somador faça **subtração**. Quando `INV = 1`, todos os bits
de B são invertidos; quando `INV = 0`, B passa sem mudança.

Por que funciona: `A - B = A + (NOT B) + 1`. O `NOT B` vem deste bloco e o
`+1` vem do `CIN = 1` do somador (o circuito CIN da ULA põe 1 quando
`SUB = 1` e `USA_C = 0`; no SBC o `+1` vem da flag C).

## Pinos

| Pino     | Direção | Largura | Descrição                     |
|----------|---------|---------|-------------------------------|
| `B[7:0]` | entrada | 8       | byte original                 |
| `INV`    | entrada | 1       | 1 = inverte, 0 = passa direto |
| `Y[7:0]` | saída   | 8       | `B XOR INV` em cada bit       |

## Circuito

```
B0 ──┐          B1 ──┐                B7 ──┐
     XOR ── Y0       XOR ── Y1  ...        XOR ── Y7
INV ─┘         INV ──┘               INV ──┘
```

Uma porta XOR por bit; o fio `INV` vai para as 8 portas.
Portas: 8 XOR.

Na ULA, `INV` é o sinal `SUB` = bit 8 da instrução AND `ARIT`
(decodificador, arquivo 17): ligado em SUB, SBC e CMP.

## Tabela verdade de 1 bit

| B   | INV | Y   |
|-----|-----|-----|
| 0   | 0   | 0   |
| 1   | 0   | 1   |
| 0   | 1   | 1   |
| 1   | 1   | 0   |

## Testes do byte

| B        | INV | Y        |
|----------|-----|----------|
| 00000000 | 0   | 00000000 |
| 10100101 | 0   | 10100101 |
| 00000000 | 1   | 11111111 |
| 10100101 | 1   | 01011010 |
| 11111111 | 1   | 00000000 |

## Como testar sozinho

8 chaves em B, 1 chave em INV, 8 LEDs em Y. Com INV desligado os LEDs copiam
as chaves; ligando INV todos os LEDs trocam de estado.

## Tempo

**0 × CLOCK** (combinacional). Só 1 porta XOR no caminho.
