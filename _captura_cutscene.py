# -*- coding: utf-8 -*-
"""Captura screenshots de cada cena da cutscene final."""
import os, sys, math, random
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.mixer.init()

_fake_cls = type('S', (), {'play': lambda *a,**k: None, 'stop': lambda *a: None,
                            'set_volume': lambda *a: None})
pygame.mixer.Sound = lambda **k: _fake_cls()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jogo

# Tempos no meio de cada cena para captura
CENAS = [
    (2.0,  "cena0_batalha_final.png"),
    (6.0,  "cena1_dispositivo_ativado.png"),
    (11.0, "cena2_ruptura_dimensional.png"),
    (17.0, "cena3_buraco_negro.png"),
    (22.5, "cena4_nave_sugada.png"),
    (27.0, "cena5_fim_capitulo.png"),
]

random.seed(42)

for tempo_alvo, nome_arquivo in CENAS:
    # Instancia o jogo do zero em estado de cutscene
    g = jogo.Game.__new__(jogo.Game)
    g.highscore = jogo.load_hs()
    g.sfx = {}
    g.music = None
    g.state = jogo.Game.MENU
    g._init_game()

    # Coloca na cutscene
    g.phase_idx = 9
    g.pal = jogo.PHASES[9]
    g._start_cutscene()

    # Simula o tempo avançando frame a frame
    frames_alvo = int(tempo_alvo * jogo.FPS)
    random.seed(42)
    for _ in range(frames_alvo):
        g._update_cutscene()

    # Força cs_t exato para o texto aparecer certo
    g.cs_t = tempo_alvo
    g.cs_scene = len([b for b in [4.0, 8.0, 14.0, 20.0, 25.0] if tempo_alvo >= b])

    # Renderiza
    g._draw_cutscene()
    pygame.image.save(jogo.screen, nome_arquivo)
    print(f"Salvo: {nome_arquivo}")

pygame.quit()
print("Concluído!")
