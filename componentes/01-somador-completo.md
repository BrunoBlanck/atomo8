# 01 · Somador completo (1 bit)

O bloco mais básico da ULA. Soma **três bits** (A, B e o vai-um que chega do
bit anterior) e devolve **um bit de soma** e **um vai-um** para o próximo bit.

## Pinos

| Pino   | Direção | Descrição                        |
|--------|---------|----------------------------------|
| `A`    | entrada | bit do primeiro número           |
| `B`    | entrada | bit do segundo número            |
| `CIN`  | entrada | vai-um que chega do bit anterior |
| `S`    | saída   | bit da soma                      |
| `COUT` | saída   | vai-um para o próximo bit        |

## Equações

```
S    = A XOR B XOR CIN
COUT = (A AND B) OR (CIN AND (A XOR B))
```

## Circuito (5 portas)

```
A ──┬──────────┐
    │        ┌─┴──┐  X1            ┌────┐
    │        │XOR ├──────┬─────────┤XOR ├──── S
B ──┼──┬─────┤    │      │    CIN ─┤    │
    │  │     └────┘      │         └────┘
    │  │                 │   ┌────┐
    │  │          CIN ───┼───┤AND ├── P2 ─┐
    │  │                 └───┤    │       │  ┌────┐
    │  │                     └────┘       └──┤ OR ├──── COUT
    │  │    ┌────┐                        ┌──┤    │
    └──┼────┤AND ├───────── P1 ───────────┘  └────┘
       └────┤    │
            └────┘
```

Portas: 2 × XOR, 2 × AND, 1 × OR = 5 portas.

## Tabela verdade (teste completo: 8 combinações)

| A   | B   | CIN | S   | COUT |
|-----|-----|-----|-----|------|
| 0   | 0   | 0   | 0   | 0    |
| 0   | 0   | 1   | 1   | 0    |
| 0   | 1   | 0   | 1   | 0    |
| 0   | 1   | 1   | 0   | 1    |
| 1   | 0   | 0   | 1   | 0    |
| 1   | 0   | 1   | 0   | 1    |
| 1   | 1   | 0   | 0   | 1    |
| 1   | 1   | 1   | 1   | 1    |

## Como testar sozinho

1. 3 chaves com resistor de pull-down (10 kΩ) nas entradas A, B, CIN.
2. 2 LEDs (com resistor de ~330 Ω) em S e COUT.
3. Percorra as 8 linhas da tabela. Todas precisam bater.

Dica: monte **8 unidades iguais** e teste cada uma. O arquivo 02 usa 8 delas.

## Tempo

**0 × CLOCK**: é combinacional, a saída muda assim que as entradas mudam.

O caminho mais lento é `A/B → XOR → AND → OR → COUT` (3 portas em fila).
Esse atraso das portas é o que, somado aos outros blocos, define o menor
CLOCK possível (arquivo 20).
