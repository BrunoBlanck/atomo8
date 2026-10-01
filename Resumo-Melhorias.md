# Resumo de melhorias (ULA, RAM, ROM e display)

> **Status (2026-10-01): tudo implementado** em `hardware.py`, `doom.py`, `bola.py`, `gerar_mapa.py` e `componentes/`. Ver seção 10.
>
> **Regra do projeto:** tudo é feito com **portas lógicas** (AND, OR, NOT, XOR…) e flip-flops montados com portas. Nenhum chip pronto (74HCxxx, EEPROM, SRAM). Por isso os custos abaixo estão em **portas**, não em chips.

---

## 1. Como está hoje

| Recurso | Uso | Observação |
|---|---|---|
| ROM | 1696 / 2048 palavras (83%) | 40% são `OUT` e 23% são `LDI` (o 3D está escrito por extenso) |
| RAM | 169 bytes do labirinto + 15 de variáveis | sobram ~70 bytes |
| ULA | ADD, SUB, AND | só a flag Z: o programa só pergunta "é igual?" |
| Display | 128 bytes, a CPU só escreve, sempre em sequência | redesenha a tela inteira a cada quadro |

**A reserva escondida:** nas instruções que não são salto, os **bits 11..8 estão sempre em 0**. São 4 bits livres para crescer sem mudar o formato da instrução.

```
   15..12   11   10..8    7..0
  [ OP  ]  [0]  [pág.]  [ N ]     ← em LDI, LD, ST, ULA… os bits 11..8 sobram
```

---

## 2. Gargalos

1. **Não existe gravação indireta (STR).** Existe `LDR`, mas o inverso não. Por isso o labirinto precisa de 169 `ST` fixos, e não dá para ter filas, vetores ou mapas gerados na hora.
   - Causa: o A sozinho não pode ser endereço **e** dado ao mesmo tempo.
2. **Só existe a flag Z:** não há como perguntar maior/menor.
3. **O display só recebe dados**, então não serve de memória nem para detectar colisão.
4. **Não há sub-rotinas:** o código repetido é copiado por extenso (os 680 `OUT`). *Fica para depois.*
5. **O `IN` do simulador espera tecla**, mas no hardware ele devolve 0 se nada foi apertado. Jogos em tempo real congelariam no simulador.

---

## 3. ULA

### O que entra

| Operação | Para que serve | Custo |
|---|---|---|
| **Flag C + JC / JNC** | maior/menor, contas de 16 bits | 1 flip-flop + 2 opcodes |
| **OR** | acender pixel sem apagar os outros | ver "Como construir" |
| **XOR** | inverter pixel, NOT (`XOR 255`), sorteio | ver "Como construir" |
| **SHR** | dividir por 2, percorrer bits | só fios |
| **ADC / SBC** | contas de 16 bits | quase nada depois da flag C |
| **"Testa A"** | atualizar Z sem mudar A (hoje é preciso `CMPI 0`) | grátis |

### O que fica de fora

- **MUL / DIV** → laço com SHR + ADD
- **SHL** → `ADD` de A com ele mesmo
- **NOT / NEG** → `XOR 255` / `0 − A`
- **INC / DEC** → `ADDI 1` / `SUBI 1`
- **Flag N** → o C já cobre as comparações

### Regra da flag C (padrão do 6502)

Depois de `SUB` ou `CMP`:

- **C = 1 → A ≥ B**
- **C = 0 → A < B**

### Como construir: 2 opções (em portas)

| Opção | Funções lógicas | Portas a mais (aprox.) | Comentário |
|---|---|---|---|
| A) Portas dedicadas (OR + XOR + mux de resultado 8×1) | AND, OR, XOR | ~120 | cada operação nova = portas novas e mais uma entrada no mux |
| **B) Mux 4×1 por bit como porta lógica programável (ideia do Gigatron)** | **todas as 16** | **~100** | **recomendada** |

*(O 74181, uma ULA num chip só, ficou fora: é um chip pronto.)*

**Como funciona a opção B:** é o mux 4×1 do arquivo 10, só que montado ao contrário. Os bits `Aₙ` e `Bₙ` entram na **seleção** e a **tabela-verdade** entra nos 4 dados. Essa tabela vem dos bits 11..8 da instrução.

```
Rₙ = (T0 · /Aₙ · /Bₙ) + (T1 · /Aₙ · Bₙ) + (T2 · Aₙ · /Bₙ) + (T3 · Aₙ · Bₙ)
```

Por bit: 2 NOT + 4 AND de 3 entradas + 3 OR = **9 portas**. Para os 8 bits são **72 portas**, que substituem as 8 AND de hoje.

| Tabela (bits 11..8) | Função |
|---|---|
| 1000 | AND |
| 1110 | OR |
| 0110 | XOR |
| 1100 | passa A ("testa A") |
| 0011 | NOT A |

### Formato das instruções

```
LOG  m / LOGI n  : bits 11..8 = tabela-verdade (ocupa os 4 bits livres)
ARIT m / ARITI n : bits 10..8 = 000 ADD  001 SUB  010 ADC  011 SBC  100 SHR
                   bit 11     = não grava A (vira CMP)
```

- São 4 opcodes de ULA (hoje são 6).
- O LOG usa os 4 bits livres para a tabela-verdade, então não sobra bit para dizer se o operando vem da RAM ou é um número. Por isso `LOG` e `LOGI` precisam de **opcodes separados**.
- Os nomes antigos (`ADDI`, `CMPI`, `ANDI`…) continuam como apelidos no montador.

### Saída da ULA

Mux de resultado: **2×1 → 4×1** (somador · lógica · SHR · livre), o mesmo circuito do arquivo 10.

### Bits da ARIT ligados direto (sem decodificar)

| Bit | Liga em | Efeito |
|---|---|---|
| 8 | inversor de B (arquivo 03) | 1 = subtrai |
| 9 | escolha do vai-um de entrada | 1 = usa o C (ADC/SBC) |
| 10 | mux de resultado | 1 = SHR |
| 11 | escrita em A | 1 = não grava (CMP) |

Assim, `000` = ADD, `001` = SUB, `010` = ADC, `011` = SBC e `100` = SHR saem **sem nenhuma porta de decodificação**, do mesmo jeito que a tabela-verdade do LOG.

---

## 4. RAM

### Registrador de endereço (ponteiro)

Um contador que **carrega o valor de A** e **soma 1 sozinho** depois de cada acesso.

| Instrução | Efeito |
|---|---|
| `PTR` | ponteiro = A |
| `LDP` | A = RAM[ponteiro], ponteiro + 1 |
| `STP` | RAM[ponteiro] = A, ponteiro + 1 |
| `LDR` | **continua como hoje**: A = RAM[A] |

O `LDR` fica como está porque o doom usa 28 vezes. Os acessos pelo ponteiro ganham nomes novos (`LDP`, `STP`).

- **Destrava:** vetores, filas (Snake), laços que limpam ou preenchem a RAM.
- **Labirinto:** só economiza ROM junto com o SHR. O mapa vai compactado em bits (22 bytes gravados com `LDI` + `ST`), e um laço com `LDR` + `SHR` + `STP` o desenrola na RAM. São ~70 palavras de ROM contra as 171 de hoje.
- **Custo:** 8 flip-flops + incrementador (8 XOR + 7 AND, como o do arquivo 11) + mux 2×1 de carga (arquivo 05) ≈ **8 flip-flops + ~40 portas**.
- **Inspiração:** os registradores X/Y do Gigatron.

---

## 5. Display como segunda memória (VRAM)

| | Hoje | Proposto |
|---|---|---|
| Acesso | só escreve, em sequência | escreve **e lê**, em qualquer endereço |
| Desenho | redesenha os 128 bytes | muda só o que mudou |
| RAM principal | dividida entre o jogo e a tela | fica toda para o jogo |

### Instruções

| Instrução | Efeito |
|---|---|
| `VPOS` | cursor = A |
| `VIN` | A = VRAM[cursor] (o cursor não anda) |
| `VOUT` | VRAM[cursor] = A, cursor + 1 (é o `OUT` atual) |

Acender um pixel:

```
LD   END   ; endereço do byte
VPOS
VIN        ; lê o byte que já está na tela
LOGI OR M  ; liga o bit
VOUT       ; grava de volta no mesmo lugar
```

### Ganhos

- **Bola:** ~300 → ~15 instruções por quadro (cerca de 20× mais rápido).
- **Colisão:** é só ler o pixel. É o mesmo truque do CHIP-8 (desenhar com XOR e ler o resultado).
- **Doom:** continua igual, porque o cursor dá a volta sozinho depois de 128 bytes.

### Decisões confirmadas pela pesquisa

- **VRAM separada da RAM** está certo: dentro da RAM ela ocuparia metade.
- **SSD1306 serial não deixa ler** a memória de vídeo, então a VRAM tem que ser **nossa**, montada com portas e flip-flops como a RAM.
- **Leitura de volta sem tri-state:** a RAM e a VRAM entram num **mux 2×1** (arquivo 05) antes do mux de A, que continua com 4 entradas. Custo: ~25 portas.
- **O cursor da VRAM e o ponteiro da RAM são a mesma peça.** É um projeto só, construído **duas vezes** (ver decisão 2).
- **Colisão feita pelo próprio hardware** (estilo CHIP-8) não vale a pena: `VIN` + AND/XOR resolvem.

### Opcional (depois)

**Tela dupla:** uma página é mostrada enquanto a outra é desenhada (`VSHOW` no opcode 15). Em portas, isso significa **dobrar a VRAM** (+1024 bits), então só vale se a imagem "rasgar" muito no hardware real.

---

## 6. ROM

- **Antes:** 1696 / 2048 palavras. **Agora:** 1596 (sobram ~450).
- **Onde vai o espaço:** os 680 `OUT` + 392 `LDI` do 3D por extenso e os 169 `ST` do labirinto.
- **Com `STP` + `SHR`:** o labirinto cai de ~171 para ~70 palavras (seção 4). A CPU não tem como ler dados da ROM, então o mapa continua vindo de `LDI`, só que compactado em bits.
- **Sub-rotinas** economizariam mais ainda, mas o endereço de volta tem 11 bits e a RAM guarda 8. *Fica para depois.*

---

## 7. Conjunto de instruções

| Cód. | Instrução | Bits 11..8 | Cód. | Instrução |
|---|---|---|---|---|
| 0 | LDI n | — | 8 | JMP |
| 1 | LD m | — | 9 | JZ |
| 2 | ST m | — | 10 | JNZ |
| 3 | LDR | — | 11 | **JC** |
| 4 | **ARIT m** | função + não grava | 12 | **JNC** |
| 5 | **ARITI n** | função + não grava | 13 | IN |
| 6 | **LOG m** | tabela-verdade | 14 | **MEM** (ver abaixo) |
| 7 | **LOGI n** | tabela-verdade | 15 | livre (`VSHOW`?) |

**MEM (opcode 14):** a operação vem nos bits 11..8.

| Bits 11..8 | Instrução | Efeito |
|---|---|---|
| 0000 | `VOUT` | VRAM[cursor] = A, cursor + 1 (o `OUT` de antes) |
| 0001 | `VIN` | A = VRAM[cursor] |
| 0010 | `VPOS` | cursor = A |
| 0100 | `STP` | RAM[ponteiro] = A, ponteiro + 1 |
| 0101 | `LDP` | A = RAM[ponteiro], ponteiro + 1 |
| 0110 | `PTR` | ponteiro = A |

Codificação simétrica: **bit 10** = qual memória (0 VRAM, 1 RAM), **bits 9..8** = operação (00 grava, 01 lê, 10 carrega o ponteiro). Assim o decodificador gasta menos portas.

- Os 16 opcodes ficam ocupados e ainda sobra o 15.
- As instruções de hoje mantêm o comportamento; só os números de opcode mudam, e o montador cuida disso.

---

## 8. Ordem sugerida

| # | Mudança | Custo |
|---|---|---|
| 0 | `IN` sem esperar no simulador | só software |
| 1 | Flag C + JC / JNC | 1 flip-flop + ~6 portas |
| 2 | Lógica programável (mux 4×1 por bit) | ~100 portas |
| 3 | Ponteiro da RAM (`PTR`, `LDP`, `STP`) | 8 flip-flops + ~40 portas |
| 4 | Cursor + leitura da VRAM | ~35 portas a mais no contador + ~25 do mux de leitura |
| 5 | SHR, ADC, SBC | SHR = só fios; ADC/SBC ≈ 4 portas |
| — | Sub-rotinas, tela dupla | depois |

---

## 9. Decisões

### 1. ULA → lógica programável (opção B)

**Por quê:**
- Em portas, as duas opções custam parecido (~100 contra ~120).
- A B faz as **16 funções lógicas**, não só 3.
- Reaproveita o circuito do **mux 4×1** (arquivo 10), que já está explicado.
- A tabela-verdade vem direto da instrução: nada para decodificar.

**Cuidados:**
- A unidade lógica fica **em paralelo** com o somador. O caminho mais longo continua sendo o vai-um do somador, então o CLOCK não muda.
- `LOG` e `LOGI` precisam de opcodes separados (seção 3).

### 2. Ponteiro → **dois**, iguais (um para a RAM, outro para a VRAM)

**Por quê:**
- Copiar RAM → tela é o uso mais comum (corpo do Snake, tijolos, placar). Com um ponteiro só, seria preciso recarregá-lo a **cada byte**:

  | Copiar 1 byte | Um ponteiro | Dois ponteiros |
  |---|---|---|
  | instruções | ~6 | **2** (`LDP` + `VOUT`) |

- O cursor da VRAM precisa avançar sozinho depois de 128 bytes, para o doom continuar funcionando sem mudanças.
- O custo extra é baixo (8 flip-flops + ~40 portas) e o **projeto é o mesmo**: um arquivo em `componentes/`, construído duas vezes.

| | Ponteiro da RAM | Cursor da VRAM |
|---|---|---|
| Bits | 8 | 7 |
| Carrega de | A (`PTR`) | A (`VPOS`) |
| Soma 1 em | `LDP`, `STP` | `VOUT` |

### 3. Decodificador → **portas** (EEPROM descartada pela regra do projeto)

**Por quê dá certo com portas:** quase nenhum campo novo precisa ser decodificado.

| Campo | Decodificação |
|---|---|
| Opcode (4 bits) | igual a hoje: 4 NOT + 16 AND de 4 entradas (arquivo 17) |
| Tabela-verdade do LOG (bits 11..8) | **nenhuma**: vai direto para a ULA |
| Função da ARIT (bits 11..8) | **nenhuma**: cada bit liga direto num ponto da ULA (seção 3) |
| Subfunção do MEM (bits 11..8) | 4 NOT + 6 AND de 5 entradas (linha do opcode 14 + 4 bits) |
| Saltos | bits 11..8 fazem parte do destino; o decodificador ignora |

- **Custo extra:** ~15 portas, mais os OR que juntam as linhas em cada sinal.
- **Tempo:** continua sendo só portas, então o CLOCK não piora (com EEPROM ele pioraria).

---

## 10. O que foi implementado

| Onde | Mudança |
|---|---|
| `hardware.py` | ULA porta a porta (somador + unidade lógica + SHR), flags Z e C, decodificador em portas (`decodifica`), lógica de salto com C, ponteiro e cursor, VRAM lida, `IN` sem esperar, montador com apelidos |
| `doom.py` | `OUT` → `VOUT`; labirinto compactado (171 → 69 palavras); vitória espera tecla com `IN`/`TST`/`JZ`. Imagens idênticas às de antes (401 quadros comparados) |
| `bola.py` | só muda o byte da bola (`VPOS`/`VIN`/`XOR`/`VOUT`), bordas com `JNC`; ~75 instruções por passo |
| `gerar_mapa.py` | gera o bloco compactado |
| `componentes/` | 04 virou unidade lógica; 09 virou flags Z e C; 21 novo (registrador-ponteiro); integração passou para 22; demais atualizados e sem "Em CI" (exceto memórias e peças analógicas, decisão pendente) |

**Custo de tempo:** ligar ficou mais lento (~180 → ~2 130 × CLOCK, uma vez só), em troca de 102 palavras de ROM.

---

## Referências

- [ULA do Isetta / Gigatron (mux como lógica)](https://hackaday.io/project/190345-isetta-ttl-computer/log/217189-the-alu-of-isetta)
- [Understanding the Gigatron](https://github.com/monsonite/Understanding-the-Gigatron-TTL-Computer)
- [74181 (Wikipedia)](https://en.wikipedia.org/wiki/74181) (só como referência de ideia)
- [ULA Hack (Nand2Tetris)](https://github.com/Olical/nand2tetris/blob/master/chips/arithmatic/ALU.hdl)
- [6502: instruções de comparação](https://6502.org/tutorials/compare_beyond.html)
- [PDP-8: instruções de memória](https://homepage.cs.uiowa.edu/~jones/pdp8/man/mri.html)
- [CHIP-8 (Wikipedia)](https://en.wikipedia.org/wiki/CHIP-8)
- [SSD1306 datasheet](https://www.buydisplay.com/download/ic/SSD1306.pdf)
