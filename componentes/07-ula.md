# 07 · ULA (Unidade Lógica e Aritmética)

Junta os blocos 02 a 06 e a unidade lógica (04). Faz soma, subtração (com ou
sem o vai-um anterior), deslocamento à direita e qualquer função lógica de
2 entradas. É **combinacional**: não tem relógio, a saída muda assim que as
entradas mudam.

Entrega o resultado `R`, a flag `Z` e o `C` novo. Quem decide se as flags
são gravadas é o decodificador (`Z_WE`, `C_WE`, arquivo 09).

## Pinos

| Pino     | Direção | Largura | Descrição                                |
|----------|---------|---------|------------------------------------------|
| `A[7:0]` | entrada | 8       | registrador A                            |
| `B[7:0]` | entrada | 8       | mux B (RAM ou N, arquivo 05)             |
| `SUB`    | entrada | 1       | inverte B e vai-um de entrada = 1        |
| `USA_C`  | entrada | 1       | vai-um de entrada = flag C (ADC, SBC)    |
| `SHR`    | entrada | 1       | resultado = A >> 1                       |
| `LOGICA` | entrada | 1       | resultado = unidade lógica               |
| `T[3:0]` | entrada | 4       | tabela-verdade (bits 11..8 da instrução) |
| `C`      | entrada | 1       | flag C atual (arquivo 09)                |
| `R[7:0]` | saída   | 8       | resultado                                |
| `Z`      | saída   | 1       | R == 0                                   |
| `C_NOVO` | saída   | 1       | vai-um final, ou A0 no SHR               |

`SUB`, `USA_C` e `SHR` são os bits 8, 9 e 10 da instrução ARIT, passados por
uma AND com `ARIT` no decodificador (arquivo 17). `T` liga direto nos
bits 11..8.

## As partes

| Parte                   | Arquivo | O que faz                                  | Portas  |
|-------------------------|---------|--------------------------------------------|---------|
| inversor controlado     | 03      | `B' = B XOR SUB`                           | 8       |
| vai-um de entrada (CIN) | aqui    | `(USA_C·C) + (/USA_C·SUB)`                 | 4       |
| somador 8 bits          | 02      | `SOMA, COUT = A + B' + CIN`                | 40      |
| unidade lógica          | 04      | `LÓGICA = T[2·An + Bn]` (usa o B original) | 72      |
| SHR                     | aqui    | `R6..R0 = A7..A1`, `R7 = 0` (só fios)      | 0       |
| mux de resultado 4×1    | 10      | escolhe SOMA, LÓGICA ou SHR                | 62      |
| detector de zero        | 06      | `Z = NOR(R7..R0)`                          | 8       |
| mux do C novo (1 bit)   | 05      | `C_NOVO = SHR ? A0 : COUT`                 | 4       |
| **total**               |         |                                            | **198** |

Vai-um de entrada (1 NOT + 2 AND + 1 OR):

```
USA_C ──┬────────────┐
        │            AND ──┐
C ──────┼────────────┘     │
        └─[NOT]──┐         OR ── CIN
SUB ─────────────AND ──────┘
```

Mux de resultado: o mesmo circuito do arquivo 10, com `S1 = SHR`,
`S0 = LOGICA` e a entrada 11 ligada em 0. (Se quiser economizar: com a
entrada 11 em 0 saem 9 AND e 8 OR, ficando 45 portas.)

## Seleção de operação

| Operação | SUB | USA_C | SHR | LOGICA | R               | C_NOVO              | Instruções                              |
|----------|-----|-------|-----|--------|-----------------|---------------------|-----------------------------------------|
| ADD      | 0   | 0     | 0   | 0      | A + B           | vai-um final        | `ADD m`, `ADDI n`                       |
| SUB      | 1   | 0     | 0   | 0      | A − B           | 1 se A ≥ B          | `SUB m`, `SUBI n`                       |
| ADC      | 0   | 1     | 0   | 0      | A + B + C       | vai-um final        | `ADC m`, `ADCI n`                       |
| SBC      | 1   | 1     | 0   | 0      | A − B − (1 − C) | 1 se sem empréstimo | `SBC m`, `SBCI n`                       |
| SHR      | 0   | 0     | 1   | 0      | A >> 1          | A0                  | `SHR`                                   |
| CMP      | 1   | 0     | 0   | 0      | A − B           | 1 se A ≥ B          | `CMP m`, `CMPI n`                       |
| LOG      | 0   | 0     | 0   | 1      | T(A, B) por bit | (não gravado)       | `AND`, `OR`, `XOR`, `TST`, `NOT`, `LOG` |

- **CMP** é um SUB em que A não é gravado (bit 11 = NG, o decodificador
  desliga `A_WE`). A ULA não sabe a diferença.
- No **LOG** o C da ULA sai qualquer, mas `C_WE = 0`: a flag C não muda.
- `SHR` e `LOGICA` nunca vêm juntos (seriam a entrada 11 do mux, ligada em 0).

## Regra do C (padrão 6502)

| Depois de | C = 1 quer dizer           | C = 0 quer dizer         |
|-----------|----------------------------|--------------------------|
| ADD / ADC | passou de 255              | coube em 8 bits          |
| SUB / CMP | **A ≥ B** (sem empréstimo) | A < B (pediu empréstimo) |
| SBC       | sem empréstimo             | pediu empréstimo         |
| SHR       | o bit que saiu (A0) era 1  | A0 era 0                 |

Exemplo da bola: `CMPI 31` / `JNC X` salta se A < 31.
Para SBC encadeado, comece com C = 1 (por exemplo depois de um SUB).

## Ligação interna

```
                       B[7:0]
                         │
              SUB ──►[03 INVERSOR]
                         │ B'
  USA_C, C, SUB ──►[CIN]─┤
                         ▼
 A[7:0] ──┬─────►[02 SOMADOR]─── COUT ──────────► D0 ┐
          │              │ SOMA                      │ [05 MUX 1 bit] ──► C_NOVO
          ├── A0 ────────┼─────────────────────► D1 ┘  SEL = SHR
          │              └──────────────► D0 (00) ┐
          ├──►[04 LÓGICA]──────────────► D1 (01) ┤
          │      ▲ B, T                           │ [10 MUX 4×1]
          └──► fios A>>1 ──────────────► D2 (10) ┤ S1 = SHR
                                   0 ──► D3 (11) ┘ S0 = LOGICA
                                                  │
                                                R[7:0] ──►[06 ZERO]──► Z
```

A unidade lógica recebe o **B original**, não o B' (no LOG o SUB é 0 de
qualquer forma; ligar no original deixa claro).

## Tabelas de teste (geradas pelo simulador)

`ULA().calcula(a, b, sub, usa_c, shr, logica, tabela, c)` → `(R, Z, C_NOVO)`.

### ADD (SUB=0, USA_C=0, SHR=0, LOGICA=0)

| A   | B   | R   | Z   | C   |
|-----|-----|-----|-----|-----|
| 0   | 0   | 0   | 1   | 0   |
| 1   | 1   | 2   | 0   | 0   |
| 5   | 3   | 8   | 0   | 0   |
| 200 | 100 | 44  | 0   | 1   |
| 255 | 1   | 0   | 1   | 1   |
| 128 | 128 | 0   | 1   | 1   |
| 15  | 240 | 255 | 0   | 0   |
| 255 | 255 | 254 | 0   | 1   |

### SUB / CMP (SUB=1)

| A   | B   | R   | Z   | C   | A ≥ B? |
|-----|-----|-----|-----|-----|--------|
| 0   | 0   | 0   | 1   | 1   | sim    |
| 5   | 3   | 2   | 0   | 1   | sim    |
| 3   | 5   | 254 | 0   | 0   | não    |
| 200 | 100 | 100 | 0   | 1   | sim    |
| 15  | 240 | 31  | 0   | 0   | não    |
| 63  | 63  | 0   | 1   | 1   | sim    |
| 0   | 1   | 255 | 0   | 0   | não    |
| 255 | 255 | 0   | 1   | 1   | sim    |

### ADC (USA_C=1)

| A   | B   | C antes | R   | Z   | C novo |
|-----|-----|---------|-----|-----|--------|
| 5   | 3   | 0       | 8   | 0   | 0      |
| 5   | 3   | 1       | 9   | 0   | 0      |
| 255 | 0   | 1       | 0   | 1   | 1      |
| 200 | 100 | 1       | 45  | 0   | 1      |

### SBC (SUB=1, USA_C=1)

| A   | B   | C antes | R   | Z   | C novo |
|-----|-----|---------|-----|-----|--------|
| 5   | 3   | 1       | 2   | 0   | 1      |
| 5   | 3   | 0       | 1   | 0   | 1      |
| 0   | 0   | 0       | 255 | 0   | 0      |
| 3   | 5   | 1       | 254 | 0   | 0      |

### SHR (SHR=1)

| A              | R              | Z   | C   |
|----------------|----------------|-----|-----|
| 0 (00000000)   | 0 (00000000)   | 1   | 0   |
| 1 (00000001)   | 0 (00000000)   | 1   | 1   |
| 2 (00000010)   | 1 (00000001)   | 0   | 0   |
| 255 (11111111) | 127 (01111111) | 0   | 1   |
| 170 (10101010) | 85 (01010101)  | 0   | 0   |
| 85 (01010101)  | 42 (00101010)  | 0   | 1   |

### LOG (LOGICA=1)

| Tabela   | A   | B   | R   | Z   |
|----------|-----|-----|-----|-----|
| 1000 AND | 15  | 240 | 0   | 1   |
| 1000 AND | 255 | 8   | 8   | 0   |
| 1110 OR  | 15  | 240 | 255 | 0   |
| 0110 XOR | 255 | 255 | 0   | 1   |
| 0110 XOR | 255 | 8   | 247 | 0   |
| 1100 TST | 0   | 0   | 0   | 1   |
| 1100 TST | 37  | 0   | 37  | 0   |
| 0011 NOT | 170 | 0   | 85  | 0   |

`ANDI 8` com parede = 255 é o uso mais comum no jogo: pega um bit da célula.

## Como testar sozinho

- 16 chaves (A, B), 4 chaves (SUB, USA_C, SHR, LOGICA), 4 chaves (T),
  1 chave (C).
- 10 LEDs (R, Z, C_NOVO).
- Rode as tabelas acima. Pistas:
  - ADD certo e SUB errado → inversor (03) ou CIN.
  - ADC/SBC errados com ADD/SUB certos → circuito do CIN (USA_C).
  - SHR errado só no C → mux do C novo.
  - LOG errado → unidade lógica (04), teste com `A = 11001100`, `B = 10101010`.

## Tempo

**0 × CLOCK**: a ULA inteira é combinacional. R, Z e C_NOVO ficam prontos
dentro do mesmo ciclo e são gravados (em A e nas flags) na borda de subida
seguinte.

Caminho mais longo: B → XOR (03) → somador (02, vai-um em cadeia) → mux de
resultado 4×1 → zero (06).

| Trecho               | Portas em fila    |
|----------------------|-------------------|
| inversor             | 1                 |
| somador (pior caso)  | 24                |
| mux de resultado 4×1 | 3 (AND → OR → OR) |
| detector de zero     | 4                 |
| **total**            | **~32**           |

- O mux 4×1 tem 1 porta a mais que o mux 2×1 antigo.
- O CIN usa só sinais do decodificador e a flag C, que chegam bem antes de B
  (que passa pela RAM): fica fora do caminho crítico.
- A unidade lógica (4 portas) e o SHR (fios) correm em paralelo com o
  somador.

Junto com ROM, decodificador, RAM e mux de A, tudo precisa caber em
**½ × CLOCK** (arquivo 20).

## Correspondência com o simulador

`ULA.calcula(a, b, sub, usa_c, shr, logica, tabela, c)` em `hardware.py` faz
exatamente isso, porta por porta: CIN, somador com `bi ^ sub`, `mux4` da
unidade lógica, fios do SHR, `mux4_n(shr, logica, ...)` de resultado, NOR
dos 8 bits e `mux2(shr, cout, A0)`.
