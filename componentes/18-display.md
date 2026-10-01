# 18 · Display 32 × 32 (VRAM de 128 bytes + cursor de 7 bits)

Guarda a imagem e mantém o display aceso. É o dispositivo de saída **único**.
A CPU fala com ele por 3 instruções (grupo MEM, arquivo 17):

| Instr. | Efeito                             | Sinal                |
|--------|------------------------------------|----------------------|
| `VOUT` | VRAM[cursor] = A, cursor + 1       | `VID_WR` + `CUR_INC` |
| `VIN`  | A = VRAM[cursor] (cursor não anda) | `MEM_VID`, `A_WE`    |
| `VPOS` | cursor = A (7 bits de baixo)       | `CUR_LD`             |

`OUT` continua valendo como apelido de `VOUT`. O endereço da CPU é sempre o
**cursor**: um registrador-ponteiro de 7 bits (arquivo 21).

## Organização da imagem: bytes em pé

A tela é dividida em **4 páginas** de 8 linhas. Cada byte é um pedaço de
**uma coluna** com 8 pixels **na vertical**:

```
            coluna 0   coluna 1   ...   coluna 31
página 0    [byte 0]   [byte 4]         [byte 124]    linhas 0..7
página 1    [byte 1]   [byte 5]         [byte 125]    linhas 8..15
página 2    [byte 2]   [byte 6]         [byte 126]    linhas 16..23
página 3    [byte 3]   [byte 7]         [byte 127]    linhas 24..31

dentro de 1 byte:  bit 0 = linha de cima da página
                   bit 7 = linha de baixo da página
```

Endereço (7 bits) = `COLUNA[4:0] : PÁGINA[1:0]` = `4 × coluna + página`.

## Partes internas

| Parte                 | Tamanho                   | Função                                           |
|-----------------------|---------------------------|--------------------------------------------------|
| Cursor (arquivo 21)   | 7 bits                    | VPOS carrega; VOUT grava e avança; zera no reset |
| VRAM                  | 128 × 8 bits              | a imagem                                         |
| Contador de varredura | 7 bits de byte + 3 de bit | percorre a VRAM para acender a matriz            |
| Mux de endereço       | 7 bits, 2×1 (arquivo 05)  | CPU (cursor) ou varredura; SEL = `MEM_VID`       |

## Pinos (lado da CPU)

| Pino        | Direção | Descrição                                            |
|-------------|---------|------------------------------------------------------|
| `DADO[7:0]` | entrada | registrador A (grava e carrega o cursor)             |
| `VID_WR`    | entrada | VOUT: pulso de gravação (arquivo 17)                 |
| `CUR_INC`   | entrada | VOUT: cursor + 1 (mesmo fio que `VID_WR`)            |
| `CUR_LD`    | entrada | VPOS: cursor = A                                     |
| `MEM_VID`   | entrada | instrução de vídeo: mux de endereço escolhe o cursor |
| `CLK`       | entrada | relógio (o cursor grava na ↑CLK)                     |
| `CLK_BAIXO` | entrada | metade baixa do relógio (arquivo 20)                 |
| `/RST`      | entrada | zera o cursor                                        |
| `LIDO[7:0]` | saída   | VRAM[cursor] → mux de memória (05) → mux de A        |

## Como funciona

```
SEL_CPU          = MEM_VID                    (VOUT, VIN, VPOS)
end. da VRAM     = SEL_CPU ? cursor : varredura
pulso de escrita = VID_WR AND CLK_BAIXO

VOUT : no pulso  VRAM[cursor] = A ;  na ↑CLK  cursor = cursor + 1
VIN  : LIDO = VRAM[cursor] (combinacional) ;  na ↑CLK  A = LIDO
VPOS : na ↑CLK  cursor = A (7 bits)
```

- O cursor muda só na ↑CLK, **depois** do pulso de escrita: o byte vai para o
  endereço atual.
- 7 bits: depois de 127 o cursor volta sozinho a 0.
- A leitura da VRAM passa pelo **mux de memória** (arquivo 05, `MEM_VID` = 1
  escolhe a VRAM) e chega ao mux de A pela entrada 01, a mesma da RAM.

Como o cursor conta de 1 em 1 e o endereço é `4 × coluna + página`, os `VOUT`
seguidos **descem as 4 páginas de uma coluna e passam para a próxima**.

## Exemplos

**Acender 1 pixel** (END = `4 × x + y/8`, M = `1 << (y & 7)` na RAM):

```
LD   END
VPOS        ; cursor = END
VIN         ; A = byte atual (8 pixels)
OR   M      ; liga o pixel sem mexer nos outros
VOUT        ; grava (o cursor anda, mas não importa)
```

5 instruções = **5 × CLOCK**. Antes era preciso redesenhar a tela inteira.

**Desenhar e apagar** (como no CHIP-8): troque `OR M` por `XOR M`. Fazer de
novo apaga. É o que a bola usa (`bola.py`): ~75 × CLOCK por passo em vez de
~300 por quadro.

**Doom:** continua gravando **128 `VOUT` por quadro**, sem `VPOS`: o cursor
começa em 0 no reset e volta a 0 depois do 128º `VOUT`.

```
LDI  0     / VOUT     ; página 0 (linhas 0..7)
LDI  32    / VOUT     ; página 1 (linhas 8..15): pixel na linha 13
LDI  4     / VOUT     ; página 2 (linhas 16..23): pixel na linha 18
LDI  0     / VOUT     ; página 3 (linhas 24..31)
```

As páginas 2 e 3 do 3D são as páginas 1 e 0 com os bits em ordem invertida
(a parede é simétrica em cima e embaixo). O programa já tem os 4 valores
prontos dentro das instruções `LDI`.

## Custo (lado da CPU)

| Parte                       | Portas                | Flip-flops    |
|-----------------------------|-----------------------|---------------|
| cursor (arquivo 21, k = 7)  | 58                    | 7 (com clear) |
| mux de endereço 2×1, 7 bits | 1 NOT + 14 AND + 7 OR | —             |
| pulso de escrita            | 1 AND                 | —             |

O mux de memória (05) entra na conta do caminho de A (arquivo 22).

## Varredura (manter a imagem acesa)

Uma matriz de LED 32×32 é **multiplexada**: acende uma linha de pixels por
vez, rápido o bastante para o olho ver tudo junto.

```
contador de varredura (relógio PRÓPRIO: CLOCK_VIDEO)
para cada linha y (0..31):
    para cada coluna x (0..31):
        byte  = VRAM[4x + (y >> 3)]    ; página = 2 bits de cima de y
        pixel = bit (y & 7) do byte    ; mux 8 → 1
        desloca o pixel para os drivers de coluna
    trava e acende a linha y
```

A varredura **não usa o CLOCK da CPU**. Ela tem a sua própria constante:

```
CLOCK_VIDEO = período do relógio da varredura (1 pixel por pulso)
imagem completa = 1024 × CLOCK_VIDEO
```

Para a imagem não piscar: `1024 × CLOCK_VIDEO ≤ 1/60 s`. Isso não depende de
quão lenta a CPU for: com a CPU lenta a imagem só **muda** devagar.

## Conflito CPU × varredura

As duas querem o endereço da VRAM. Regra simples:
- durante **qualquer instrução de vídeo** (`MEM_VID = 1`: VOUT, VIN, VPOS) o
  mux escolhe o **cursor**: a CPU grava (VOUT) ou lê (VIN);
- no resto do tempo escolhe o **contador de varredura**.

Um pixel da varredura pode sair errado por 1 leitura nesse instante; fica
invisível.

## Tempo (lado da CPU)

| Operação                          | Tempo                                          |
|-----------------------------------|------------------------------------------------|
| `VOUT`, `VIN`, `VPOS`             | 1 × CLOCK cada                                 |
| pulso de gravação do byte na VRAM | ½ × CLOCK (metade baixa)                       |
| leitura (VIN)                     | 0 × CLOCK (combinacional, metade alta)         |
| avanço do cursor                  | 0 × CLOCK extra (na ↑CLK, depois do pulso)     |
| acender 1 pixel                   | 5 × CLOCK                                      |
| quadro 3D inteiro                 | 262 a 385 × CLOCK, média ~318 (128 são `VOUT`) |
| bola: 1 passo                     | ~75 × CLOCK + espera                           |

O caminho cursor → VRAM → mux de memória → mux de A é mais curto que o da RAM:
o cursor já está pronto no início do ciclo e não depende do decodificador.

## Implementação prática

- VRAM: um SRAM de 8 bits (ex.: 6116) usando 7 fios de endereço.
- Cursor e mux de endereço: em portas (arquivos 21 e 05).
- Displays OLED com controlador (SSD1306 etc.) usam o mesmo formato de bytes
  em pé e páginas de 8 linhas: dá para mandar os bytes direto.

## Testes (antes de ligar na CPU)

1. **Cursor**: testes do arquivo 21 (carrega, avança, segura, 127 → 0).
2. **VRAM**: reset, grave `00000001` → só o pixel (0,0) acende.
3. **Ordem**: reset, grave 4 bytes `11111111` → coluna 0 inteira acesa;
   mais 4 → coluna 1.
4. **Varredura**: grave 128 bytes `01010101` → listras horizontais de 1 pixel.
5. **Orientação**: (0,0) é o canto superior esquerdo; bit 0 é o pixel de cima.
6. **VPOS + VOUT**: A = 77, `VPOS`; A = `11111111`, `VOUT` → só o byte 77
   (coluna 19, página 1) acende; cursor = 78.
7. **VIN**: A = 77, `VPOS`, `VIN` → A = `11111111` (o que foi gravado); o
   cursor continua 77.
8. **Prioridade**: com `MEM_VID = 0` o endereço da VRAM é o da varredura;
   com `MEM_VID = 1` é o do cursor.
