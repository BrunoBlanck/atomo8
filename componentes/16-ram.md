# 16 · RAM (256 × 8 bits)

Toda a memória de dados: o labirinto (169 bytes) e as variáveis do jogo.

## Pinos

| Pino        | Direção | Largura | Descrição                                 |
|-------------|---------|---------|-------------------------------------------|
| `END[7:0]`  | entrada | 8       | vem do mux de endereço (N, A ou ponteiro) |
| `DIN[7:0]`  | entrada | 8       | dado a gravar = registrador A             |
| `DOUT[7:0]` | saída   | 8       | dado lido (mux B da ULA e mux de memória) |
| `/WE`       | entrada | 1       | 0 = grava (pulso)                         |

## De onde vem o endereço

Mux 4×1 de 8 bits (circuito do arquivo 10), seleção `END_SRC[1:0]`:

| END_SRC | Endereço                   | Instruções            |
|---------|----------------------------|-----------------------|
| 00      | N (bits 7..0 da instrução) | LD, ST, ARIT m, LOG m |
| 01      | A                          | LDR                   |
| 10      | ponteiro (arquivo 21)      | STP, LDP              |
| 11      | sem uso                    | —                     |

`END_SRC0 = L3` (LDR) e `END_SRC1 = MEM` (arquivo 17). Nas instruções de
vídeo o mux também escolhe o ponteiro, mas a RAM não grava e o dado lido
é descartado.

## Quem usa a RAM

| Uso      | Instruções    | Sinal                                 |
|----------|---------------|---------------------------------------|
| gravação | ST, STP       | `RAM_WE = L2 + M_GRAVA·F2`            |
| leitura  | LD, LDR, LDP  | DOUT → mux de memória (05) → mux de A |
| leitura  | ARIT m, LOG m | DOUT → mux B (05) → ULA               |

O mux de memória (arquivo 05, seleção `MEM_VID`) escolhe entre RAM (0) e
VRAM (1) antes da entrada 01 do mux de A. Sem barramento compartilhado.

## Comportamento

- **Leitura**: sempre ativa. Mudou o endereço, depois do tempo de acesso o dado
  aparece em DOUT. Não depende de relógio.
- **Escrita** (ST, STP): quando `/WE` vai a 0, DIN é gravado em `END`.
  `/WE = NOT (RAM_WE AND CLK_BAIXO)` → o pulso só acontece na metade baixa do
  relógio, quando endereço e dado já estão estáveis (arquivo 20).

## Mapa de uso

| Endereço  | Conteúdo                                                                                     |
|-----------|----------------------------------------------------------------------------------------------|
| 0x00–0xA8 | labirinto 13×13, **1 byte por célula**: parede = 255, livre = 0. Célula (x, y) em `13*y + x` |
| 0xA9–0xAF | sobra do desenrolar (o laço grava 22 × 8 = 176 bytes; sem uso)                               |
| 0xB0–0xBE | variáveis do jogo (lista em `doom.py`, seção `.ram`)                                         |
| 0xBF      | livre                                                                                        |
| 0xC0–0xD5 | labirinto compactado, 1 bit por célula (só usado ao ligar)                                   |
| 0xD6–0xD8 | variáveis do desenrolar (`MSRC`, `MBYTE`, `MCNT`)                                            |
| 0xD9–0xFF | livre                                                                                        |

Ao ligar, o doom grava os 22 bytes compactados (`LDI` + `ST`) e um laço
`LDR` / `SHR` / `JNC` / `STP` desenrola cada bit em 1 byte, a partir do
ponteiro = 0. Gerado por `gerar_mapa.py`.

Por que 1 byte por célula (e parede = 255): consultar uma célula é um único
`LDR`, e como todos os bits da parede são 1, um `ANDI` pega direto o bit que
o programa quer (bit da profundidade no 3D, posição do pixel no mapa).

Ao ligar o conteúdo é lixo; o programa inicializa tudo que usa.

## Implementação prática

Um SRAM comum (ex.: 6116 = 2K×8 ou 62256 = 32K×8) usando só os 8 fios de
endereço de baixo; os outros vão para GND. `/CE = 0`.

**Cuidado com o barramento de dados:** esses chips têm os pinos de dado
**bidirecionais**. Ligue:
- `/OE = RAM_WE` (quando vai gravar, o chip para de "falar" no barramento);
- um buffer 74HC245 (ou 74HC541) do registrador A para os pinos de dado,
  habilitado só quando `RAM_WE = 1`.

Assim DOUT e DIN nunca brigam no mesmo fio.

## Nível de bit (para entender)

Cada bit é um latch (2 portas NOR em cruz ou 1 flip-flop D). Um byte = 8 latches
com o mesmo "enable". O decodificador de endereço 8 → 256 escolhe qual byte
recebe o pulso de escrita, e um mux 256 → 1 (por bit) escolhe qual byte sai.
São 2048 latches: dá para montar **uma fatia** (por exemplo 4 bytes, 2 bits de
endereço) para aprender, e usar o SRAM na versão final.

## Testes

Com chaves no endereço e no dado, LEDs em DOUT e um botão gerando o pulso `/WE`:

| Passo | END      | DIN        | /WE   | DOUT esperado |
|-------|----------|------------|-------|---------------|
| 1     | 00000000 | 10101010   | pulso | —             |
| 2     | 00000001 | 01010101   | pulso | —             |
| 3     | 11111111 | 11110000   | pulso | —             |
| 4     | 00000000 | (qualquer) | 1     | 10101010      |
| 5     | 00000001 | (qualquer) | 1     | 01010101      |
| 6     | 11111111 | (qualquer) | 1     | 11110000      |

Teste de endereços cruzados: grave o próprio endereço em cada posição
(0 em 0, 1 em 1, ..., 255 em 255) e leia de volta. Um fio de endereço solto
aparece como dois endereços mostrando o mesmo valor.

## Tempo

| Operação                              | Tempo     | Detalhe                                          |
|---------------------------------------|-----------|--------------------------------------------------|
| Leitura (LD, LDR, LDP, ARIT m, LOG m) | 0 × CLOCK | combinacional, dentro da metade alta (½ × CLOCK) |
| Escrita (ST, STP)                     | ½ × CLOCK | pulso `/WE` dura a metade baixa do relógio       |
| Instrução ST ou STP inteira           | 1 × CLOCK | como todas as outras                             |
| Mux de endereço 4×1                   | 0 × CLOCK | combinacional; está no caminho crítico (arq. 20) |

Se a RAM escolhida for lenta demais para caber no ciclo, a solução é aumentar
o CLOCK (arquivo 20). O simulador também permite testar uma RAM que precise
de CLOCKs extras de espera (`CLOCKS_EXTRA_LEITURA` e `CLOCKS_EXTRA_GRAVACAO` em
`hardware.py`). O hardware descrito aqui não tem esses ciclos de espera.
