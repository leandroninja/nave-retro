# Nave Retrô

Jogo de nave estilo shoot 'em up com visual CRT fósforo — scanlines, estrelas com parallax e efeitos retrô. Desvie e destrua asteroides e naves inimigas através de 4 setores com chefes finais.

![Tela inicial](screenshot.png)

## Funcionalidades

- **Visual CRT retrô** — fundo escuro, scanlines, efeito fósforo
- **Parallax de estrelas** — 3 camadas em velocidades distintas, sensação real de movimento
- **Nave com movimento livre** por toda a tela
- **Inimigos de 3 tipos** — padrão, rápido (diamante) e pesado (hexagonal)
- **Asteroides** em dois tamanhos — sem disparo, puro obstáculo
- **Projéteis inimigos** com mira no jogador
- **Power-ups dropeados** por inimigos:
  - **Cristal (PWR)** — aumenta o nível do disparo até 5 (spread de 1 a 5 tiros)
  - **Bomba (BOMB)** — adiciona 1 bomba (máx. 5)
- **Bomba especial** — destroi tudo na tela com explosão visual
- **Chefe final** por fase — nave grande com 300 HP e 2 padrões de ataque
- **4 fases com paletas distintas**: Verde → Ciano → Âmbar → Violeta
- **Highscore** salvo em `highscore.json`
- **Música e sons** gerados por código — sem arquivos externos

## Controles

| Tecla | Ação |
|-------|------|
| `↑ ↓ ← →` / `W A S D` | Mover a nave |
| `Espaço` / `Z` | Atirar |
| `B` / `X` | Lançar bomba |
| `Esc` | Sair |

## Requisitos

```bash
pip install pygame
```

## Como jogar

```bash
python jogo.py
```

## Desenvolvido por

**Leandro Oliveira Moraes** — [github.com/leandroninja](https://github.com/leandroninja)
