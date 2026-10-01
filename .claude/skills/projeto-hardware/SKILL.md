---
name: projeto-hardware
description: Contexto completo do hardware do labirinto 3D (TesteDoom) - arquitetura, conjunto de instruções, regra de "tudo em portas lógicas", modelo de documento de componente e checklist para mudar hardware, simulador, programas e docs juntos. Use antes de analisar, propor ou implementar qualquer mudança no hardware, na ULA, nas memórias, no display, no simulador (hardware.py), nos programas da ROM (doom.py, bola.py) ou em componentes/*.md.
---

# Projeto hardware do labirinto 3D

## 1. Leia primeiro

| Ordem | Arquivo | Para quê |
|---|---|---|
| 1 | `CLAUDE.md` | regras do projeto |
| 2 | `componentes/00-LEIA-ME.md` | índice, diagrama geral, sinais de controle, CLOCK |
| 3 | `hardware.py` (docstring + `passo()`) | comportamento exato de cada instrução |
| 4 | `Resumo-Melhorias.md` | histórico das decisões (por que cada peça existe) |
| 5 | o arquivo de `componentes/` da peça em questão | detalhes |

## 2. Regras que não podem quebrar

1. **Tudo em portas lógicas.** Nada de 74HCxxx, EEPROM, SRAM ou contadores prontos. Os custos são contados em portas e flip-flops.
2. **Simulador, programas e documentação em sincronia.**
3. **Hardware mínimo:** só existe o que algum programa usa.
4. **Tempos em CLOCK**, nunca em ns.
5. **Português** em tudo e textos leves.

## 3. Arquitetura atual

```
PC(11) → ROM 2048×16 → [OP|F|N] → decodificador (portas) → sinais
RAM 256×8: endereço = N, A ou PONTEIRO (mux 4×1)
VRAM 128×8: endereço = CURSOR; lida e gravada pela CPU
ULA: somador + unidade lógica (F = tabela) + SHR → R, Z, C
mux de A: N | MEMÓRIA (RAM ou VRAM) | ULA | teclado
```

| Cód. | Instr. | F | Efeito | Flags |
|---|---|---|---|---|
| 0 | LDI n | — | A = n | — |
| 1 | LD m | — | A = RAM[m] | — |
| 2 | ST m | — | RAM[m] = A | — |
| 3 | LDR | — | A = RAM[A] | — |
| 4/5 | ARIT m / ARITI n | NG SHR USA_C SUB | ADD SUB ADC SBC SHR CMP | Z, C |
| 6/7 | LOG m / LOGI n | tabela-verdade | AND OR XOR TST NOT… | Z |
| 8–12 | JMP JZ JNZ JC JNC | destino 11 bits | | — |
| 13 | IN | — | A = teclado (0 = nada) | — |
| 14 | MEM | RAM? + operação | VOUT VIN VPOS / STP LDP PTR | — |
| 15 | — | — | livre | — |

Detalhes completos: docstring do `hardware.py` e `componentes/00-LEIA-ME.md`.

## 4. Decisões tomadas e implementadas (ver `Resumo-Melhorias.md`)

| Tema | Decisão |
|---|---|
| ULA lógica | mux 4×1 por bit usado como porta programável; a tabela-verdade vem dos bits 11..8 |
| ULA aritmética | os bits 8, 9, 10 e 11 ligam direto em SUB, usa-C, SHR e não-grava |
| Flags | Z + C (padrão 6502: C = 1 → A ≥ B), com JC / JNC |
| Ponteiros | dois iguais: RAM (8 bits) e cursor da VRAM (7 bits) |
| Display | VRAM que pode ser lida (`VPOS`/`VIN`/`VOUT`), separada da RAM |
| Decodificador | em portas (EEPROM descartada) |

## 5. Modelo de arquivo de componente

Todo arquivo novo em `componentes/NN-nome.md` segue esta estrutura:

```
# NN · Nome (resumo de 1 linha)
Para que serve (2–3 linhas).
## Pinos            tabela: Pino | Direção | Largura | Descrição
## Equações         em AND / OR / NOT / XOR
## Circuito         esquema ASCII em portas + "Portas: N × AND, …"
## Tabela verdade   ou tabela de testes gerada pelo simulador
## Como testar sozinho   chaves nas entradas, LEDs nas saídas
## Tempo            em × CLOCK (combinacional = 0 × CLOCK)
## Correspondência com o simulador
```

- **Sem** linha "Em CI".
- Reaproveite os blocos existentes: somador completo (01), somador 8 bits (02), XOR controlado (03), unidade lógica (04), mux 2×1 (05), detector de zero (06), mux 4×1 (10), incrementador (11), registrador-ponteiro (21).
- Atualize o índice e a tabela de sinais em `00-LEIA-ME.md`.

## 6. Checklist de uma mudança no hardware

- [ ] Algum programa precisa disso? Não dá para fazer com o que já existe?
- [ ] Custo em portas e flip-flops calculado
- [ ] Efeito no caminho crítico (`½ × CLOCK ≥ ROM → decod. → RAM → ULA → mux A`)
- [ ] `hardware.py`: simulação porta a porta + montador (com apelidos para nomes antigos)
- [ ] `doom.py`, `bola.py` e `tetris.py` montam e rodam (`python -c "from hardware import montar; import doom; print(len(montar(doom.PROGRAMA)))"`)
- [ ] `componentes/`: arquivo da peça + 00 (índice e sinais) + 17 (decodificador) + 20 (tempo) + 22 (testes de integração)
- [ ] Tabelas com colunas alinhadas, tempos em CLOCK
- [ ] `esquema/dados.py`: bloco, fios, custo e caminho das instruções novas
- [ ] `esquema/portas.py`: circuito em portas do componente (e testar contra `hardware.py`)
- [ ] `Resumo-Melhorias.md` atualizado (marcar o que foi implementado)

## 7. Pontos de atenção conhecidos

- `IN` devolve 0 sem evento (no hardware e no simulador). Para esperar tecla: `IN` / `TST` / `JZ`.
- Só ARIT/ARITI mudam C; só ARIT/ARITI/LOG/LOGI mudam Z. `LD`, `LDI`, `ST`, `LDR`, saltos, `IN` e MEM **não mudam flags**.
- Testes de equivalência: compare as imagens geradas com uma sequência fixa de teclas (`pc.teclado.ler` substituído).
- A RAM liga com lixo: o programa inicializa tudo o que usa.
- A CPU não lê dados da ROM: dados fixos só entram por `LDI`.
