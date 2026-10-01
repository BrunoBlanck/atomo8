# 19 · Teclado (5 botões → 1 byte)

É o dispositivo de entrada **único**: a instrução `IN` coloca este byte em A.
Cada bit é um botão:

| Bit | Botão | Ação no jogo              |
|-----|-------|---------------------------|
| 0   | W / ↑ | anda para frente          |
| 1   | S / ↓ | anda para trás            |
| 2   | A / ← | gira à esquerda           |
| 3   | D / → | gira à direita            |
| 4   | M     | liga/desliga mapa         |
| 5–7 | —     | sempre 0 (ligados em GND) |

## Pinos

| Pino         | Direção | Descrição                                                 |
|--------------|---------|-----------------------------------------------------------|
| 5 botões     | entrada | contato físico                                            |
| `TEC_RD`     | entrada | instrução IN (arquivo 17)                                 |
| `CLK`        | entrada | relógio                                                   |
| `SAIDA[7:0]` | saída   | vai **direto** para a entrada 11 do mux de A (arquivo 10) |

Como só existe um dispositivo de entrada, não há barramento compartilhado nem
buffer tri-state: a saída fica sempre ligada no mux, e o mux só a escolhe
durante `IN`.

## Por que precisa de "trava de evento"

O programa lê o teclado **uma vez por quadro** e age em cima do que leu. Se o
bloco entregasse só "botão apertado agora":
- segurar o M ligaria e desligaria o mapa a cada quadro (pisca);
- um toque rápido entre duas leituras seria perdido.

Então cada botão tem um **flip-flop de evento**:
- vai para 1 quando o botão é **apertado** (borda de subida);
- volta para 0 quando a CPU **lê** (`TEC_RD`).

O simulador faz o mesmo: cada tecla apertada é entregue uma única vez.

## Circuito de 1 bit (repita 5 vezes)

```
botão ─► [DEBOUNCE] ─► b ──► [SINCRONIZA: FF D no CLK] ─► b1 ─► [FF D] ─► b2
                                                          │
                                         aperto = b1 AND NOT b2   (borda)
                                                          │
                                    ┌─────────────────────┘
                                    ▼
      EVENTO(n+1) = aperto OR (EVENTO(n) AND NOT TEC_RD)      (FF D no CLK)
                                    │
                                    ▼
                               SAIDA bit n
```

- **Debounce**: resistor + capacitor (10 kΩ / 100 nF) seguido de porta Schmitt
  (74HC14), ou um latch SR com botão de duas posições.
- **Sincronizar** no relógio evita que o bit mude no meio de uma instrução.

Portas (5 bits): 15 flip-flops D + 6 NOT + 10 AND + 5 OR
(por bit: 3 flip-flops, 1 NOT + 2 AND + 1 OR; o NOT de `TEC_RD` é um só).
Fora isso, só o debounce de cada botão.

## IN não espera

Sem evento, `IN` devolve **0** na hora. O simulador agora faz igual (antes
ele esperava uma tecla). Para esperar, o programa faz um laço:

```
ESPERA:
    IN           ; A = eventos (0 = nenhum)
    TST          ; Z = (A == 0)
    JZ   ESPERA
```

O doom usa este laço na tela de vitória (`V_ESPERA`). Cada volta: 3 × CLOCK.

## Tempo

| Etapa                               | Tempo                                                  |
|-------------------------------------|--------------------------------------------------------|
| debounce do botão                   | **não depende do CLOCK** (vem do resistor + capacitor) |
| botão estável → `b1`                | 1 × CLOCK                                              |
| `b1` → EVENTO = 1                   | 1 × CLOCK                                              |
| **aperto → evento pronto para ler** | **2 × CLOCK**                                          |
| `IN` (ler e apagar o evento)        | 1 × CLOCK                                              |

Um aperto precisa durar pelo menos **2 × CLOCK** depois do debounce para ser
visto. Com o hardware bem lento (passo a passo), segure o botão durante 2 pulsos.

## Testes

LEDs na SAIDA, botão manual como relógio e uma chave como `TEC_RD`:

| Passo | Ação                                | SAIDA                          |
|-------|-------------------------------------|--------------------------------|
| 1     | nada apertado, alguns pulsos de CLK | 00000000                       |
| 2     | aperta e solta W, 2 pulsos de CLK   | 00000001                       |
| 3     | TEC_RD = 1, 1 pulso de CLK          | 00000000 (evento consumido)    |
| 4     | segura M, TEC_RD = 1, vários pulsos | 00010000 por 1 pulso, depois 0 |
| 5     | TEC_RD = 0, aperta A e D, 2 pulsos  | 00001100                       |
