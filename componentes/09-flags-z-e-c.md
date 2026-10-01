# 09 · Flags Z e C

Dois flip-flops que guardam o resultado da **última operação da ULA** que
mexeu neles. Os saltos condicionais decidem olhando para eles (arquivo 14).

| Flag | Guarda                                           | Saltos      |
|------|--------------------------------------------------|-------------|
| `Z`  | o resultado foi zero                             | `JZ`, `JNZ` |
| `C`  | vai-um final (ADD) / A ≥ B (SUB, CMP) / A0 (SHR) | `JC`, `JNC` |

As duas são **o mesmo circuito** montado duas vezes: flip-flop D com enable.

## Pinos (de cada flag)

| Pino   | Direção | Z                       | C                                  |
|--------|---------|-------------------------|------------------------------------|
| `D_IN` | entrada | `Z` da ULA (arquivo 07) | `C_NOVO` da ULA                    |
| `WE`   | entrada | `Z_WE` do decodificador | `C_WE` do decodificador            |
| `CLK`  | entrada | relógio                 | relógio                            |
| `Q`    | saída   | `Z` → lógica de salto   | `C` → lógica de salto e CIN da ULA |

A saída C volta para a ULA: é o vai-um de entrada do `ADC` e do `SBC`.

## Quem muda cada flag

| Instruções                                                    | Z      | C      | Sinais               |
|---------------------------------------------------------------|--------|--------|----------------------|
| ARIT/ARITI: `ADD SUB ADC SBC CMP SHR` (e `...I`)              | grava  | grava  | `Z_WE = C_WE = ARIT` |
| LOG/LOGI: `AND OR XOR TST NOT LOG` (e `...I`)                 | grava  | mantém | `Z_WE = LOGICA`      |
| `LDI LD ST LDR IN`, saltos, MEM (`VOUT VIN VPOS STP LDP PTR`) | mantém | mantém | —                    |

```
Z_WE = ARIT + LOGICA
C_WE = ARIT
```

O programa depende de quem **mantém**. Exemplos reais:

```
    LDR          ; A = celula (0 ou 255)
    CMPI 0       ; Z calculado aqui
    JNZ  AN_F0   ; usa o Z do CMPI                     (doom.py)

    SHR          ; C = bit da celula
    ST   MBYTE
    LDI  0       ; LDI e ST nao mudam C
    JNC  DESC_GRAVA                                    (doom.py)
```

## Circuito (de cada flag)

1 flip-flop D + 1 mux 2×1 de 1 bit na entrada (realimentação):

```
D_IN ──► D1 ┐
            MUX (SEL = WE) ──► D [FF] Q ──┬──► Q
Q ─────► D0 ┘               ↑CLK         │
  ▲                                      │
  └──────────────────────────────────────┘
```

Quando WE = 0 o flip-flop regrava o próprio valor. Não faça "AND do relógio
com WE" (gera pulsos falsos).

| Peça                          | Por flag             | Total (Z e C) |
|-------------------------------|----------------------|---------------|
| flip-flop D                   | 1                    | 2             |
| mux 2×1 de 1 bit (arquivo 05) | 1 NOT + 2 AND + 1 OR | 8 portas      |

Estado ao ligar: qualquer. O programa sempre calcula a flag antes de saltar.

## Testes (vale para Z e para C)

| Passo | D_IN | WE  | Ação | Q             |
|-------|------|-----|------|---------------|
| 1     | 1    | 1   | ↑CLK | 1             |
| 2     | 0    | 0   | ↑CLK | 1 (não mudou) |
| 3     | 0    | 1   | ↑CLK | 0             |
| 4     | 1    | 0   | ↑CLK | 0 (não mudou) |
| 5     | 1    | 1   | ↑CLK | 1             |

Teste com o decodificador ligado: depois de `ANDI` o C não pode mudar; depois
de `LDI` nenhuma das duas pode mudar.

## Tempo

**Gravar: 1 × CLOCK** (borda de subida). A flag nova vale para a instrução
seguinte.

## Correspondência com o simulador

Em `passo()` (`hardware.py`): `if s.Z_WE: self.z = z` e `if s.C_WE: self.c = c`, com `z` e `c` vindos de
`ULA.calcula()`.
