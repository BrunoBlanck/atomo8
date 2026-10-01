# -*- coding: utf-8 -*-
"""
DADOS DO ESQUEMA: componentes, fios e caminhos das instrucoes.

So dados (nada de desenho). Coordenadas em "pixels do mundo"; a tela
aplica zoom e deslocamento. Manter em sincronia com hardware.py e
componentes/*.md (custos em portas, sinais, numeros dos arquivos).
"""

# ============================================================
# CATEGORIAS (cor de destaque de cada grupo)
# ============================================================

CATEGORIAS = {
    "controle":     ("Controle", "#4f8cff"),
    "registrador":  ("Registradores", "#2ed39a"),
    "memoria":      ("Memórias", "#ff9f43"),
    "ula":          ("ULA", "#b07cff"),
    "mux":          ("Multiplexadores", "#22c3d6"),
    "es":           ("Entrada e saída", "#ff5c8a"),
    "relogio":      ("Relógio", "#ffd166"),
}

# ============================================================
# COMPONENTES
#   x, y, l, a : retangulo no mundo
#   pai        : bloco que contem este (sub-blocos da ULA)
# ============================================================

def _c(id, nome, arquivo, cat, x, y, l, a, resumo, entradas=(), saidas=(),
       sinais=(), custo="", tempo="", instrucoes="", pai=None, subtitulo=""):
    return dict(id=id, nome=nome, arquivo=arquivo, cat=cat, x=x, y=y, l=l, a=a,
                resumo=resumo, entradas=list(entradas), saidas=list(saidas),
                sinais=list(sinais), custo=custo, tempo=tempo,
                instrucoes=instrucoes, pai=pai, subtitulo=subtitulo)


COMPONENTES = [
    # ------------------------------------------------ controle
    _c("relogio", "Relógio e reset", "20-relogio-e-reset.md", "relogio",
       40, 40, 170, 80,
       "Gera o CLOCK, o pulso que faz tudo andar. Na borda de subida (↑CLK) "
       "todos os registradores gravam juntos; na metade baixa acontecem os "
       "pulsos de escrita da RAM e da VRAM. Tem modo passo a passo (1 instrução "
       "por aperto) e o botão RESET, que zera o PC e o cursor da VRAM.",
       entradas=["oscilador", "chave MODO", "botão PASSO", "botão RESET"],
       saidas=["CLK → A, Z, C, PC, ponteiro, cursor, teclado",
               "CLK_BAIXO → pulsos de escrita", "/RST → PC e cursor"],
       custo="oscilador e debounce (peças analógicas: decisão pendente)",
       tempo="1 instrução = 1 × CLOCK",
       subtitulo="CLK · /RST"),

    _c("muxpc", "Mux do próximo PC", "13-multiplexador-proximo-pc.md", "mux",
       40, 190, 170, 80,
       "Escolhe o endereço da próxima instrução: PC + 1 (seguir em frente) "
       "ou o destino do salto, que vem da própria instrução.",
       entradas=["PC + 1 (11 bits)", "destino (11 bits, da ROM)"],
       saidas=["próximo PC (11 bits)"],
       sinais=["TOMA (da lógica de salto)"],
       custo="1 NOT + 22 AND + 11 OR",
       tempo="0 × CLOCK (combinacional)",
       instrucoes="todas (saltos escolhem o destino)",
       subtitulo="PC+1 ou destino"),

    _c("pc", "PC", "12-registrador-pc.md", "registrador",
       40, 330, 170, 80,
       "Contador de programa: guarda o endereço (11 bits) da instrução que "
       "está sendo executada. Grava o próximo PC em toda borda de subida.",
       entradas=["próximo PC (11 bits)", "CLK", "/RST"],
       saidas=["endereço da ROM (11 bits)"],
       custo="11 flip-flops D com clear",
       tempo="grava no ↑CLK",
       instrucoes="todas",
       subtitulo="11 bits"),

    _c("inc", "Incrementador +1", "11-incrementador-11-bits.md", "controle",
       40, 470, 170, 80,
       "Calcula PC + 1 com meio-somadores em cadeia. O mesmo circuito, "
       "com menos bits, é usado no ponteiro e no cursor (arquivo 21).",
       entradas=["PC (11 bits)"], saidas=["PC + 1 (11 bits)"],
       custo="10 XOR + 10 AND + 1 NOT",
       tempo="0 × CLOCK",
       subtitulo="PC + 1"),

    _c("rom", "ROM de programa", "15-rom-de-programa.md", "memoria",
       280, 300, 190, 150,
       "Guarda o programa: 2048 palavras de 16 bits. A CPU só lê e não "
       "consegue ler dados daqui (dado fixo entra por LDI). Cada palavra é "
       "dividida em OP (4 bits), F (4 bits) e N (8 bits); nos saltos os "
       "11 bits de baixo são o destino. Em portas: decodificador de "
       "endereço + matriz de diodos.",
       entradas=["endereço (11 bits, do PC)"],
       saidas=["OP + F → decodificador", "F → ULA (tabela / função)",
               "N → mux de endereço, mux B, mux de A",
               "destino → mux do próximo PC"],
       custo="decodificador de endereço em portas + diodos (memória: decisão pendente)",
       tempo="leitura dentro da metade alta do CLOCK",
       instrucoes="todas · doom usa 1596 de 2048 palavras",
       subtitulo="2048 × 16"),

    _c("dec", "Decodificador", "17-decodificador-de-instrucoes.md", "controle",
       560, 40, 210, 120,
       "A unidade de controle: transforma OP e F em todos os sinais que "
       "comandam o hardware (quem grava, de onde vêm os dados, o que a ULA "
       "faz). Só portas: decodificador 4→16 e um OR por sinal. Na ARIT e na "
       "LOG os bits de F vão direto para a ULA, sem decodificar.",
       entradas=["OP (4 bits)", "F (4 bits)"],
       saidas=["25 sinais de controle (A_WE, A_SRC, RAM_WE, END_SRC, "
               "B_IMED, SUB, USA_C, SHR, LOGICA, Z_WE, C_WE, saltos, "
               "TEC_RD, VID_WR, CUR_*, PTR_*, MEM_VID)"],
       custo="8 NOT + 29 AND + 16 OR = 53 portas",
       tempo="0 × CLOCK",
       instrucoes="todas",
       subtitulo="OP + F → sinais"),

    _c("salto", "Lógica de salto", "14-logica-de-salto.md", "controle",
       560, 215, 210, 80,
       "Decide se o salto acontece: TOMA = SALTO + SE_Z·Z + SE_NZ·/Z + "
       "SE_C·C + SE_NC·/C.",
       entradas=["SALTO, SE_Z, SE_NZ, SE_C, SE_NC (decodificador)",
                 "flags Z e C"],
       saidas=["TOMA → mux do próximo PC"],
       custo="2 NOT + 4 AND + 4 OR = 10 portas",
       tempo="0 × CLOCK",
       instrucoes="JMP, JZ, JNZ, JC, JNC",
       subtitulo="TOMA"),

    _c("flags", "Flags Z e C", "09-flags-z-e-c.md", "registrador",
       560, 310, 210, 80,
       "Guardam o resultado da última conta: Z = deu zero; C = vai-um "
       "(depois de SUB/CMP, C = 1 quer dizer A ≥ B, como no 6502). Só "
       "ARIT/ARITI mudam C; só ARIT, ARITI, LOG e LOGI mudam Z.",
       entradas=["Z e C novos (da ULA)", "Z_WE, C_WE", "CLK"],
       saidas=["Z, C → lógica de salto", "C → ULA (ADC/SBC)"],
       sinais=["Z_WE", "C_WE"],
       custo="2 flip-flops D + 8 portas",
       tempo="grava no ↑CLK",
       instrucoes="ADD, SUB, ADC, SBC, SHR, CMP, AND, OR, XOR, TST, NOT…",
       subtitulo="Z · C"),

    # ------------------------------------------------ caminho de dados
    _c("muxend", "Mux de endereço", "10-multiplexador-4x1-8-bits.md", "mux",
       840, 470, 160, 90,
       "Escolhe de onde vem o endereço da RAM: N (endereço fixo na "
       "instrução), A (leitura indireta, LDR) ou o ponteiro (LDP/STP).",
       entradas=["00: N", "01: A", "10: ponteiro"],
       saidas=["endereço da RAM (8 bits)"],
       sinais=["END_SRC1, END_SRC0"],
       custo="mux 4×1 de 8 bits = 62 portas",
       tempo="0 × CLOCK",
       instrucoes="LD, ST, LDR, LDP, STP, ARIT m, LOG m",
       subtitulo="da RAM: N · A · ponteiro"),

    _c("ptr", "Ponteiro da RAM", "21-registrador-ponteiro.md", "registrador",
       840, 625, 160, 80,
       "Registrador de 8 bits que guarda um endereço da RAM e soma 1 sozinho "
       "depois de cada acesso. É o que permite gravação indireta: filas, "
       "vetores e o labirinto compactado do doom. Mesmo componente do cursor.",
       entradas=["A (carga)", "PTR_LD", "PTR_INC", "CLK"],
       saidas=["endereço → mux de endereço da RAM"],
       sinais=["PTR_LD (PTR)", "PTR_INC (STP, LDP)"],
       custo="8 flip-flops + 66 portas",
       tempo="calcula em 0 × CLOCK, grava no ↑CLK",
       instrucoes="PTR, STP, LDP",
       subtitulo="8 bits · +1 sozinho"),

    _c("ram", "RAM", "16-ram.md", "memoria",
       1050, 440, 180, 150,
       "Memória de dados de 256 bytes: o labirinto (1 byte por célula) e as "
       "variáveis. Liga com lixo; o programa inicializa tudo o que usa. "
       "Grava sempre o valor de A (ST, STP).",
       entradas=["endereço (8 bits)", "dado = A", "RAM_WE + CLK_BAIXO"],
       saidas=["dado lido → mux B e mux de memória"],
       sinais=["RAM_WE"],
       custo="256 × 8 bits (memória: decisão pendente)",
       tempo="leitura 0 × CLOCK · escrita ½ × CLOCK",
       instrucoes="LD, ST, LDR, LDP, STP, ARIT m, LOG m",
       subtitulo="256 × 8"),

    _c("muxb", "Mux B", "05-multiplexador-2x1-8-bits.md", "mux",
       1310, 300, 140, 80,
       "Escolhe o segundo operando da ULA: o dado lido da RAM (ADD m, "
       "XOR m…) ou o número N da instrução (ADDI n, ANDI n…).",
       entradas=["0: RAM", "1: N"], saidas=["B → ULA"],
       sinais=["B_IMED"],
       custo="1 NOT + 16 AND + 8 OR = 25 portas",
       tempo="0 × CLOCK",
       instrucoes="ARIT, ARITI, LOG, LOGI",
       subtitulo="RAM ou N"),

    _c("ula", "ULA", "07-ula.md", "ula",
       1500, 150, 330, 410,
       "Faz as contas. Somador (ADD, SUB, ADC, SBC, CMP), unidade lógica "
       "programável (AND, OR, XOR, TST, NOT… a tabela-verdade vem em F) e "
       "SHR (só fios). Um mux escolhe o resultado; Z e C saem para as flags. "
       "Clique nas peças internas para ver cada uma.",
       entradas=["A", "B (do mux B)", "F (função ou tabela)", "C atual",
                 "SUB, USA_C, SHR, LOGICA"],
       saidas=["R → mux de A", "Z, C novos → flags"],
       sinais=["SUB", "USA_C", "SHR", "LOGICA"],
       custo="198 portas",
       tempo="0 × CLOCK · caminho mais longo ~32 portas em fila",
       instrucoes="ARIT, ARITI, LOG, LOGI",
       subtitulo="somador · lógica · SHR"),

    _c("inv", "Inversor de B", "03-inversor-controlado-8-bits.md", "ula",
       1520, 200, 140, 52,
       "8 XOR: com SUB = 1 inverte B, para subtrair (A + não B + 1).",
       entradas=["B", "SUB (bit 8 de F)"], saidas=["B' → somador"],
       custo="8 XOR", tempo="0 × CLOCK", pai="ula", subtitulo="B XOR SUB"),

    _c("cin", "Vai-um de entrada", "07-ula.md", "ula",
       1670, 200, 140, 52,
       "CIN = (USA_C AND C) OR (NOT USA_C AND SUB). ADD: 0 · SUB: 1 · "
       "ADC/SBC: a flag C.",
       entradas=["SUB", "USA_C (bit 9 de F)", "C"], saidas=["CIN → somador"],
       custo="1 NOT + 2 AND + 1 OR", tempo="0 × CLOCK", pai="ula",
       subtitulo="CIN"),

    _c("soma", "Somador 8 bits", "02-somador-8-bits.md", "ula",
       1520, 270, 290, 56,
       "8 somadores completos (arquivo 01) em cadeia: o vai-um passa de bit "
       "em bit. É o caminho mais longo do hardware. O vai-um final vira o C.",
       entradas=["A", "B'", "CIN"], saidas=["soma → mux de resultado",
                                          "vai-um final → C novo"],
       custo="40 portas (16 XOR + 16 AND + 8 OR)", tempo="0 × CLOCK",
       pai="ula", subtitulo="ADD · SUB · ADC · SBC"),

    _c("logica", "Unidade lógica", "04-unidade-logica.md", "ula",
       1520, 345, 140, 56,
       "8 muxes 4×1 montados ao contrário: An e Bn na seleção, a "
       "tabela-verdade (F) nos dados. Faz qualquer uma das 16 funções de 2 "
       "entradas: AND 1000, OR 1110, XOR 0110, TST 1100, NOT 0011. Ideia "
       "do Gigatron.",
       entradas=["A", "B", "tabela T = F"], saidas=["lógica → mux de resultado"],
       custo="72 portas (9 por bit)", tempo="0 × CLOCK", pai="ula",
       subtitulo="tabela-verdade"),

    _c("shr", "SHR", "07-ula.md", "ula",
       1670, 345, 140, 56,
       "Desloca A 1 bit para a direita: só fios (A7..A1 → R6..R0, R7 = 0). "
       "O bit que sai (A0) vira o C.",
       entradas=["A"], saidas=["A >> 1 → mux de resultado", "A0 → C novo"],
       custo="0 portas (só fios)", tempo="0 × CLOCK", pai="ula",
       subtitulo="A >> 1"),

    _c("muxr", "Mux de resultado", "10-multiplexador-4x1-8-bits.md", "ula",
       1520, 420, 290, 50,
       "Escolhe o resultado da ULA: 00 soma, 01 lógica, 10 SHR.",
       entradas=["soma", "lógica", "SHR"], saidas=["R"],
       sinais=["SHR", "LOGICA"],
       custo="62 portas", tempo="0 × CLOCK", pai="ula", subtitulo="R"),

    _c("zero", "Detector de zero", "06-detector-de-zero.md", "ula",
       1520, 488, 140, 50,
       "Z = NOR dos 8 bits de R (OR em árvore + NOT).",
       entradas=["R"], saidas=["Z novo → flags"],
       custo="7 OR + 1 NOT = 8 portas", tempo="0 × CLOCK", pai="ula",
       subtitulo="Z"),

    _c("cnovo", "C novo", "05-multiplexador-2x1-8-bits.md", "ula",
       1670, 488, 140, 50,
       "Mux 2×1 de 1 bit: com SHR o C novo é A0; senão, o vai-um final do "
       "somador.",
       entradas=["vai-um final", "A0", "SHR"], saidas=["C novo → flags"],
       custo="1 NOT + 2 AND + 1 OR", tempo="0 × CLOCK", pai="ula",
       subtitulo="C"),

    _c("muxmem", "Mux de memória", "05-multiplexador-2x1-8-bits.md", "mux",
       1310, 640, 140, 80,
       "Escolhe qual memória entrega o dado para A: RAM (LD, LDR, LDP) ou "
       "VRAM (VIN). Substitui o tri-state: só portas.",
       entradas=["0: RAM", "1: VRAM"], saidas=["MEMÓRIA → mux de A"],
       sinais=["MEM_VID"],
       custo="25 portas", tempo="0 × CLOCK",
       instrucoes="LD, LDR, LDP, VIN", subtitulo="RAM ou VRAM"),

    _c("muxa", "Mux de A", "10-multiplexador-4x1-8-bits.md", "mux",
       1500, 640, 160, 110,
       "Escolhe o valor novo de A: 00 N (LDI), 01 memória (LD, LDR, LDP, "
       "VIN), 10 resultado da ULA, 11 teclado (IN).",
       entradas=["00: N", "01: MEMÓRIA", "10: ULA", "11: teclado"],
       saidas=["valor novo → registrador A"],
       sinais=["A_SRC1, A_SRC0"],
       custo="62 portas", tempo="0 × CLOCK",
       instrucoes="LDI, LD, LDR, LDP, VIN, ARIT, LOG, IN",
       subtitulo="N · MEM · ULA · teclado"),

    _c("rega", "Registrador A", "08-registrador-a.md", "registrador",
       1710, 650, 140, 90,
       "O acumulador: único registrador de dados (8 bits). Entra na ULA, é "
       "o dado gravado na RAM e na VRAM e o valor carregado no ponteiro e "
       "no cursor.",
       entradas=["valor novo (mux de A)", "A_WE", "CLK"],
       saidas=["A → ULA, RAM, VRAM, mux de endereço, ponteiro, cursor"],
       sinais=["A_WE"],
       custo="8 flip-flops + 25 portas", tempo="grava no ↑CLK",
       instrucoes="quase todas", subtitulo="8 bits"),

    _c("cursor", "Cursor da VRAM", "21-registrador-ponteiro.md", "registrador",
       840, 800, 160, 80,
       "O mesmo registrador-ponteiro, com 7 bits: endereço da VRAM. VPOS "
       "carrega, VOUT grava e avança, VIN lê sem avançar. Depois de 127 volta "
       "a 0 sozinho (o doom escreve 128 VOUT por quadro sem VPOS). O RESET "
       "zera.",
       entradas=["A (carga)", "CUR_LD", "CUR_INC", "CLK", "/RST"],
       saidas=["endereço da VRAM (7 bits)"],
       sinais=["CUR_LD (VPOS)", "CUR_INC (VOUT)"],
       custo="7 flip-flops com clear + 58 portas",
       tempo="calcula em 0 × CLOCK, grava no ↑CLK",
       instrucoes="VPOS, VOUT, VIN", subtitulo="7 bits · 0..127"),

    _c("vram", "VRAM + display", "18-display.md", "es",
       1050, 780, 180, 175,
       "A imagem: 128 bytes (32 colunas × 4 páginas, bytes em pé, bit 0 = "
       "pixel de cima), separada da RAM. A CPU lê e grava pelo cursor; a "
       "varredura acende o painel 32×32 sozinha. Desenhar com XOR e ler o "
       "pixel = colisão, como no CHIP-8.",
       entradas=["endereço = cursor", "dado = A", "VID_WR + CLK_BAIXO"],
       saidas=["dado lido → mux de memória", "painel 32 × 32"],
       sinais=["VID_WR", "MEM_VID (CPU tem prioridade no endereço)"],
       custo="128 × 8 bits + varredura (memória: decisão pendente)",
       tempo="VOUT/VIN: 1 × CLOCK", instrucoes="VOUT, VIN",
       subtitulo="128 × 8 · 32×32"),

    _c("teclado", "Teclado", "19-teclado.md", "es",
       1310, 820, 140, 80,
       "5 botões (frente, trás, gira esq., gira dir., mapa), cada um com "
       "trava de evento: vira 1 no aperto e volta a 0 quando a CPU lê. Sem "
       "aperto pendente, IN devolve 0 (não espera).",
       entradas=["5 botões", "TEC_RD", "CLK"], saidas=["byte → mux de A"],
       sinais=["TEC_RD"],
       custo="15 flip-flops + 6 NOT + 10 AND + 5 OR",
       tempo="aperto → evento: 2 × CLOCK", instrucoes="IN",
       subtitulo="5 botões"),
]

POR_ID = {c["id"]: c for c in COMPONENTES}

# ============================================================
# FIOS (barramentos)
#   id, de, para, largura (bits), rotulo, pontos (caminho no mundo)
# ============================================================

FIOS = [
    # ---- controle
    ("pc_rom",    "pc", "rom", 11, "endereço", [(210, 370), (245, 370), (245, 340), (280, 340)]),
    ("pc_inc",    "pc", "inc", 11, "PC", [(125, 410), (125, 470)]),
    ("inc_muxpc", "inc", "muxpc", 11, "PC+1", [(40, 510), (20, 510), (20, 230), (40, 230)]),
    ("muxpc_pc",  "muxpc", "pc", 11, "", [(125, 270), (125, 330)]),
    ("rom_dest",  "rom", "muxpc", 11, "destino", [(330, 300), (330, 245), (210, 245)]),
    ("salto_pc",  "salto", "muxpc", 1, "TOMA", [(560, 255), (490, 255), (490, 205), (210, 205)]),
    ("rom_dec",   "rom", "dec", 8, "OP + F", [(420, 300), (420, 100), (560, 100)]),
    ("rom_f",     "rom", "ula", 4, "F", [(450, 300), (450, 18), (1740, 18), (1740, 150)]),
    ("dec_salto", "dec", "salto", 5, "SE_*", [(665, 160), (665, 215)]),
    ("flags_salto", "flags", "salto", 2, "Z, C", [(665, 310), (665, 295)]),
    ("ula_flags", "ula", "flags", 2, "Z, C novos", [(1560, 150), (1560, 122), (800, 122), (800, 370), (770, 370)]),
    ("flags_ula", "flags", "ula", 1, "C", [(770, 335), (785, 335), (785, 136), (1580, 136), (1580, 150)]),
    # ---- N
    ("rom_n_end", "rom", "muxend", 8, "N", [(470, 410), (820, 410), (820, 490), (840, 490)]),
    ("rom_n_b",   "rom", "muxb", 8, "N", [(470, 410), (1280, 410), (1280, 330), (1310, 330)]),
    ("rom_n_a",   "rom", "muxa", 8, "N", [(470, 410), (1470, 410), (1470, 665), (1500, 665)]),
    # ---- RAM
    ("ptr_end",   "ptr", "muxend", 8, "ponteiro", [(920, 625), (920, 560)]),
    ("end_ram",   "muxend", "ram", 8, "endereço", [(1000, 515), (1050, 515)]),
    ("ram_b",     "ram", "muxb", 8, "dado", [(1230, 470), (1295, 470), (1295, 355), (1310, 355)]),
    ("ram_mem",   "ram", "muxmem", 8, "dado", [(1230, 500), (1295, 500), (1295, 665), (1310, 665)]),
    ("b_ula",     "muxb", "ula", 8, "B", [(1450, 340), (1485, 340), (1485, 226), (1520, 226)]),
    # ---- resultado
    ("ula_a",     "ula", "muxa", 8, "R", [(1580, 560), (1580, 640)]),
    ("mem_a",     "muxmem", "muxa", 8, "MEM", [(1450, 690), (1500, 690)]),
    ("tec_a",     "teclado", "muxa", 8, "teclas", [(1450, 860), (1485, 860), (1485, 725), (1500, 725)]),
    ("muxa_rega", "muxa", "rega", 8, "", [(1660, 695), (1710, 695)]),
    # ---- vídeo
    ("cur_vram",  "cursor", "vram", 7, "endereço", [(1000, 840), (1050, 840)]),
    ("vram_mem",  "vram", "muxmem", 8, "dado", [(1230, 820), (1280, 820), (1280, 700), (1310, 700)]),
    # ---- barramento A (sai do registrador A)
    ("a_ula",     "rega", "ula", 8, "A", [(1800, 650), (1800, 560)]),
    ("a_ram",     "rega", "ram", 8, "A", [(1780, 740), (1780, 1010), (1260, 1010), (1260, 570), (1230, 570)]),
    ("a_vram",    "rega", "vram", 8, "A", [(1780, 740), (1780, 1010), (1140, 1010), (1140, 955)]),
    ("a_cursor",  "rega", "cursor", 8, "A", [(1780, 740), (1780, 1010), (805, 1010), (805, 860), (840, 860)]),
    ("a_ptr",     "rega", "ptr", 8, "A", [(1780, 740), (1780, 1010), (805, 1010), (805, 680), (840, 680)]),
    ("a_end",     "rega", "muxend", 8, "A", [(1780, 740), (1780, 1010), (805, 1010), (805, 535), (840, 535)]),
    # ---- dentro da ULA
    ("inv_soma",    "inv", "soma", 8, "", [(1590, 252), (1590, 270)]),
    ("cin_soma",    "cin", "soma", 1, "", [(1740, 252), (1740, 270)]),
    ("soma_muxr",   "soma", "muxr", 8, "", [(1520, 300), (1508, 300), (1508, 445), (1520, 445)]),
    ("logica_muxr", "logica", "muxr", 8, "", [(1590, 401), (1590, 420)]),
    ("shr_muxr",    "shr", "muxr", 8, "", [(1740, 401), (1740, 420)]),
    ("muxr_zero",   "muxr", "zero", 8, "", [(1590, 470), (1590, 488)]),
    ("soma_cnovo",  "soma", "cnovo", 1, "", [(1810, 300), (1822, 300), (1822, 513), (1810, 513)]),
]

# ============================================================
# CAMINHO DE CADA INSTRUCAO (fios e componentes que trabalham)
# ============================================================

_BUSCA = ["pc_rom", "rom_dec", "pc_inc", "inc_muxpc", "muxpc_pc"]
_BUSCA_C = ["pc", "rom", "dec", "inc", "muxpc", "relogio"]

def _cam(descricao, fios, comps):
    return dict(descricao=descricao, fios=_BUSCA + fios, comps=_BUSCA_C + comps)


CAMINHOS = {
    "LDI":  _cam("A = n. O número vem da própria instrução.",
                 ["rom_n_a", "muxa_rega"], ["muxa", "rega"]),
    "LD":   _cam("A = RAM[m]. N é o endereço.",
                 ["rom_n_end", "end_ram", "ram_mem", "mem_a", "muxa_rega"],
                 ["muxend", "ram", "muxmem", "muxa", "rega"]),
    "ST":   _cam("RAM[m] = A.",
                 ["rom_n_end", "end_ram", "a_ram"], ["muxend", "ram", "rega"]),
    "LDR":  _cam("A = RAM[A]: o próprio A é o endereço (leitura indireta).",
                 ["a_end", "end_ram", "ram_mem", "mem_a", "muxa_rega"],
                 ["muxend", "ram", "muxmem", "muxa", "rega"]),
    "ADD":  _cam("A = A + RAM[m]; muda Z e C.",
                 ["rom_n_end", "end_ram", "ram_b", "b_ula", "a_ula", "ula_a",
                  "muxa_rega", "ula_flags"],
                 ["muxend", "ram", "muxb", "ula", "inv", "cin", "soma", "muxr",
                  "zero", "cnovo", "muxa", "rega", "flags"]),
    "ADDI": _cam("A = A + n; muda Z e C.",
                 ["rom_n_b", "b_ula", "a_ula", "ula_a", "muxa_rega", "ula_flags"],
                 ["muxb", "ula", "inv", "cin", "soma", "muxr", "zero", "cnovo",
                  "muxa", "rega", "flags"]),
    "SUBI": _cam("A = A − n (B invertido, vai-um = 1); C = 1 se A ≥ n.",
                 ["rom_n_b", "b_ula", "a_ula", "ula_a", "muxa_rega", "ula_flags"],
                 ["muxb", "ula", "inv", "cin", "soma", "muxr", "zero", "cnovo",
                  "muxa", "rega", "flags"]),
    "ADC":  _cam("A = A + RAM[m] + C (contas de 16 bits).",
                 ["rom_n_end", "end_ram", "ram_b", "b_ula", "a_ula", "flags_ula",
                  "ula_a", "muxa_rega", "ula_flags"],
                 ["muxend", "ram", "muxb", "ula", "inv", "cin", "soma", "muxr",
                  "zero", "cnovo", "muxa", "rega", "flags"]),
    "CMPI": _cam("Calcula A − n só para as flags (A não muda). C = 1 se A ≥ n.",
                 ["rom_n_b", "b_ula", "a_ula", "ula_flags"],
                 ["muxb", "ula", "inv", "cin", "soma", "muxr", "zero", "cnovo", "flags"]),
    "SHR":  _cam("A = A >> 1; o bit que sai vai para C.",
                 ["a_ula", "ula_a", "muxa_rega", "ula_flags"],
                 ["ula", "shr", "muxr", "zero", "cnovo", "muxa", "rega", "flags"]),
    "ANDI": _cam("A = A AND n bit a bit (tabela 1000 em F); muda Z.",
                 ["rom_n_b", "b_ula", "a_ula", "rom_f", "ula_a", "muxa_rega",
                  "ula_flags"],
                 ["muxb", "ula", "logica", "muxr", "zero", "muxa", "rega", "flags"]),
    "XOR":  _cam("A = A XOR RAM[m] (tabela 0110). Inverte pixels.",
                 ["rom_n_end", "end_ram", "ram_b", "b_ula", "a_ula", "rom_f",
                  "ula_a", "muxa_rega", "ula_flags"],
                 ["muxend", "ram", "muxb", "ula", "logica", "muxr", "zero", "muxa",
                  "rega", "flags"]),
    "TST":  _cam("Passa A pela unidade lógica (tabela 1100): Z = (A == 0).",
                 ["a_ula", "rom_f", "ula_a", "muxa_rega", "ula_flags"],
                 ["ula", "logica", "muxr", "zero", "muxa", "rega", "flags"]),
    "JMP":  _cam("PC = destino.", ["rom_dest", "dec_salto", "salto_pc"],
                 ["salto"]),
    "JZ":   _cam("Se Z = 1: PC = destino.",
                 ["rom_dest", "dec_salto", "flags_salto", "salto_pc"],
                 ["salto", "flags"]),
    "JNC":  _cam("Se C = 0 (A < B depois de CMP): PC = destino.",
                 ["rom_dest", "dec_salto", "flags_salto", "salto_pc"],
                 ["salto", "flags"]),
    "IN":   _cam("A = eventos do teclado (0 se nada foi apertado).",
                 ["tec_a", "muxa_rega"], ["teclado", "muxa", "rega"]),
    "VOUT": _cam("VRAM[cursor] = A e o cursor avança.",
                 ["cur_vram", "a_vram"], ["cursor", "vram", "rega"]),
    "VIN":  _cam("A = VRAM[cursor] (o cursor não anda).",
                 ["cur_vram", "vram_mem", "mem_a", "muxa_rega"],
                 ["cursor", "vram", "muxmem", "muxa", "rega"]),
    "VPOS": _cam("cursor = A.", ["a_cursor"], ["cursor", "rega"]),
    "PTR":  _cam("ponteiro = A.", ["a_ptr"], ["ptr", "rega"]),
    "STP":  _cam("RAM[ponteiro] = A e o ponteiro avança.",
                 ["ptr_end", "end_ram", "a_ram"], ["ptr", "muxend", "ram", "rega"]),
    "LDP":  _cam("A = RAM[ponteiro] e o ponteiro avança.",
                 ["ptr_end", "end_ram", "ram_mem", "mem_a", "muxa_rega"],
                 ["ptr", "muxend", "ram", "muxmem", "muxa", "rega"]),
}

# fios internos da ULA entram sozinhos conforme as pecas usadas
_INTERNOS = {"soma": ["inv_soma", "cin_soma", "soma_muxr", "soma_cnovo"],
             "logica": ["logica_muxr"], "shr": ["shr_muxr"], "zero": ["muxr_zero"]}
for _c_ in CAMINHOS.values():
    for _peca, _fios in _INTERNOS.items():
        if _peca in _c_["comps"]:
            _c_["fios"] += _fios
