# 15 · ROM de programa (2048 × 16 bits)

Guarda o programa (`doom.py` montado). O hardware só **lê**. Não há dados na
ROM, só instruções.

## Pinos

| Pino         | Direção | Largura | Descrição |
|--------------|---------|---------|-----------|
| `END[10:0]`  | entrada | 11      | vem do PC |
| `DADO[15:0]` | saída   | 16      | instrução |

## Formato da palavra

```
 15 14 13 12 | 11 10  9  8 | 7  6  5  4  3  2  1  0
 ---- OP --- | ---- F ---- | --------- N ---------
```

| Campo        | Bits   | Vai para                                                                  |
|--------------|--------|---------------------------------------------------------------------------|
| `OP[3:0]`    | 15..12 | decodificador (arquivo 17)                                                |
| `F[3:0]`     | 11..8  | decodificador e ULA: função (ARIT), tabela-verdade (LOG), subfunção (MEM) |
| `N[7:0]`     | 7..0   | número imediato ou endereço de RAM                                        |
| `DEST[10:0]` | 10..0  | só nos saltos: destino (arquivo 13); bit 11 = 0                           |

Os mesmos fios servem aos dois usos: nos saltos o decodificador ignora F.

## Implementação prática

**Dois chips de 2048 × 8** (ex.: EEPROM 28C16 ou AT28C16), com os mesmos
11 fios de endereço:

| Chip      | Guarda              | Saídas       |
|-----------|---------------------|--------------|
| ROM ALTA  | bits 15..8 (OP + F) | `DADO[15:8]` |
| ROM BAIXA | bits 7..0 (N)       | `DADO[7:0]`  |

`/CE` e `/OE` ligados em GND (sempre lendo), `/WE` em VCC (nunca grava no circuito).

O `doom.py` usa **1 596 de 2048** palavras (`bola.py`: 76, `tetris.py`: 960).

## Gerando os arquivos para o gravador de EEPROM

```python
import hardware, doom
rom = hardware.montar(doom.PROGRAMA)
rom += [0xF000] * (2048 - len(rom))          # completa com o código 15 (não faz nada)
open("rom_alta.bin", "wb").write(bytes(w >> 8 for w in rom))
open("rom_baixa.bin", "wb").write(bytes(w & 0xFF for w in rom))
```

As primeiras palavras do programa (para conferir o gravador):

| Endereço      | Palavra | Alta | Baixa | Instrução |
|---------------|---------|------|-------|-----------|
| 0             | 00FF    | 00   | FF    | LDI 255   |
| 1             | 20C0    | 20   | C0    | ST 0xC0   |
| 2             | 00BF    | 00   | BF    | LDI 191   |
| 3             | 20C1    | 20   | C1    | ST 0xC1   |
| 4             | 0088    | 00   | 88    | LDI 136   |
| 1595 (último) | 8000    | 80   | 00    | JMP 0     |

## Como construir uma ROM (esquema lógico)

A versão final usa EEPROM, mas a ROM é um circuito simples de entender e de
montar em tamanho pequeno. Esta seção mostra como ela é por dentro.

### A ideia: uma tabela feita de fios

A ROM é **combinacional**: a saída depende só do endereço, como uma tabela
fixa. Ela tem só duas partes:

1. **Decodificador de endereço**: liga **uma única linha** (a do endereço
   pedido) e deixa todas as outras em 0. É o mesmo tipo de circuito do
   decodificador de instruções (arquivo 17).
2. **Matriz**: linhas (uma por palavra) cruzando colunas (uma por bit). Em
   cada cruzamento há um **diodo** (o bit vale 1) ou não há nada (o bit vale 0).

Cada coluna é, na prática, um **OR** das linhas que têm diodo nela:

```
bit n da saída = OR de todas as linhas Lk cuja palavra k tem o bit n = 1
```

### Exemplo mínimo: 4 palavras de 2 bits

| Endereço | Palavra |
|----------|---------|
| 0        | 01      |
| 1        | 10      |
| 2        | 11      |
| 3        | 00      |

```
                  D1              D0
                  │               │
 L0 ──────────────┼───────►|──────┤        palavra 0 = 01
 L1 ──────►|──────┤               │        palavra 1 = 10
 L2 ──────►|──────┼───────►|──────┤        palavra 2 = 11
 L3 ──────────────┼───────────────┤        palavra 3 = 00
                  │               │
                 [R]             [R]       10 kΩ (pull-down)
                  │               │
                 GND             GND

 ──►|──  = diodo (anodo na linha, catodo na coluna)
```

Em portas lógicas, é exatamente:

```
D0 = L0 OR L2
D1 = L1 OR L2
```

Como funciona:
- O decodificador põe **1** (5 V) só na linha escolhida; as outras ficam em 0.
- Onde há diodo, o 1 da linha passa para a coluna → aquele bit lê **1**.
- Onde não há diodo, nada chega; o resistor de **pull-down** segura a coluna
  em **0**.
- O diodo é uma "válvula de mão única": deixa a linha acesa levantar a coluna,
  mas impede que a coluna acesa volte e "acenda" as outras linhas. Sem diodo
  (só um fio), todas as linhas ligadas àquela coluna entrariam em curto.

### Decodificador de endereço

Para 2 bits de endereço (4 linhas), cada linha é um AND:

```
L0 = /A1 · /A0        L2 =  A1 · /A0
L1 = /A1 ·  A0        L3 =  A1 ·  A0
```

Para 4 bits (16 linhas): cada linha é um AND de 4 entradas, com cada bit
invertido ou não. Portas: **4 NOT + 16 AND de 4 entradas** (o mesmo
circuito do passo 1 do arquivo 17).

Há duas formas de ligar a matriz:

| Forma           | Linhas do decodificador                      | Matriz                                                | Diodo significa | Diodos para o `doom.py` |
|-----------------|----------------------------------------------|-------------------------------------------------------|-----------------|-------------------------|
| A (recomendada) | AND de 4 entradas: linha escolhida em **1**  | diodo anodo na linha, catodo na coluna; **pull-down** | bit **1**       | 5 508                   |
| B               | NAND de 4 entradas: linha escolhida em **0** | diodo catodo na linha, anodo na coluna; **pull-up**   | bit **0**       | 20 028                  |

O programa tem muito mais bits 0 do que 1 (5 508 uns em 25 536 bits), então a
forma A usa **~3,6× menos diodos**.

### ROM de teste montável: 16 palavras × 16 bits

É o tamanho certo para os testes do arquivo 22, antes de ter a EEPROM gravada.

```
          A3 A2 A1 A0  (bits 3..0 do PC)
           │  │  │  │
        ┌──┴──┴──┴──┴──┐
        │ decodificador│  4 NOT + 16 AND de 4 entradas
        │    4 → 16    │  (passo 1 do arquivo 17)
        └──────────────┘
         │ │ │ ... │                 → L0 .. L15 ativas em 1
         │ │ │ ... │
   L0 ───┼─┼─┼─────┼──────────── 16 cruzamentos (D15 .. D0)
   L1 ─────┼─┼─────┼────────────
   ...                              diodo 1N4148 onde o bit é 1
   L15 ────────────┼────────────
                                  │ │ │ ... │
                                 [pull-down 10 kΩ em cada coluna]
                                  │ │ │ ... │
                                 D15 ...  D0  → para o decodificador (OP),
                                                mux do PC (DEST) e N
```

- 4 NOT + 16 AND de 4 entradas, até 256 diodos, 16 resistores.
- Os bits 10..4 do PC ficam sem uso: o programa de teste cabe nos endereços
  0 a 15.

Exemplo: o programa da **Etapa 3** do arquivo 22 (conta de 0 a 255):

| End. | Instrução | Palavra | Bits (OP F N)      | Diodos nos bits |
|------|-----------|---------|--------------------|-----------------|
| 0    | `LDI 0`   | 0000    | 0000 0000 00000000 | nenhum          |
| 1    | `ADDI 1`  | 5001    | 0101 0000 00000001 | 14, 12, 0       |
| 2    | `JNZ 1`   | A001    | 1010 0000 00000001 | 15, 13, 0       |
| 3    | `JMP 0`   | 8000    | 1000 0000 00000000 | 15              |

São só **6 diodos**. Trocar de programa = trocar diodos de lugar (dá para
montar com diodos em soquete ou em barra de pinos).

### Escalando para 2048 × 16: decodificação em 2 dimensões

Um decodificador de 11 bits teria 2048 linhas, cada uma um AND de 11 entradas:
inviável. As memórias de verdade dobram o endereço em **linha × coluna**:

```
  A[10:4] (7 bits) ──► decodificador 7 → 128 linhas
  A[3:0]  (4 bits) ──► escolhe 1 de 16 palavras dentro da linha

  matriz: 128 linhas × 256 colunas  (cada linha guarda 16 palavras × 16 bits)

         ┌──────────── linha selecionada (1 de 128) ────────────┐
         │ palavra 0  │ palavra 1  │ ...        │ palavra 15    │  256 colunas
         │ 16 bits    │ 16 bits    │            │ 16 bits       │
         └─────┬──────┴─────┬──────┴────────────┴──────┬───────┘
               │            │                          │
        para cada bit n (0..15): mux 16 → 1 escolhe a coluna do bit n
        da palavra A[3:0]  →  DADO[n]
```

| Organização | Linhas do decodificador   | Muxes na saída | Cruzamentos |
|-------------|---------------------------|----------------|-------------|
| 1 dimensão  | 2048 (AND de 11 entradas) | nenhum         | 32 768      |
| 2 dimensões | 128 (AND de 7 entradas)   | 16 × (16 → 1)  | 32 768      |

O número de bits guardados é o mesmo; o que encolhe muito é o decodificador.
A RAM (arquivo 16) e a EEPROM usam essa mesma organização.

### Por que a versão final é EEPROM

A EEPROM (28C16) é **exatamente este esquema** dentro de um chip: decodificador
em 2 dimensões + matriz. A diferença é que, no lugar do diodo, cada cruzamento
tem um transistor que pode ser ligado ou desligado eletricamente pelo gravador.
Com 32 768 bits (5 508 diodos na forma A), montar em discreto é possível mas
enorme; dois 28C16 fazem o mesmo em dois chips e podem ser regravados.

## Testes

**EEPROM (versão final):**
1. Grave os `.bin`.
2. Coloque 11 chaves no endereço e 16 LEDs na saída.
3. Confira os endereços da tabela acima.
4. Endereço 1596 em diante deve mostrar F000.

**ROM de diodos (versão de teste):**
1. Sem nenhum diodo: todos os 16 LEDs apagados em qualquer endereço
   (confirma os pull-downs).
2. Com 4 chaves no endereço, confira que só a linha certa vai a 1 (meça as
   saídas dos AND com LED ou multímetro).
3. Coloque os 6 diodos da Etapa 3 e confira as 4 palavras da tabela.
4. Se um bit acende em endereços errados, há um diodo invertido ou faltando o
   pull-down daquela coluna.

## Tempo

**0 × CLOCK**: a leitura é combinacional, sem pulso de relógio. Mudou o PC,
depois do "tempo de acesso" do chip a instrução aparece na saída.

Esse tempo de acesso é o **primeiro** trecho da fila que precisa caber em
½ × CLOCK (arquivo 20). Depois do somador, é o que mais pesa.
