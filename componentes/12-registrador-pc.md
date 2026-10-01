# 12 · Registrador PC (contador de programa, 11 bits)

Guarda o endereço da instrução que está sendo executada. Grava **em toda
borda de subida** o valor que o mux do próximo PC (arquivo 13) escolher.

11 bits porque o programa tem mais de 1024 instruções (ROM de 2048).

## Pinos

| Pino      | Direção | Largura | Descrição                            |
|-----------|---------|---------|--------------------------------------|
| `D[10:0]` | entrada | 11      | próximo PC (arquivo 13)              |
| `CLK`     | entrada | 1       | relógio                              |
| `/RST`    | entrada | 1       | 0 = zera imediatamente               |
| `Q[10:0]` | saída   | 11      | endereço atual → ROM e incrementador |

## Circuito

11 flip-flops D com **clear assíncrono** (`/CLR`), com todos os
`/CLR` ligados em `/RST`. Não precisa de enable nem de mux de realimentação:
o PC grava em todo pulso.

Portas: 11 flip-flops D com clear, nenhuma porta a mais.

## Testes

| Passo | D           | /RST | Ação | Q                                        |
|-------|-------------|------|------|------------------------------------------|
| 1     | qualquer    | 0    | —    | 00000000000                              |
| 2     | 00000000101 | 1    | ↑CLK | 00000000101                              |
| 3     | 11111111111 | 1    | ↑CLK | 11111111111                              |
| 4     | 11111111111 | 0    | —    | 00000000000 (reset não espera o relógio) |
| 5     | 10000000000 | 1    | ↑CLK | 10000000000                              |

## Tempo

- **Avança a cada 1 × CLOCK** (uma instrução por pulso).
- **Reset: 0 × CLOCK**. É assíncrono, zera na hora sem esperar o relógio.
