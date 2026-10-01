# 21 · Registrador-ponteiro (k bits, carrega ou avança)

Um registrador que guarda um endereço e **soma 1 sozinho** depois de usado.
O mesmo circuito é construído **2 vezes**:

| Instância       | Bits | Para quê                                        |
|-----------------|------|-------------------------------------------------|
| Ponteiro da RAM | 8    | `STP` / `LDP`: gravar ou ler bytes em sequência |
| Cursor da VRAM  | 7    | `VOUT` / `VIN`: endereço da tela (lado da CPU)  |

## Pinos

| Pino         | Direção | Largura | Descrição                          |
|--------------|---------|---------|------------------------------------|
| `D_A[k-1:0]` | entrada | k       | registrador A (bits de baixo)      |
| `CARREGA`    | entrada | 1       | 1 = Q recebe A na próxima ↑CLK     |
| `AVANCA`     | entrada | 1       | 1 = Q recebe Q + 1 na próxima ↑CLK |
| `CLK`        | entrada | 1       | relógio                            |
| `/RST`       | entrada | 1       | só no cursor: 0 = zera na hora     |
| `Q[k-1:0]`   | saída   | k       | endereço atual (sempre disponível) |

## Equações

```
INC  = Q + 1                  incrementador do arquivo 11 com k bits
NOVO = CARREGA ? D_A : INC    mux 2×1 (arquivo 05)
WE   = CARREGA OR AVANCA      1 OR
D    = WE ? NOVO : Q          mux 2×1 = "enable", como o registrador A (08)
grava D na ↑CLK
```

| CARREGA | AVANCA | Q depois da ↑CLK         |
|---------|--------|--------------------------|
| 0       | 0      | Q (segura)               |
| 0       | 1      | Q + 1 (volta a 0 no fim) |
| 1       | 0      | A                        |
| 1       | 1      | A (nunca acontece)       |

## Circuito de 1 bit (repita k vezes)

```
                 incrementador (arquivo 11)
 Qn ──┬─────────►[XOR]──► INCn          Cn+1 = Qn AND Cn
      │  Cn ────►[   ]
      │
      │          mux de carga                mux de enable
      │        ┌──────────────┐            ┌──────────────┐
D_An ─┼──► D1  │  MUX 2x1     │            │  MUX 2x1     │      ┌──────────┐
INCn ─┼──► D0  │ SEL=CARREGA  ├── NOVOn ──►│ D1           ├─ d ─►│ D   FF   │── Qn ─┐
      │        └──────────────┘            │ SEL=WE       │      │    ↑CLK  │       │
      └───────────────────────────────────►│ D0           │      │   /CLR   │       │
                                           └──────────────┘      └──────────┘       │
      ▲                                                                             │
      └──────────────────────────── realimentação ──────────────────────────────────┘

WE = CARREGA OR AVANCA         (1 OR, um só para os k bits)
```

- Cada mux de 1 bit: `Y = (D0 AND NOT SEL) OR (D1 AND SEL)`; o NOT de cada
  seletor é um só para os k bits.
- `/CLR` só existe no cursor (ligado em `/RST`). No ponteiro da RAM fica em 1.
- **Não** faça "AND do relógio com WE" (gera pulsos falsos).

## Contagem

| Parte              | k = 8 (ponteiro)      | k = 7 (cursor)        |
|--------------------|-----------------------|-----------------------|
| incrementador (11) | 7 XOR + 7 AND + 1 NOT | 6 XOR + 6 AND + 1 NOT |
| mux de carga (05)  | 1 NOT + 16 AND + 8 OR | 1 NOT + 14 AND + 7 OR |
| mux de enable (05) | 1 NOT + 16 AND + 8 OR | 1 NOT + 14 AND + 7 OR |
| WE                 | 1 OR                  | 1 OR                  |
| **portas**         | **66**                | **58**                |
| **flip-flops D**   | **8**                 | **7** (com clear)     |

As duas juntas: **124 portas + 15 flip-flops**. O cursor substitui o antigo
contador de 7 bits do display (arquivo 18), que já tinha incrementador e
flip-flops: o que ele acrescenta de fato são os 2 muxes.

## As duas instâncias

|                | Ponteiro da RAM                   | Cursor da VRAM                       |
|----------------|-----------------------------------|--------------------------------------|
| bits           | 8                                 | 7                                    |
| `CARREGA`      | `PTR_LD` (`PTR`)                  | `CUR_LD` (`VPOS`)                    |
| `AVANCA`       | `PTR_INC` (`STP`, `LDP`)          | `CUR_INC` (`VOUT`)                   |
| reset          | não (o programa carrega com PTR)  | `/RST` zera (clear assíncrono)       |
| saída vai para | mux de endereço da RAM (entr. 10) | endereço da VRAM, lado da CPU (18)   |
| quem usa       | doom: desenrolar o labirinto      | doom: 128 `VOUT`; bola: `VPOS`/`VIN` |

`VIN` lê no endereço do cursor e **não** avança (`CUR_INC` só vem do `VOUT`).

## Por que 2 e não 1

Com um ponteiro só, copiar da RAM para a tela teria que trocar o endereço a
cada byte. Com dois, cada um anda sozinho:

| Copiar 1 byte RAM → tela | Instruções                                                    |
|--------------------------|---------------------------------------------------------------|
| com 2 ponteiros          | `LDP` / `VOUT` = **2**                                        |
| só com o cursor          | `LD P` / `LDR` / `VOUT` / `LD P` / `ADDI 1` / `ST P` = **~6** |

E o doom usa o ponteiro (`STP`) ao ligar sem mexer no cursor da tela.
`LDP` não custa nada a mais: usa os mesmos sinais de `STP` (`PTR_INC`).

## Testes

Cursor (k = 7), chaves em D_A, CARREGA, AVANCA; LEDs em Q:

| Passo | D_A     | CARREGA | AVANCA | /RST | Ação      | Q esperado                 |
|-------|---------|---------|--------|------|-----------|----------------------------|
| 1     | —       | 0       | 0      | 0    | —         | 0000000 (reset na hora)    |
| 2     | 0000101 | 1       | 0      | 1    | ↑CLK      | 0000101 (carrega)          |
| 3     | —       | 0       | 1      | 1    | ↑CLK      | 0000110 (avança)           |
| 4     | 1111111 | 0       | 0      | 1    | ↑CLK      | 0000110 (segura)           |
| 5     | 1111111 | 1       | 0      | 1    | ↑CLK      | 1111111 (127)              |
| 6     | —       | 0       | 1      | 1    | ↑CLK      | 0000000 (volta a 0)        |
| 7     | 0101010 | 1       | 0      | 1    | sem pulso | 0000000 (só muda na borda) |

Ponteiro (k = 8): carregue `11111111`, avance → `00000000`; carregue
`10101010`, avance 2 vezes → `10101100`.

## Como testar sozinho

- Chaves em D_A, CARREGA e AVANCA; botão com debounce como CLK (arquivo 20).
- LEDs em Q e também em INC (mostra Q + 1 antes da borda).
- Teste "sem pulso": mude as chaves e veja que Q só muda na ↑CLK.

## Tempo

- **Calcular: 0 × CLOCK** (incrementador e muxes são combinacionais; o pior
  caso é o vai-um atravessando k − 1 AND, igual ao arquivo 11).
- **Gravar: na ↑CLK**, 1 × CLOCK por instrução como tudo.
- No `VOUT` e no `STP` o byte é gravado na metade baixa no endereço **atual**;
  o ponteiro/cursor só muda na ↑CLK seguinte, depois do pulso de escrita.
- Q vai direto para o endereço da memória: não entra no caminho crítico
  (fica pronto no início do ciclo).

## Correspondência com o simulador

| Hardware             | `hardware.py`                                              |
|----------------------|------------------------------------------------------------|
| ponteiro da RAM (Q)  | `Computador.ponteiro` (liga com lixo)                      |
| cursor da VRAM (Q)   | `Computador.cursor` (0 no reset)                           |
| incrementador k bits | `incrementa(v, largura)`                                   |
| sinais               | `PTR_LD`, `PTR_INC`, `CUR_LD`, `CUR_INC` em `decodifica()` |
| ↑CLK                 | fim de `passo()`: `if s.PTR_LD ... elif s.PTR_INC ...`     |
