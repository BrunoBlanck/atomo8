# 20 · Relógio e reset

Gera o "coração" do hardware e controla quando tudo grava. É aqui que nasce
a constante **CLOCK** usada em todos os arquivos.

```
CLOCK = período de 1 pulso completo do relógio (valor a medir)
```

O programa nunca para: não há instrução de parada, então também não há
circuito para travar o relógio.

## Saídas

| Sinal       | Descrição                                            |
|-------------|------------------------------------------------------|
| `CLK`       | relógio para A, Z, C, PC, ponteiro, cursor e teclado |
| `CLK_BAIXO` | `NOT CLK`; libera os pulsos de escrita (RAM e VRAM)  |
| `/RST`      | 0 = zera o PC e o cursor da VRAM (arquivo 21)        |

## Entradas

| Entrada     | Descrição                                |
|-------------|------------------------------------------|
| oscilador   | 555 (lento, ajustável) ou cristal (fixo) |
| chave MODO  | automático / passo a passo               |
| botão PASSO | 1 × CLOCK por aperto (com debounce)      |
| botão RESET | reinicia o jogo                          |

## Um ciclo de instrução = 1 × CLOCK

```
        |<------------------ 1 × CLOCK ------------------>|
        |<------ ½ × CLOCK ----->|<------ ½ × CLOCK ----->|
        ┌────────────────────────┐                        ┌──
CLK     │          alto          │         baixo          │
   ─────┘                        └────────────────────────┘
        ▲                                                 ▲
     ↑CLK: PC, A, Z, C,                              próxima ↑CLK
     ponteiro e cursor
     gravam; nova
     instrução começa
        |<- ROM, decodificador, ->|<- /WE da RAM e escrita ->|
            RAM, ULA estabilizam       na VRAM pulsam
```

- **Metade alta (½ × CLOCK)**: tudo o que é combinacional estabiliza.
- **Metade baixa (½ × CLOCK)**: os pulsos de escrita (`RAM_WE AND CLK_BAIXO`,
  `VID_WR AND CLK_BAIXO`) acontecem com endereço e dado já parados.
- **Borda de subida**: os registradores gravam juntos.

## Quanto tempo cada coisa leva

| O quê                                                | Tempo                               |
|------------------------------------------------------|-------------------------------------|
| qualquer instrução                                   | 1 × CLOCK                           |
| consultar 1 célula do labirinto (`LD`, `ADD`, `LDR`) | 3 × CLOCK                           |
| 1 coluna do 3D (`LDI` + `VOUT`, 4 bytes)             | ~5 a 8 × CLOCK                      |
| girar (esquerda ou direita)                          | 7 × CLOCK                           |
| quadro 3D completo                                   | 262 a 385 × CLOCK (média ~318)      |
| quadro do mapa                                       | ~1 496 × CLOCK                      |
| ligar (desenrolar o labirinto compactado na RAM)     | ~2 130 × CLOCK, uma vez             |
| bola: 1 passo (apaga, move, acende)                  | ~75 × CLOCK + espera de 512 × CLOCK |
| tetris: 1 volta do laço (sem tecla)                  | ~93 × CLOCK                         |
| tetris: mover, girar ou descer 1                     | ~610 a 625 × CLOCK                  |
| tetris: peça para e some 1 a 4 linhas                | ~1 250 a 2 190 × CLOCK              |

Ligar ficou mais lento (antes ~180 × CLOCK) porque o labirinto vem
compactado, 1 bit por célula, e um laço `LDR` / `SHR` / `JNC` / `STP` o
desenrola. Em troca a ROM usa 69 palavras em vez de 171. Acontece uma vez só.

## Quadros por segundo

```
quadros por segundo ≈ 1 / (320 × CLOCK)       (3D, caso médio)
```

Exemplos, só para ter noção (o valor real de CLOCK virá da medição):

| CLOCK                     | Tempo de 1 quadro 3D | Quadros por segundo |
|---------------------------|----------------------|---------------------|
| 1 s (passo a passo lento) | ~5 min               | —                   |
| 10 ms                     | ~3,2 s               | ~0,3                |
| 1 ms                      | ~0,32 s              | ~3                  |
| 100 µs                    | ~32 ms               | ~31                 |
| 10 µs                     | ~3,2 ms              | ~300                |

Um hardware lento continua funcionando igual, só mais devagar. Nada no
programa depende do valor de CLOCK.

O simulador ainda permite somar CLOCKs extras por leitura, gravação e quadro
(`CLOCKS_EXTRA_*` em `hardware.py`) para imitar peças lentas. Na posição
inicial, um giro completo do laço (quadro 3D + leitura do teclado) leva
~400 × CLOCK; com os valores atuais (10 / 10 / 100) vira ~2 470 × CLOCK.

## Como descobrir o CLOCK (quando tudo estiver pronto)

O menor CLOCK possível é aquele em que a fila combinacional mais longa ainda
cabe na metade alta:

```
½ × CLOCK ≥ ROM → decodificador → mux de endereço da RAM (4×1) → RAM
            → mux B → XOR (SUB) → somador (vai-um em cadeia)
            → mux de resultado (4×1) → mux de A → entrada de A
```

Caminhos em paralelo, mais curtos (não mandam no CLOCK):

| Caminho                                         | Por que é mais curto                         |
|-------------------------------------------------|----------------------------------------------|
| unidade lógica (arquivo 04)                     | 4 níveis de porta, sem cadeia                |
| vai-um de entrada `CIN` (USA_C, SUB, C)         | 3 níveis de porta, junto com os 8 XOR do SUB |
| cursor → VRAM → mux de memória (05) → mux de A  | não passa pela ULA                           |
| Z, C → lógica de salto (14) → mux do próximo PC | flags já guardadas desde o ↑CLK anterior     |

Procedimento prático:
1. Comece no modo passo a passo e rode os testes do arquivo 22.
2. Passe para o oscilador ajustável (555) bem lento e rode os mesmos testes.
3. Vá diminuindo o CLOCK (aumentando a frequência) e rodando o teste da
   Etapa 3 do arquivo 22 (`ADDI 1` até passar de 255). É o pior caso do somador.
4. Quando começar a errar, anote esse valor: `CLOCK_LIMITE`.
5. Use **CLOCK = 2 × CLOCK_LIMITE** (margem para temperatura, fios e ruído).
6. Coloque o valor em `CLOCK_US` no `hardware.py` para o simulador rodar na
   mesma velocidade do seu hardware.

## Reset

- Botão RESET → `/RST = 0` → PC = 0 e cursor da VRAM = 0 imediatamente
  (0 × CLOCK, clear assíncrono nos flip-flops; arquivos 12 e 21).
- Ao ligar a fonte, um RC (10 kΩ + 10 µF) no `/RST` mantém o reset por um
  instante. Esse tempo **não depende do CLOCK**: vem só do resistor e do
  capacitor e só precisa ser bem maior que alguns CLOCKs.
- Não precisa zerar A, Z, C, o ponteiro da RAM nem a RAM: o programa
  inicializa tudo (o ponteiro é carregado com `PTR` antes de usar).

## Modo passo a passo

Mux 2×1 de 1 bit: `CLK = MODO ? OSC : BOTÃO_PASSO_SEM_REPIQUE`.
Cada aperto = 1 × CLOCK = 1 instrução. Com LEDs no PC, em A, Z e C, dá para
seguir o programa instrução por instrução e comparar com o simulador.

## Testes

1. LED ou osciloscópio no CLK: confira que o oscilador pulsa.
2. Modo passo: cada aperto = exatamente 1 pulso (se contar 2, o debounce está
   ruim). Com a ROM toda em `F000` (não faz nada), os LEDs do PC servem de
   contador de pulsos: cada aperto soma 1.
3. RESET: PC e cursor voltam a 0 na hora, sem precisar de pulso.
