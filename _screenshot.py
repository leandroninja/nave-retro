# -*- coding: utf-8 -*-
"""Captura a tela inicial do jogo e salva como screenshot.png"""
import os, sys
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.mixer.init()

_fake_cls = type('S', (), {'play': lambda *a,**k: None, 'stop': lambda *a: None})
pygame.mixer.Sound = lambda **k: _fake_cls()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jogo

g = jogo.Game.__new__(jogo.Game)
g.highscore = jogo.load_hs()
g.sfx = {}
g.music = None
g.state = jogo.Game.MENU
g._init_game()

g._draw()

pygame.image.save(jogo.screen, "screenshot.png")
print("screenshot.png salvo!")
pygame.quit()
