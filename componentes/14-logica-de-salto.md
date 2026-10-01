# 14 · Lógica de salto

Combina o tipo de salto (vindo do decodificador) com as flags Z e C e responde
uma única pergunta: **o salto acontece?** (`TOMA`).

## Pinos

| Pino    | Direção | Descrição                               |
|---------|---------|-----------------------------------------|
| `SALTO` | entrada | instrução JMP (sempre salta)            |
| `SE_Z`  | entrada | instrução JZ                            |
| `SE_NZ` | entrada | instrução JNZ                           |
| `SE_C`  | entrada | instrução JC                            |
| `SE_NC` | entrada | instrução JNC                           |
| `Z`     | entrada | flag Z guardada (arquivo 09)            |
| `C`     | entrada | flag C guardada (arquivo 09)            |
| `TOMA`  | saída   | 1 = próximo PC é o destino (arquivo 13) |

## Equação

```
TOMA = SALTO + SE_Z·Z + SE_NZ·/Z + SE_C·C + SE_NC·/C
```

## Esquema em portas

```
SALTO ─────────────────────────────────────┐
                                           OR ──┐
SE_Z  ──┐                                  │    │
        AND ───────────────────────────────┘    OR ──┐
Z  ──┬──┘                                       │    │
     │                                          │    │
     └─ NOT ─┐                                  │    │
SE_NZ ───────AND ───────────────────────────────┘    OR ──┐
                                                     │    │
SE_C  ──┐                                            │    │
        AND ─────────────────────────────────────────┘    OR ── TOMA
C  ──┬──┘                                                 │
     │                                                    │
     └─ NOT ─┐                                            │
SE_NC ───────AND ─────────────────────────────────────────┘
```

| Peça      | Quantas                 |
|-----------|-------------------------|
| NOT       | 2                       |
| AND de 2  | 4                       |
| OR de 2   | 4                       |
| **Total** | **10 portas** (antes 5) |

## Tabela de testes

(no máximo uma das 5 entradas de tipo fica em 1 por vez; o decodificador garante)

| Tipo ligado | Z | C | TOMA |
|-------------|---|---|------|
| nenhum      | x | x | 0    |
| SALTO       | x | x | 1    |
| SE_Z        | 0 | x | 0    |
| SE_Z        | 1 | x | 1    |
| SE_NZ       | 0 | x | 1    |
| SE_NZ       | 1 | x | 0    |
| SE_C        | x | 0 | 0    |
| SE_C        | x | 1 | 1    |
| SE_NC       | x | 0 | 1    |
| SE_NC       | x | 1 | 0    |

`x` = tanto faz: no teste, passe pelos dois valores e confira que `TOMA` não muda.
(JZ/JNZ não olham C; JC/JNC não olham Z.)

## Tempo

**0 × CLOCK** (combinacional, no máximo 5 portas em fila: NOT → AND → 3 OR).
Fica fora do caminho crítico: Z e C já estão guardadas desde o ↑CLK anterior.
