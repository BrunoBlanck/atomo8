# -*- coding: utf-8 -*-
"""
GERADOR DO INICIO DO PROGRAMA (labirinto -> assembly)

Script avulso: NAO tem nenhuma ligacao com doom.py nem com hardware.py.
Desenhe o labirinto na matriz MAPA abaixo, rode:

    python gerar_mapa.py

e cole o texto impresso no doom.py, logo abaixo de "INICIO:", no lugar do
bloco que grava o labirinto (do comentario "labirinto compactado" ate o
"JNZ  DESCOMPACTA", antes de "LDI  14").

Como o bloco e gerado:
    1) 1 bit por celula (1 = parede), 8 celulas por byte: 169 celulas
       = 22 bytes. Cada byte entra com LDI + ST (a CPU nao le dados da
       ROM, entao dado fixo so entra por LDI).
    2) Um laco desenrola: LDR pega o byte, SHR joga o bit da celula na
       flag C e STP grava 255 (parede) ou 0 (livre) e avanca o ponteiro.
Sao 69 instrucoes na ROM (antes: 169 ST + 2 LDI = 171).

Regras que o doom.py exige (o script confere todas antes de gerar):
    - 13 linhas x 13 colunas, so '#' (parede) e '.' (livre);
    - borda toda de parede, menos a SAIDA em (12, 11);
    - INICIO em (1, 1) livre (o jogador comeca ali olhando para o sul);
    - nenhuma linha reta (horizontal ou vertical) com mais de 3 livres
      seguidas: e isso que garante a parede da frente a no maximo 3 celulas;
    - a saida precisa ser alcancavel a partir do inicio.
"""

import sys
from collections import deque

# ============================================================
# DESENHE O LABIRINTO AQUI  (# = parede, . = livre)
#            coluna x: 0123456789012
# ============================================================
MAPA = [
    "#############",   # y = 0
    "#.#...#...#.#",   # y = 1   inicio em x = 1
    "#...#...#...#",   # y = 2
    "#.#..#.#.#.##",   # y = 3
    "######.#.#..#",   # y = 4
    "###...#...#.#",   # y = 5
    "#...#...#...#",   # y = 6
    "#.#.#.##..###",   # y = 7
    "#..###..##..#",   # y = 8
    "##..#..#...##",   # y = 9
    "#.#...#..#..#",   # y = 10
    "#...#...###..",   # y = 11  saida em x = 12
    "#############",   # y = 12
]

N = 13
INICIO = (1, 1)
SAIDA = (12, 11)
MAX_SEGUIDAS = 3


def conferir(mapa):
    erros = []
    if len(mapa) != N:
        erros.append("o mapa tem {} linhas (precisa de {})".format(len(mapa), N))
    for y, linha in enumerate(mapa):
        if len(linha) != N:
            erros.append("linha {} tem {} colunas (precisa de {})".format(y, len(linha), N))
        for x, c in enumerate(linha):
            if c not in "#.":
                erros.append("linha {} coluna {}: caractere '{}' (use # ou .)".format(y, x, c))
    if erros:
        return erros            # sem tamanho certo nao da para conferir o resto

    livre = lambda x, y: mapa[y][x] == "."
    for y in range(N):
        for x in range(N):
            borda = x in (0, N - 1) or y in (0, N - 1)
            if borda and livre(x, y) and (x, y) != SAIDA:
                erros.append("borda livre em ({}, {}): so a saida {} pode".format(x, y, SAIDA))
    if not livre(*INICIO):
        erros.append("o inicio {} precisa estar livre".format(INICIO))
    if not livre(*SAIDA):
        erros.append("a saida {} precisa estar livre".format(SAIDA))

    # nenhuma sequencia reta com mais de 3 livres
    for y in range(N):
        seguidas = 0
        for x in range(N):
            seguidas = seguidas + 1 if livre(x, y) else 0
            if seguidas == MAX_SEGUIDAS + 1:
                erros.append("linha {}: mais de {} livres seguidas terminando em x = {}".format(y, MAX_SEGUIDAS, x))
    for x in range(N):
        seguidas = 0
        for y in range(N):
            seguidas = seguidas + 1 if livre(x, y) else 0
            if seguidas == MAX_SEGUIDAS + 1:
                erros.append("coluna {}: mais de {} livres seguidas terminando em y = {}".format(x, MAX_SEGUIDAS, y))

    # a saida e alcancavel?
    visto = {INICIO}
    fila = deque([INICIO])
    while fila:
        x, y = fila.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < N and 0 <= ny < N and livre(nx, ny) and (nx, ny) not in visto:
                visto.add((nx, ny))
                fila.append((nx, ny))
    if livre(*SAIDA) and SAIDA not in visto:
        erros.append("a saida {} nao e alcancavel a partir do inicio {}".format(SAIDA, INICIO))
    return erros


def gerar(mapa):
    """Labirinto compactado: 1 bit por celula (1 = parede), 8 celulas por
    byte. Bit k do byte j = celula 8*j + k. Os 22 bytes vao para a RAM
    (0xC0..0xD5) e um laco com SHR + STP os desenrola nas 169 celulas."""
    bits = [1 if mapa[c // N][c % N] == "#" else 0 for c in range(N * N)]
    bits += [0] * (-len(bits) % 8)                  # completa o ultimo byte
    linhas = ["    ; labirinto compactado: bit k do byte j = celula 8*j + k (1 = parede)"]
    for j in range(len(bits) // 8):
        v = sum(bits[8 * j + k] << k for k in range(8))
        linhas.append("    LDI  0b{:08b}   ; celulas {:3d}..{:3d}".format(v, 8 * j + 7, 8 * j))
        linhas.append("    ST   0x{:02X}".format(0xC0 + j))
    fim = 0xC0 + len(bits) // 8
    linhas += [
        "    ; desenrola: cada bit vira 1 byte (parede = 255, livre = 0)",
        "    LDI  0",
        "    PTR              ; ponteiro = celula 0",
        "    LDI  0xC0",
        "    ST   MSRC",
        "DESCOMPACTA:",
        "    LD   MSRC",
        "    LDR              ; A = byte compactado",
        "    ST   MBYTE",
        "    LDI  8",
        "    ST   MCNT",
        "DESC_BIT:",
        "    LD   MBYTE",
        "    SHR              ; C = bit da celula",
        "    ST   MBYTE",
        "    LDI  0           ; livre (LDI e ST nao mudam C)",
        "    JNC  DESC_GRAVA",
        "    LDI  255         ; parede",
        "DESC_GRAVA:",
        "    STP              ; RAM[ponteiro] = A, ponteiro + 1",
        "    LD   MCNT",
        "    SUBI 1",
        "    ST   MCNT",
        "    JNZ  DESC_BIT",
        "    LD   MSRC",
        "    ADDI 1",
        "    ST   MSRC",
        "    CMPI 0x{:02X}".format(fim),
        "    JNZ  DESCOMPACTA",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    erros = conferir(MAPA)
    if erros:
        print("O mapa nao pode ser usado:")
        for e in erros:
            print("  -", e)
        sys.exit(1)
    bloco = gerar(MAPA)
    print(bloco)
    instrucoes = sum(1 for l in bloco.splitlines()
                     if not l.strip().startswith(";") and not l.endswith(":"))
    print("\n; {} instrucoes na ROM (antes: 169 ST + 2 LDI = 171)".format(instrucoes),
          file=sys.stderr)
