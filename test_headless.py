# -*- coding: utf-8 -*-
"""Testes automáticos (sem janela): valida o banco de questões, os mapas e o fluxo do jogo.

Executar:  python test_headless.py
"""
import math
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from questoes import BANCO_QUESTOES

C = math.comb
P = math.perm
F = math.factorial

# Valores esperados calculados independentemente (id -> resposta)
ESPERADO = {
    "F1-01": 3 * 4 * 2, "F1-02": 10 ** 3, "F1-03": 4 ** 4, "F1-04": 5 * 3 * 2, "F1-05": 10 * 9 * 8,
    "F1-06": 9 * 1000, "F1-07": 900, "F1-08": 6 * 4 * 3, "F1-09": 25 * 100, "F1-10": 2 ** 5,
    "F2-01": F(5), "F2-02": F(6) // F(2), "F2-03": F(7), "F2-04": F(7) // (F(2) * F(2)), "F2-05": F(6),
    "F2-06": F(8) // (F(3) * F(3) * F(2)), "F2-07": F(7) // F(2), "F2-08": F(9),
    "F2-09": F(6) // (F(2) * F(3)), "F2-10": F(7) // (F(3) * F(2) * F(2)),
    "F3-01": P(8, 3), "F3-02": P(10, 4), "F3-03": P(6, 2), "F3-04": P(7, 3), "F3-05": P(9, 5),
    "F3-06": P(10, 3), "F3-07": P(6, 3), "F3-08": P(12, 2), "F3-09": P(7, 4), "F3-10": P(20, 3),
    "F4-01": C(8, 3), "F4-02": C(10, 4), "F4-03": C(12, 2), "F4-04": C(7, 5), "F4-05": C(9, 2),
    "F4-06": C(15, 3), "F4-07": C(6, 3), "F4-08": C(9, 4), "F4-09": C(8, 2), "F4-10": C(5, 2) * C(6, 2),
    "F5-01": F(4) * 2, "F5-02": F(5) - F(4) * 2,
    "F5-03": sum(1 for n in range(1000, 10000) if len(set(str(n))) == 4 and n % 2 == 0),
    "F5-04": C(10, 4) - C(6, 4), "F5-05": 2 * F(5), "F5-06": F(5) * F(3), "F5-07": C(6, 3) - C(4, 1),
    "F5-08": P(5, 3) * P(10, 2), "F5-09": C(7, 3) * C(4, 2),
    "F5-10": sum(1 for n in range(501, 1000) if len(set(str(n))) == 3),
}


def testar_banco():
    ids = set()
    for fase, qs in BANCO_QUESTOES.items():
        assert len(qs) == 10, f"fase {fase} deve ter 10 questões"
        for q in qs:
            assert set(q) >= {"id", "enunciado", "resposta", "resolucao"}
            assert q["id"] not in ids
            ids.add(q["id"])
            assert q["resposta"].isdigit()
            assert int(q["resposta"]) == ESPERADO[q["id"]], (q["id"], q["resposta"], ESPERADO[q["id"]])
    assert len(ids) == 50 and set(ESPERADO) == ids
    print("OK banco: 50 questões, respostas conferidas por cálculo independente")


def testar_mapas():
    for idx in range(5):
        fase = main.Fase(idx)
        T = main.TILE
        livre = [[True] * main.COLS for _ in range(main.ROWS)]
        for r in range(main.ROWS):
            for c in range(main.COLS):
                tile = pygame.Rect(c * T, r * T, T, T)
                if any(tile.colliderect(s) for s in fase.solidos):
                    livre[r][c] = False
        sc, sr = fase.inicio[0] // T, fase.inicio[1] // T
        assert livre[sr][sc], f"início bloqueado na fase {idx + 1}"
        visto = {(sc, sr)}
        fila = deque([(sc, sr)])
        while fila:
            c, r = fila.popleft()
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c + dc, r + dr)
                if 0 <= n[0] < main.COLS and 0 <= n[1] < main.ROWS and n not in visto and livre[n[1]][n[0]]:
                    visto.add(n)
                    fila.append(n)
        for t in fase.terminais:
            acessivel = any((c, r) in visto
                            for c in range(t.rect.x // T - 1, t.rect.right // T + 1)
                            for r in range(t.rect.y // T - 1, t.rect.bottom // T + 1))
            assert acessivel, f"terminal inacessível: {t.nome}"
        pl = fase.cfg["porta"]
        assert (main.COLS - 2, pl) in visto or (main.COLS - 2, pl + 1) in visto, f"porta inacessível fase {idx + 1}"
        assert len(fase.terminais) == main.FASES[idx]["meta"]
    assert sum(f["meta"] for f in main.FASES) == main.TOTAL_ACERTOS
    print("OK mapas: início livre, terminais e porta alcançáveis, metas somam 12")


def testar_notas():
    av = main.avaliar_expressao
    assert av("8!/(3!*5!)") == "56"
    assert av("10*9*8") == "720"
    assert av("2^5") == "32"
    assert av("5!x2") == "240"
    assert av("1/0") is None and av("abc") is None and av("70!") is None
    print("OK bloco de notas: calculadora segura")


def passos(jogo, n, dt=1 / 60):
    for _ in range(n):
        jogo.atualizar(dt)
        jogo.desenhar()


def tecla(jogo, k, ch=""):
    jogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch, mod=0))


def digitar(jogo, txt):
    for ch in txt:
        tecla(jogo, getattr(pygame, "K_" + ch), ch)


def clique(jogo, pos):
    jogo.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1, touch=False))
    jogo.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1, touch=False))


def dedo(jogo, tipo, fid, pos):
    jogo.tratar_evento(pygame.event.Event(tipo, finger_id=fid, touch_id=0,
                                          x=pos[0] / jogo.larg_tela, y=pos[1] / main.ALTURA, dx=0, dy=0))


def resposta_certa(jogo):
    return jogo.desafio.questao["resposta"]


def testar_fluxo(salvar_dir=None):
    jogo = main.Jogo()
    jogo.estado = main.MENU
    passos(jogo, 3)
    salvar(jogo, salvar_dir, "1_menu")
    tecla(jogo, pygame.K_RETURN)
    assert jogo.estado == main.INTRO
    passos(jogo, 120)
    salvar(jogo, salvar_dir, "2_intro")
    passos(jogo, int(main.Jogo.INTRO_TOTAL * 60))
    assert jogo.estado == main.JOGANDO
    vistas = set()
    erros_esperados = 0
    for idx in range(5):
        fase = jogo.fase
        assert jogo.fase_idx == idx
        # força o jogador perto de cada terminal e responde
        primeiro = True
        for t in fase.terminais:
            jogo.jogador.rect.midbottom = (t.rect.centerx, t.rect.bottom + 22)
            jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
            passos(jogo, 2)
            if idx == 0:
                salvar(jogo, salvar_dir, "3_jogo")
            tecla(jogo, pygame.K_e)
            assert jogo.desafio, "terminal não abriu"
            if primeiro and idx in (1, 4):
                # erra de propósito: deve sortear outra questão inédita
                antiga = jogo.desafio.questao["id"]
                vistas.add(antiga)
                digitar(jogo, "1")
                tecla(jogo, pygame.K_RETURN)
                assert not jogo.desafio.acertou
                passos(jogo, 3)
                salvar(jogo, salvar_dir, f"4_erro_f{idx + 1}")
                tecla(jogo, pygame.K_RETURN)
                assert jogo.desafio.questao["id"] != antiga and jogo.desafio.estado == "pergunta"
                erros_esperados += 1
            primeiro = False
            q = jogo.desafio.questao
            assert q["id"] not in vistas, "questão repetida na fase"
            vistas.add(q["id"])
            if idx == 0:
                passos(jogo, 2)
                salvar(jogo, salvar_dir, "5_desafio")
            digitar(jogo, q["resposta"])
            tecla(jogo, pygame.K_RETURN)
            assert jogo.desafio.acertou
            if idx == 0:
                passos(jogo, 2)
                salvar(jogo, salvar_dir, "6_acerto")
            tecla(jogo, pygame.K_RETURN)
            assert jogo.desafio is None
        vistas.clear()
        assert fase.porta.aberta and fase.acertos == fase.meta
        passos(jogo, 90)
        if idx == 0:
            salvar(jogo, salvar_dir, "7_porta_aberta")
        # caminha até a porta
        jogo.jogador.rect.center = (main.LARGURA - 60, fase.porta.rect.centery)
        jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
        for _ in range(120):
            jogo.jogador.rect.x += 3
            jogo.jogador.px = jogo.jogador.rect.centerx
            jogo.atualizar(1 / 60)
            if jogo.estado != main.JOGANDO:
                break
        if idx < 4:
            assert jogo.estado == main.INTRO, f"não avançou da fase {idx + 1}"
            passos(jogo, int(main.Jogo.INTRO_TOTAL * 60) + 5)
            assert jogo.estado == main.JOGANDO
    assert jogo.estado == main.ESCOLHA_FINAL
    assert jogo.acertos_total == 12 and jogo.erros == erros_esperados
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "8_escolha")
    tecla(jogo, pygame.K_2, "2")
    assert jogo.estado == main.VITORIA
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "9_vitoria")
    # reinício
    tecla(jogo, pygame.K_RETURN)
    assert jogo.estado == main.INTRO and jogo.acertos_total == 0 and jogo.erros == 0
    passos(jogo, int(main.Jogo.INTRO_TOTAL * 60) + 5)
    # derrota por erros
    jogo.fase.terminais[0].questao = None
    jogo.jogador.rect.midbottom = (jogo.fase.terminais[0].rect.centerx, jogo.fase.terminais[0].rect.bottom + 22)
    jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
    tecla(jogo, pygame.K_e)
    for _ in range(main.MAX_ERROS):
        digitar(jogo, "1")
        tecla(jogo, pygame.K_RETURN)
        passos(jogo, 2)
        tecla(jogo, pygame.K_RETURN)
    assert jogo.estado == main.DERROTA, jogo.estado
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "10_derrota")
    tecla(jogo, pygame.K_r, "r")
    passos(jogo, int(main.Jogo.INTRO_TOTAL * 60) + 5)
    assert jogo.estado == main.JOGANDO
    # derrota por tempo
    jogo.tempo = 0.01
    passos(jogo, 3)
    assert jogo.estado == main.DERROTA
    # bloco de notas
    tecla(jogo, pygame.K_r, "r")
    passos(jogo, int(main.Jogo.INTRO_TOTAL * 60) + 5)
    tecla(jogo, pygame.K_n, "n")
    assert jogo.notas.aberto
    for ch in "8!/(3!*5!)":
        jogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=0, unicode=ch, mod=0))
    tecla(jogo, pygame.K_RETURN)
    assert jogo.notas.linhas[-2][0] == "= 56"
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "11_notas")
    tecla(jogo, pygame.K_n, "n")
    assert not jogo.notas.aberto
    # pausa congela o cronômetro
    tecla(jogo, pygame.K_ESCAPE)
    assert jogo.pausado
    antes = jogo.tempo
    passos(jogo, 60)
    assert jogo.tempo == antes
    salvar(jogo, salvar_dir, "12_pausa")
    tecla(jogo, pygame.K_p, "p")
    assert not jogo.pausado
    # mute pela tecla M e pelo botão do HUD
    tecla(jogo, pygame.K_m, "m")
    assert jogo.som.mudo
    clique(jogo, jogo.r_som.center)
    assert not jogo.som.mudo
    # botão de pausa no HUD
    clique(jogo, jogo.r_pausa.center)
    assert jogo.pausado
    clique(jogo, jogo.btn_continuar.rect.center)
    assert not jogo.pausado
    # toque: joystick move o jogador; botão E abre o terminal; teclado virtual responde
    t0 = jogo.fase.terminais[0]
    t0.feita = False
    jogo.jogador.rect.center = jogo.fase.inicio
    jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
    x0 = jogo.jogador.rect.centerx
    base = jogo.toque.base
    dedo(jogo, pygame.FINGERDOWN, 1, base)
    assert jogo.toque.ativo
    dedo(jogo, pygame.FINGERMOTION, 1, (base[0] + 70, base[1]))
    passos(jogo, 30)
    assert jogo.jogador.rect.centerx > x0 + 40, "joystick não moveu o jogador"
    salvar(jogo, salvar_dir, "13_toque")
    dedo(jogo, pygame.FINGERUP, 1, base)
    assert jogo.toque.vetor == (0.0, 0.0)
    jogo.jogador.rect.midbottom = (t0.rect.centerx, t0.rect.bottom + 22)
    jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
    dedo(jogo, pygame.FINGERDOWN, 2, jogo.toque.btn_e[0])
    dedo(jogo, pygame.FINGERUP, 2, jogo.toque.btn_e[0])
    assert jogo.desafio, "botão E (toque) não abriu o terminal"
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "14_teclado_terminal")
    teclas = {v: r.center for r, _, v in jogo.desafio.teclado.teclas}
    for ch in jogo.desafio.questao["resposta"]:
        dedo(jogo, pygame.FINGERDOWN, 3, teclas[ch])
        dedo(jogo, pygame.FINGERUP, 3, teclas[ch])
    dedo(jogo, pygame.FINGERDOWN, 3, teclas["OK"])
    assert jogo.desafio.estado == "feedback" and jogo.desafio.acertou
    # bloco de notas pelo teclado virtual
    jogo.notas.aberto = True
    tn = {v: r.center for r, _, v in jogo.notas.teclado.teclas}
    for ch in "6!/(2*3)":
        clique(jogo, tn[ch])
    clique(jogo, tn["CALCULAR"])
    assert jogo.notas.linhas[-2][0] == "= 120", jogo.notas.linhas
    passos(jogo, 2)
    salvar(jogo, salvar_dir, "15_teclado_notas")
    clique(jogo, tn["FECHAR"])
    assert not jogo.notas.aberto
    tecla(jogo, pygame.K_RETURN)          # fecha o feedback do terminal
    assert jogo.desafio is None
    # tela larga (celular deitado, ~20:9): jogo centralizado, controles nas faixas laterais
    jogo.ajustar_largura(1400)
    ox = jogo.ox
    assert jogo.display.get_width() == 1400 and ox == 188 and jogo.toque.lateral
    assert jogo.toque.base[0] < ox and jogo.toque.btn_e[0][0] > ox + main.LARGURA, "controles fora das faixas"
    jogo.jogador.rect.center = jogo.fase.inicio
    jogo.jogador.px, jogo.jogador.py = jogo.jogador.rect.center
    y0 = jogo.jogador.rect.centery
    b = jogo.toque.base
    dedo(jogo, pygame.FINGERDOWN, 7, b)
    dedo(jogo, pygame.FINGERMOTION, 7, (b[0], b[1] + 60))
    passos(jogo, 30)
    assert jogo.jogador.rect.centery > y0 + 40, "joystick lateral não moveu"
    pygame.image.save(jogo.display, os.path.join(salvar_dir, "16_tela_larga.png")) if salvar_dir else None
    dedo(jogo, pygame.FINGERUP, 7, b)
    na_tela = lambda p: (p[0] + ox, p[1])
    dedo(jogo, pygame.FINGERDOWN, 8, na_tela(jogo.r_pausa.center))
    assert jogo.pausado, "toque no botão de pausa (tela larga) falhou"
    dedo(jogo, pygame.FINGERDOWN, 8, na_tela(jogo.btn_continuar.rect.center))
    assert not jogo.pausado, "toque convertido em clique (tela larga) falhou"
    mudo = jogo.som.mudo
    jogo.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=na_tela(jogo.r_som.center), button=1, touch=False))
    assert jogo.som.mudo != mudo, "clique de mouse (tela larga) falhou"
    jogo.ajustar_largura(main.LARGURA)
    assert jogo.ox == 0 and not jogo.toque.lateral
    print("OK fluxo completo: menu→5 fases→final→reinício, erro sorteia nova questão, derrotas, notas, toque, tela larga")


def salvar(jogo, pasta, nome):
    if pasta:
        os.makedirs(pasta, exist_ok=True)
        pygame.image.save(jogo.tela, os.path.join(pasta, nome + ".png"))


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else None
    testar_banco()
    testar_mapas()
    testar_notas()
    testar_fluxo(pasta)
    print("TUDO OK")
