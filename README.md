# Átomo8

Computador de 8 bits projetado do zero, **porta lógica por porta lógica**, sem nenhum chip pronto.
Roda um labirinto 3D, Tetris e uma bola quicando num display 32×32 de 1 bit.

O Python aqui é só a referência: o destino é hardware real.

---

## A ideia

- **Tudo em portas lógicas:** AND, OR, NOT, XOR, NAND, NOR e flip-flops montados com elas.
- **Nenhum chip pronto:** sem 74HCxxx, ULA integrada, contadores ou muxes comprados.
- **Hardware mínimo:** só entra a peça que os programas realmente usam.
- **Custos em portas**, tempos em múltiplos de `CLOCK`.

## Especificação

| Peça       | Especificação                     |
|------------|-----------------------------------|
| CPU        | 8 bits, acumulador A, flags Z e C |
| Instruções | 16 opcodes, 1 instrução por CLOCK |
| ROM        | 2048 × 16                         |
| RAM        | 256 × 8                           |
| VRAM       | 128 × 8 (display 32×32, 1 bit)    |
| Teclado    | 5 botões com trava de evento      |
| PC         | 11 bits                           |

### Formato da instrução

```
 15..12   11..8   7..0
 [ OP ]  [  F  ] [ N ]
```

| Campo | Uso                                                    |
|-------|--------------------------------------------------------|
| `OP`  | código da instrução                                    |
| `F`   | função (ARIT), tabela-verdade (LOG) ou subfunção (MEM) |
| `N`   | número imediato ou endereço da RAM                     |

### Opcodes

| Grupo      | Instruções                                     |
|------------|------------------------------------------------|
| Carga      | `LDI`, `LD`, `ST`, `LDR`                       |
| Aritmética | `ARIT`, `ARITI` (ADD, SUB, ADC, SBC, SHR, CMP) |
| Lógica     | `LOG`, `LOGI` (AND, OR, XOR, TST, NOT…)        |
| Saltos     | `JMP`, `JZ`, `JNZ`, `JC`, `JNC`                |
| Entrada    | `IN`                                           |
| Memória    | `MEM` (VOUT, VIN, VPOS, STP, LDP, PTR)         |

## Programas

| Programa      | Arquivo     | Tamanho na ROM       |
|---------------|-------------|----------------------|
| Labirinto 3D  | `doom.py`   | 1596 / 2048 palavras |
| Tetris 10×16  | `tetris.py` | 960 palavras         |
| Bola quicando | `bola.py`   | 76 palavras          |

Os programas são escritos só em assembly do Átomo8.

## Rodar

Requer Python 3 (o esquema usa `tkinter`, que já vem com o Python).

```
python doom.py              # labirinto 3D
python tetris.py            # tetris (A/D move, W gira, S desce, M solta)
python bola.py              # bola quicando
python esquema/esquema.py   # esquema interativo do hardware
```

Teclas: `W` `A` `S` `D` (ou setas) e `M`.

## Estrutura

| Caminho                           | Conteúdo                                                       |
|-----------------------------------|----------------------------------------------------------------|
| `hardware.py`                     | simulador: ULA porta a porta, CPU, display, teclado e montador |
| `doom.py`, `tetris.py`, `bola.py` | programas da ROM                                               |
| `gerar_mapa.py`                   | gera o labirinto compactado em assembly                        |
| `componentes/`                    | um documento por peça, na ordem de construção (00 a 22)        |
| `esquema/`                        | esquema gráfico com simulação Livre/Debug e visão em portas    |
| `Resumo-Melhorias.md`             | histórico das decisões de projeto                              |

## Construção

Cada arquivo em [`componentes/`](componentes/00-LEIA-ME.md) traz pinos, equações, esquema em portas,
tabela-verdade, teste isolado e tempo em CLOCK. Dá para montar cada peça sozinha na protoboard,
testar com chaves e LEDs, e só então integrar.

| Etapa       | Peças                                                      |
|-------------|------------------------------------------------------------|
| ULA         | somador, inversor, unidade lógica, muxes, detector de zero |
| Estado      | registrador A, flags, PC, ponteiro/cursor                  |
| Controle    | incrementador, lógica de salto, decodificador              |
| Memórias    | ROM, RAM, VRAM                                             |
| Periféricos | display, teclado, relógio e reset                          |
| Integração  | ligar tudo e testar o sistema (`22-integracao.md`)         |

## Situação

- Simulador, programas e documentação funcionando e em sincronia.
- **Pendente:** memórias (ROM, RAM, VRAM) e peças analógicas (oscilador, debounce) ainda citam chips
  nos documentos 15, 16, 18, 19 e 20.
