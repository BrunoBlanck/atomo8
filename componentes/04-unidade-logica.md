# 04 · Unidade lógica programável (8 bits)

Faz **qualquer** função lógica de 2 entradas, bit a bit: AND, OR, XOR, NOT...
Quem escolhe a função é a própria instrução: os bits 11..8 (`T3..T0`) são a
**tabela-verdade** da função.

A ideia vem do Gigatron: um mux usado "ao contrário" vira uma porta
programável. Em vez de escolher entre dados, os bits `An` e `Bn` vão na
**seleção** e a tabela-verdade `T` vai nos **dados**. O mux devolve a linha
da tabela que corresponde a (An, Bn).

## Pinos

| Pino     | Direção | Largura | Descrição                                    |
|----------|---------|---------|----------------------------------------------|
| `A[7:0]` | entrada | 8       | registrador A                                |
| `B[7:0]` | entrada | 8       | operando B (RAM ou N, **sem** o inversor 03) |
| `T[3:0]` | entrada | 4       | tabela-verdade = bits 11..8 da instrução     |
| `Y[7:0]` | saída   | 8       | `Yn = T[2·An + Bn]`                          |

## Equação por bit

```
Yn = (T0 AND /An AND /Bn)      linha A=0 B=0
   OR (T1 AND /An AND  Bn)     linha A=0 B=1
   OR (T2 AND  An AND /Bn)     linha A=1 B=0
   OR (T3 AND  An AND  Bn)     linha A=1 B=1
```

É o mux 4×1 do arquivo 10 com `S1 = An`, `S0 = Bn` e `D0..D3 = T0..T3`.
Como a seleção muda de bit para bit, cada bit tem os seus 2 NOT.

## Circuito de 1 bit (repita 8 vezes)

```
An ──┬──────────── An          T0 ──┐
     └─[NOT]────── /An         /An ─┤AND3── P0 ──┐
Bn ──┬──────────── Bn          /Bn ─┘            ├─OR──┐
     └─[NOT]────── /Bn         T1 ──┐            │     │
                               /An ─┤AND3── P1 ──┘     │
                               Bn ──┘                  ├─OR── Yn
                               T2 ──┐                  │
                               An ──┤AND3── P2 ──┐     │
                               /Bn ─┘            ├─OR──┘
                               T3 ──┐            │
                               An ──┤AND3── P3 ──┘
                               Bn ──┘
```

Os fios `T0..T3` vão para os 8 bits.

| Por bit             | Total (8 bits)       |
|---------------------|----------------------|
| 2 NOT               | 16 NOT               |
| 4 AND de 3 entradas | 32 AND de 3 entradas |
| 3 OR de 2 entradas  | 24 OR de 2 entradas  |
| **9 portas**        | **72 portas**        |

Substitui as 8 AND da ULA antiga (+64 portas).

## As 16 tabelas = as 16 funções de 2 entradas

`T` tem 4 bits → 16 tabelas possíveis, e existem exatamente 16 funções de 2
entradas. Todas saem do mesmo circuito (conferido no simulador):

| T3 T2 T1 T0 | A=0 B=0 | A=0 B=1 | A=1 B=0 | A=1 B=1 | Função      |
|-------------|---------|---------|---------|---------|-------------|
| 0000        | 0       | 0       | 0       | 0       | sempre 0    |
| 0001        | 1       | 0       | 0       | 0       | NOR         |
| 0010        | 0       | 1       | 0       | 0       | /A AND B    |
| 0011        | 1       | 1       | 0       | 0       | **NOT A**   |
| 0100        | 0       | 0       | 1       | 0       | A AND /B    |
| 0101        | 1       | 0       | 1       | 0       | NOT B       |
| 0110        | 0       | 1       | 1       | 0       | **XOR**     |
| 0111        | 1       | 1       | 1       | 0       | NAND        |
| 1000        | 0       | 0       | 0       | 1       | **AND**     |
| 1001        | 1       | 0       | 0       | 1       | XNOR        |
| 1010        | 0       | 1       | 0       | 1       | passa B     |
| 1011        | 1       | 1       | 0       | 1       | /A OR B     |
| 1100        | 0       | 0       | 1       | 1       | **passa A** |
| 1101        | 1       | 0       | 1       | 1       | A OR /B     |
| 1110        | 0       | 1       | 1       | 1       | **OR**      |
| 1111        | 1       | 1       | 1       | 1       | sempre 1    |

## Funções com nome no montador

| Tabela | Função  | Instruções        | Quem usa                             |
|--------|---------|-------------------|--------------------------------------|
| 1000   | AND     | `AND m`, `ANDI n` | doom (`ANDI 2^d` pega um bit), bola  |
| 1110   | OR      | `OR m`, `ORI n`   | (disponível)                         |
| 0110   | XOR     | `XOR m`, `XORI n` | bola (desenha e apaga com `XOR M`)   |
| 1100   | passa A | `TST` (N = 0)     | doom, bola: Z = (A == 0), A não muda |
| 0011   | NOT A   | `NOT` (N = 0)     | (disponível)                         |

Forma genérica: `LOG t m` / `LOGI t n` com qualquer tabela `t`.

## Testes (gerados pelo simulador)

`ULA().calcula(a, b, 0, 0, 0, 1, tabela, 0)` (logica = 1):

| Tabela     | A              | B              | Y              |
|------------|----------------|----------------|----------------|
| 1000 AND   | 5 (00000101)   | 3 (00000011)   | 1 (00000001)   |
| 1000 AND   | 200 (11001000) | 100 (01100100) | 64 (01000000)  |
| 1000 AND   | 255 (11111111) | 8 (00001000)   | 8 (00001000)   |
| 1110 OR    | 5 (00000101)   | 3 (00000011)   | 7 (00000111)   |
| 1110 OR    | 200 (11001000) | 100 (01100100) | 236 (11101100) |
| 0110 XOR   | 5 (00000101)   | 3 (00000011)   | 6 (00000110)   |
| 0110 XOR   | 255 (11111111) | 8 (00001000)   | 247 (11110111) |
| 1100 A     | 37 (00100101)  | 0 (00000000)   | 37 (00100101)  |
| 0011 NOT A | 170 (10101010) | 0 (00000000)   | 85 (01010101)  |
| 0011 NOT A | 255 (11111111) | 0 (00000000)   | 0 (00000000)   |

**Teste de todas as tabelas de uma vez:** com `A = 11001100` e
`B = 10101010`, cada par de bits passa pelas 4 linhas da tabela, e a saída
repete a própria tabela duas vezes: `Y = T3 T2 T1 T0 T3 T2 T1 T0`.

| T    | Y        |
|------|----------|
| 0000 | 00000000 |
| 0110 | 01100110 |
| 1000 | 10001000 |
| 1100 | 11001100 |
| 1110 | 11101110 |
| 1111 | 11111111 |

## Como testar sozinho

- 16 chaves (A, B), 4 chaves (T), 8 LEDs (Y).
- Fixe `A = 11001100`, `B = 10101010` e mexa só nas 4 chaves de T: os LEDs
  copiam as chaves, duas vezes. Se um LED não acompanha, a porta daquele bit
  e daquela linha está errada.
- Depois confira a tabela de testes acima.

## Tempo

**0 × CLOCK** (combinacional). 4 portas em fila: NOT → AND3 → OR → OR.
Fica em paralelo com o somador (02), que é bem mais lento: não pesa no
caminho crítico.

## Correspondência com o simulador

Em `ULA.calcula()` (`hardware.py`), cada bit faz
`mux4(ai, bi, T0, T1, T2, T3)`: An e Bn na seleção, a tabela nos dados.
