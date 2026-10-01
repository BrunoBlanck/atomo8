# TesteDoom: hardware do labirinto 3D

Protótipo de um **hardware dedicado** (não é um computador de uso geral), que será construído do zero para rodar o labirinto 3D num display 32×32 de 1 bit. O Python é só a referência: o destino é hardware real.

Tudo em **português**: código, comentários, documentos e respostas.

---

## Regra nº 1: tudo em portas lógicas

- **Todo** componente é projetado, explicado e contado em **portas lógicas**: AND, OR, NOT, XOR, NAND, NOR e flip-flops/latches montados com essas portas.
- **Nunca** usar componente pronto como base: 74HCxxx, 74181, EEPROM, SRAM, contadores ou muxes integrados.
- Custos são dados em **portas** (e flip-flops), nunca em chips.
- Cada peça nova segue o padrão de `componentes/`: pinos, equações, esquema em portas (ASCII), tabela-verdade, teste isolado e tempo em CLOCK.
- Reaproveite os blocos já explicados (somador 01, mux 05/10, incrementador 11…) em vez de inventar outros.
- **Legado:** linhas "Em CI: 74HC…" e seções "Implementação prática" em `componentes/` são anteriores a esta regra. Não use como base. Ao editar um desses arquivos, troque por contagem de portas.

## Regra nº 2: tudo sempre em sincronia

Quando o hardware muda, todos mudam juntos:

| O quê | Onde |
|---|---|
| Simulador | `hardware.py` (ULA simulada porta a porta) |
| Programas da ROM | `doom.py`, `bola.py`, `tetris.py` (só assembly, sem lógica Python) |
| Documentação | `componentes/00..22-*.md` |
| Esquema gráfico | `esquema/dados.py` (blocos, fios, custos, caminhos das instruções) |

## Outras regras

- **Hardware mínimo:** antes de acrescentar uma peça, ver se o programa resolve com o que já existe. O que ficar sem uso sai.
- **Tempos sempre em múltiplos de CLOCK** (ex.: `3 × CLOCK`, `½ × CLOCK`), nunca em ns. O valor de CLOCK ainda não é conhecido.
- **Otimize por acessos à RAM:** o simulador cobra CLOCKs extras por leitura e gravação (`CLOCKS_EXTRA_*`).
- **Tabelas dos `.md`** com as colunas alinhadas por espaços.
- **Textos leves:** tabelas e listas curtas, sem texto desnecessário.

---

## Mapa dos arquivos

| Arquivo | Conteúdo |
|---|---|
| `hardware.py` | simulador: ULA, display, teclado, CPU, montador |
| `doom.py` | labirinto 3D (programa da ROM, 1596 / 2048 palavras) |
| `bola.py` | bola quicando usando a VRAM como memória (76 palavras) |
| `tetris.py` | Tetris 10 × 16 com prévia e placar (960 palavras) |
| `gerar_mapa.py` | gera o bloco do labirinto compactado em assembly (script avulso) |
| `componentes/` | um `.md` por peça, na ordem de construção (00 = índice, 22 = integração) |
| `esquema/` | esquema gráfico interativo (`python esquema/esquema.py`) com simulação Livre/Debug do DOOM, da Bola e do Tetris. `dados.py` = blocos e fios; `simulacao.py` = liga o esquema ao `hardware.py` (sem lógica própria); `portas.py` = cada componente em portas lógicas (netlist testável); `visor_portas.py` = janela "Visualizar em portas lógicas" |
| `Resumo-Melhorias.md` | histórico das melhorias decididas (ULA, RAM, ROM, VRAM), **já implementadas** |

## Arquitetura atual (resumo)

- **Registradores:** A (8 bits, acumulador), PC (11), flags Z e C, ponteiro da RAM (8) e cursor da VRAM (7). Ponteiro e cursor são o mesmo componente (arquivo 21).
- **Memórias:** ROM 2048 × 16, RAM 256 × 8 (liga com lixo), VRAM 128 × 8 (a CPU lê e grava).
- **Instrução:** `[OP 4][F 4][N 8]`; saltos usam 11 bits de destino. F = função (ARIT), tabela-verdade (LOG) ou subfunção (MEM).
- **16 opcodes:** LDI, LD, ST, LDR, ARIT, ARITI, LOG, LOGI, JMP, JZ, JNZ, JC, JNC, IN, MEM, livre.
  - ARIT: ADD, SUB, ADC, SBC, SHR, CMP (bits de F ligados direto na ULA).
  - LOG: AND, OR, XOR, TST, NOT… (F = tabela-verdade, mux 4×1 por bit).
  - MEM: VOUT, VIN, VPOS (VRAM) e STP, LDP, PTR (RAM pelo ponteiro).
- **Ciclo único:** toda instrução gasta 1 × CLOCK.
- **Display:** VRAM de 128 bytes (bytes em pé, 4 páginas × 32 colunas). O doom escreve 128 `VOUT` por quadro; a bola só muda o byte da bola.
- **Teclado:** 5 botões com trava de evento. `IN` devolve 0 sem evento (não espera).
- **Decisão pendente:** memórias (ROM, RAM, VRAM) e peças analógicas (oscilador, debounce) ainda citam chips nos arquivos 15, 16, 18, 19 e 20.

## Rodar

```
python doom.py     # labirinto
python bola.py     # bola quicando
python tetris.py   # tetris (A/D move, W gira, S desce, M solta)
python esquema/esquema.py   # esquema interativo do hardware
```

## Para ir mais fundo

- Skill **`projeto-hardware`**: contexto completo e checklist de mudança.
- Agente **`engenheiro-hardware`**: analisa ou altera o projeto respeitando as regras acima.
