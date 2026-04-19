# -*- coding: utf-8 -*-
import pygame, math, random, array, sys, json, os

# ── Áudio ──────────────────────────────────────────────────────────────────────
SR = 44100

def _sq(f, t):  return 1.0 if (f * t) % 1 < 0.5 else -1.0
def _saw(f, t): return 2.0 * ((f * t) % 1) - 1.0

def _mk(samples):
    buf = array.array('h', [0] * (len(samples) * 2))
    for i, v in enumerate(samples):
        buf[2*i] = buf[2*i+1] = max(-32767, min(32767, int(v)))
    return pygame.mixer.Sound(buffer=buf)

def _snd_shoot():
    n = int(SR * 0.07)
    return _mk([32767*0.2*(1-i/n)**2*_sq(900*math.exp(-12*i/SR), i/SR) for i in range(n)])

def _snd_hit():
    n = int(SR * 0.05)
    return _mk([32767*0.25*(1-i/n)**1.5*random.uniform(-1, 1) for i in range(n)])

def _snd_explosion():
    n = int(SR * 0.4)
    return _mk([32767*0.42*math.exp(-4*i/SR)*(random.uniform(-1,1)*0.6+_saw(80*math.exp(-2*i/SR),i/SR)*0.4) for i in range(n)])

def _snd_powerup():
    samples = []
    for freq in [523, 659, 784, 1047]:
        seg = int(SR * 0.1)
        for j in range(seg):
            t = j / SR
            samples.append(32767*0.35*math.exp(-5*t/0.1)*math.sin(2*math.pi*freq*t))
    return _mk(samples)

def _snd_bomb():
    n = int(SR * 1.3)
    return _mk([32767*0.55*math.exp(-1.8*i/SR)*(1-math.exp(-20*i/SR))*(random.uniform(-1,1)*0.5+_saw(50*math.exp(-i/SR),i/SR)*0.5) for i in range(n)])

def _snd_player_dmg():
    n = int(SR * 0.18)
    return _mk([32767*0.38*math.exp(-8*i/SR)*(_sq(180*math.exp(-4*i/SR),i/SR)*0.6+random.uniform(-0.4,0.4)) for i in range(n)])

def _snd_boss_alert():
    samples = []
    for freq in [880, 660, 440]:
        for j in range(int(SR * 0.22)):
            t = j / SR
            samples.append(32767*0.3*math.exp(-3*t/0.22)*_sq(freq, t))
    return _mk(samples)

def _snd_music():
    vol = 0.14; bpm = 145; beat = 60/bpm; h = beat/2; q = beat/4
    mel = [
        (440,q),(0,q),(494,q),(523,h),(494,q),(440,q),(0,h),
        (392,q),(440,q),(494,h),(392,q),(330,beat),(0,beat),
        (523,q),(0,q),(587,q),(659,h),(587,q),(523,q),(0,h),
        (494,q),(523,q),(587,h),(494,q),(440,beat),(0,beat),
    ]
    bass = [110,110,131,131,110,110,98,98] * 4
    total = max(sum(d for _,d in mel), h*len(bass))
    n = int(total * SR)
    buf = array.array('h', [0]*(n*2))
    pos = 0
    for freq, dur in mel:
        samp = int(dur*SR)
        for i in range(samp):
            if freq > 0 and pos+i < n:
                t = i/SR; env = math.exp(-2*t/dur)
                v = int(32767*vol*0.65*env*_sq(freq, t))
                buf[2*(pos+i)]   = max(-32767, min(32767, buf[2*(pos+i)]  +v))
                buf[2*(pos+i)+1] = max(-32767, min(32767, buf[2*(pos+i)+1]+v))
        pos += samp
    pos = 0
    for freq in bass:
        samp = int(h*SR)
        for i in range(samp):
            if pos+i < n:
                t = i/SR; env = 0.5+0.5*math.exp(-6*t/h)
                v = int(32767*vol*0.5*env*_sq(freq//2, t))
                buf[2*(pos+i)]   = max(-32767, min(32767, buf[2*(pos+i)]  +v))
                buf[2*(pos+i)+1] = max(-32767, min(32767, buf[2*(pos+i)+1]+v))
        pos += samp
    return pygame.mixer.Sound(buffer=buf)


# ── Init ───────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)

W, H  = 800, 600
FPS   = 60
SCORE_FILE = "highscore.json"

PHASES = [
    {"name": "SETOR VERDE",   "star": (0,160,0),   "ec": (0,255,65),  "bc": (0,200,80),   "ui": (0,255,65),  "bg": (0,8,0),   "be": (0,255,80),  "bp": (150,255,80)},
    {"name": "SETOR CIANO",   "star": (0,130,200), "ec": (0,200,255), "bc": (0,160,220),  "ui": (0,200,255), "bg": (0,4,12),  "be": (0,200,255), "bp": (80,220,255)},
    {"name": "SETOR ÂMBAR",   "star": (190,130,0), "ec": (255,175,0), "bc": (220,110,0),  "ui": (255,175,0), "bg": (8,5,0),   "be": (255,155,0), "bp": (255,220,60)},
    {"name": "SETOR VIOLETA", "star": (120,0,180), "ec": (200,0,255), "bc": (160,0,220),  "ui": (200,0,255), "bg": (6,0,12),  "be": (200,0,255), "bp": (230,100,255)},
]

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("NAVE RETRÔ")
clock  = pygame.time.Clock()

_font_lg = pygame.font.SysFont("Courier New", 36, bold=True)
_font_md = pygame.font.SysFont("Courier New", 22, bold=True)
_font_sm = pygame.font.SysFont("Courier New", 16, bold=True)

_scanline = pygame.Surface((W, H), pygame.SRCALPHA)
for _y in range(0, H, 2):
    pygame.draw.line(_scanline, (0, 0, 0, 55), (0, _y), (W, _y))


# ── Utilitários ────────────────────────────────────────────────────────────────
def load_hs():
    try:
        with open(SCORE_FILE) as f: return json.load(f).get("hs", 0)
    except: return 0

def save_hs(score):
    hs = load_hs()
    if score > hs:
        with open(SCORE_FILE, "w") as f: json.dump({"hs": score}, f)

def dim(col, f):
    return tuple(max(0, min(255, int(c*f))) for c in col)

def glow_text(surf, text, font, col, x, y, center=False):
    gc = dim(col, 0.25)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        img = font.render(text, True, gc)
        rx = x - img.get_width()//2 + dx if center else x + dx
        surf.blit(img, (rx, y+dy))
    img = font.render(text, True, col)
    rx = x - img.get_width()//2 if center else x
    surf.blit(img, (rx, y))

def spawn_particles(particles, x, y, col, n=16, spd=3.5):
    for _ in range(n):
        a = random.uniform(0, 2*math.pi)
        s = random.uniform(0.5, spd)
        life = random.uniform(0.35, 0.85)
        particles.append([float(x), float(y), math.cos(a)*s, math.sin(a)*s, life, life, col])


# ── Estrelas (parallax) ────────────────────────────────────────────────────────
def make_stars():
    stars = []
    for _ in range(80): stars.append([random.uniform(0,W), random.uniform(0,H), 0.55, 1, 0])
    for _ in range(50): stars.append([random.uniform(0,W), random.uniform(0,H), 1.5,  1, 1])
    for _ in range(25): stars.append([random.uniform(0,W), random.uniform(0,H), 3.2,  2, 2])
    return stars

def update_stars(stars):
    for s in stars:
        s[1] += s[2]
        if s[1] > H:
            s[1] = random.uniform(-8, 0)
            s[0] = random.uniform(0, W)

def draw_stars(surf, stars, col):
    for s in stars:
        af = [0.22, 0.5, 1.0][int(s[4])]
        c  = dim(col, af)
        sx, sy = int(s[0]), int(s[1])
        if s[3] <= 1:
            if 0 <= sx < W and 0 <= sy < H:
                surf.set_at((sx, sy), c)
        else:
            pygame.draw.circle(surf, c, (sx, sy), int(s[3]))
        if s[2] >= 3.0 and sy-4 >= 0:
            surf.set_at((sx, sy-4), dim(c, 0.3))


# ── Desenho de sprites ─────────────────────────────────────────────────────────
def draw_player(surf, cx, cy, col, inv=0):
    if inv > 0 and (inv // 6) % 2 == 0:
        return
    pts = [(cx, cy-16),(cx-14,cy+9),(cx-7,cy+3),(cx,cy+11),(cx+7,cy+3),(cx+14,cy+9)]
    pygame.draw.polygon(surf, dim(col, 0.35), pts)
    pygame.draw.polygon(surf, col, pts, 1)
    pygame.draw.circle(surf, col, (cx, cy-4), 4)
    pygame.draw.circle(surf, dim(col, 0.25), (cx, cy-4), 3)
    gc = col if (pygame.time.get_ticks()//80)%2 else dim(col, 0.5)
    pygame.draw.circle(surf, gc, (cx, cy+11), 3)
    pygame.draw.circle(surf, dim(col, 0.2), (cx, cy+11), 5)

def draw_enemy(surf, cx, cy, col, etype, flash=0):
    c = (220,220,220) if flash > 0 else col
    cf = dim(c, 0.35)
    if etype == 0:
        pts = [(cx,cy+13),(cx-12,cy-7),(cx-6,cy+1),(cx,cy-9),(cx+6,cy+1),(cx+12,cy-7)]
        pygame.draw.polygon(surf, cf, pts)
        pygame.draw.polygon(surf, c, pts, 1)
        pygame.draw.circle(surf, c, (cx, cy+3), 3)
    elif etype == 1:
        pts = [(cx,cy-11),(cx+8,cy),(cx,cy+11),(cx-8,cy)]
        pygame.draw.polygon(surf, cf, pts)
        pygame.draw.polygon(surf, c, pts, 1)
    else:
        pts = [(cx,cy+17),(cx-17,cy+8),(cx-22,cy-5),(cx-10,cy-16),(cx+10,cy-16),(cx+22,cy-5),(cx+17,cy+8)]
        pygame.draw.polygon(surf, cf, pts)
        pygame.draw.polygon(surf, c, pts, 1)
        pygame.draw.circle(surf, c, (cx, cy), 5)

def draw_asteroid(surf, cx, cy, radius, col, seed):
    rng = random.Random(seed)
    pts = []
    for i in range(9):
        a = 2*math.pi*i/9 + rng.uniform(-0.25, 0.25)
        r = radius * rng.uniform(0.65, 1.0)
        pts.append((int(cx + r*math.cos(a)), int(cy + r*math.sin(a))))
    pygame.draw.polygon(surf, dim(col, 0.22), pts)
    pygame.draw.polygon(surf, dim(col, 0.65), pts, 1)

def draw_boss(surf, cx, cy, col, hp, flash=0):
    c = (220,220,220) if flash > 0 else col
    cf = dim(c, 0.28)
    pts = [
        (cx,cy+28),(cx-28,cy+16),(cx-50,cy+2),
        (cx-36,cy-14),(cx-20,cy-24),(cx,cy-18),
        (cx+20,cy-24),(cx+36,cy-14),(cx+50,cy+2),
        (cx+28,cy+16),
    ]
    pygame.draw.polygon(surf, cf, pts)
    pygame.draw.polygon(surf, c, pts, 2)
    pygame.draw.circle(surf, c, (cx, cy), 12)
    pygame.draw.circle(surf, cf, (cx, cy), 10)
    for dx in [-28, 28]:
        pygame.draw.circle(surf, c, (cx+dx, cy+6), 6, 1)
        pygame.draw.line(surf, c, (cx+dx, cy+6), (cx+dx, cy+14), 1)
    bar_w, bar_x, bar_y = 200, cx-100, cy-38
    pygame.draw.rect(surf, dim(c, 0.25), (bar_x, bar_y, bar_w, 7))
    fill = max(0, int(bar_w * hp / 300))
    bar_col = (220,60,60) if flash == 0 and hp < 90 else c
    pygame.draw.rect(surf, bar_col, (bar_x, bar_y, fill, 7))
    pygame.draw.rect(surf, c, (bar_x, bar_y, bar_w, 7), 1)

def draw_powerup(surf, cx, cy, ptype, col, bp_col):
    if ptype == 0:
        c = col
        pts = [(cx, cy-10),(cx+10,cy),(cx,cy+10),(cx-10,cy)]
        pygame.draw.polygon(surf, dim(c, 0.28), pts)
        pygame.draw.polygon(surf, c, pts, 1)
        pygame.draw.line(surf, c, (cx, cy-5), (cx, cy+5), 1)
        pygame.draw.line(surf, c, (cx-5, cy), (cx+5, cy), 1)
    else:
        c = bp_col
        pygame.draw.circle(surf, dim(c, 0.28), (cx, cy), 10)
        pygame.draw.circle(surf, c, (cx, cy), 10, 1)
        pygame.draw.circle(surf, c, (cx, cy), 4)

def draw_bullet_player(surf, bx, by, col):
    pygame.draw.rect(surf, col, (int(bx)-2, int(by)-6, 4, 12))
    pygame.draw.rect(surf, dim(col, 0.4), (int(bx)-1, int(by)-9, 2, 4))

def draw_bullet_enemy(surf, bx, by, col):
    pygame.draw.circle(surf, col, (int(bx), int(by)), 4)
    pygame.draw.circle(surf, dim(col, 0.4), (int(bx), int(by)), 6, 1)


# ── Classe principal ───────────────────────────────────────────────────────────
class Game:
    MENU        = 0
    PLAYING     = 1
    BOSS_WARN   = 2
    PHASE_CLEAR = 3
    GAME_OVER   = 4
    VICTORY     = 5

    def __init__(self):
        self.highscore = load_hs()
        self.sfx = {}
        self.music = None
        self._load_audio()
        self.state = self.MENU
        self._init_game()

    def _load_audio(self):
        try:
            self.sfx = {
                'shoot':      _snd_shoot(),
                'hit':        _snd_hit(),
                'explosion':  _snd_explosion(),
                'powerup':    _snd_powerup(),
                'bomb':       _snd_bomb(),
                'player_dmg': _snd_player_dmg(),
                'boss_alert': _snd_boss_alert(),
            }
            self.music = _snd_music()
            self.music.play(-1)
        except Exception as e:
            print(f"Audio: {e}")

    def _play(self, name):
        s = self.sfx.get(name)
        if s: s.play()

    def _init_game(self):
        self.phase_idx = 0
        self.score     = 0
        self.lives     = 3
        self._start_phase()

    def _start_phase(self):
        pal = PHASES[self.phase_idx % len(PHASES)]
        self.pal         = pal
        self.stars       = make_stars()
        self.px          = float(W // 2)
        self.py          = float(H - 100)
        self.inv         = 0
        self.weapon_lvl  = 1
        self.bombs       = 3
        self.shoot_cd    = 0
        self.p_bullets   = []
        self.e_bullets   = []
        self.enemies     = []
        self.asteroids   = []
        self.powerups    = []
        self.particles   = []
        self.boss        = None
        self.boss_vx     = 1.8 + self.phase_idx * 0.15
        self.bomb_flash  = 0
        self.kills       = 0
        self.target_kills = 18 + self.phase_idx * 4
        self.spawn_cd    = 70
        self.spawned     = 0
        self.state_timer = 0
        self.pspd        = 1.0 + self.phase_idx * 0.18

    # ── Run ────────────────────────────────────────────────────────────────────
    def run(self):
        while True:
            clock.tick(FPS)
            self._events()
            self._update()
            self._draw()

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_hs(self.score); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    save_hs(self.score); pygame.quit(); sys.exit()
                if self.state == self.MENU and ev.key == pygame.K_RETURN:
                    self.state = self.PLAYING
                if self.state in (self.GAME_OVER, self.VICTORY) and ev.key == pygame.K_RETURN:
                    self._init_game(); self.state = self.PLAYING
                if self.state == self.PLAYING and ev.key in (pygame.K_b, pygame.K_x):
                    self._use_bomb()

    def _update(self):
        if self.state == self.BOSS_WARN:
            self.state_timer -= 1
            update_stars(self.stars)
            if self.state_timer <= 0:
                self._spawn_boss()
                self.state = self.PLAYING
            return

        if self.state == self.PHASE_CLEAR:
            self.state_timer -= 1
            update_stars(self.stars)
            if self.state_timer <= 0:
                self.phase_idx += 1
                if self.phase_idx >= len(PHASES) * 2:
                    save_hs(self.score); self.state = self.VICTORY
                else:
                    self._start_phase(); self.state = self.PLAYING
            return

        if self.state != self.PLAYING:
            return

        keys = pygame.key.get_pressed()

        # Movimento do jogador
        spd = 5.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.px -= spd
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.px += spd
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.py -= spd
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.py += spd
        self.px = max(16, min(W-16, self.px))
        self.py = max(20, min(H-20, self.py))

        # Disparo do jogador
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.shoot_cd <= 0:
            self._player_shoot()
            self.shoot_cd = max(5, 12 - self.weapon_lvl * 2)

        if self.inv > 0: self.inv -= 1

        update_stars(self.stars)

        # Mover projéteis do jogador
        new_pb = []
        for b in self.p_bullets:
            b[0] += b[2]; b[1] += b[3]
            if -10 < b[1] < H+10 and -10 < b[0] < W+10:
                new_pb.append(b)
        self.p_bullets = new_pb

        # Mover projéteis inimigos
        new_eb = []
        for b in self.e_bullets:
            b[0] += b[2]; b[1] += b[3]
            if -20 < b[0] < W+20 and -20 < b[1] < H+20:
                new_eb.append(b)
        self.e_bullets = new_eb

        # Spawning e atualização de inimigos
        if self.boss is None:
            self._do_spawn()
            for e in self.enemies: self._update_enemy(e)
            self.enemies   = [e for e in self.enemies   if e['alive']]
            for a in self.asteroids: self._update_asteroid(a)
            self.asteroids = [a for a in self.asteroids if a['alive']]
            # Verificar se já pode surgir o boss
            if (self.spawned >= self.target_kills
                    and not self.enemies and not self.asteroids
                    and self.state == self.PLAYING):
                self._play('boss_alert')
                self.state = self.BOSS_WARN
                self.state_timer = FPS * 3
        else:
            self._update_boss()

        # Powerups
        new_pu = []
        for p in self.powerups:
            p[1] += 1.6
            if p[1] < H+20: new_pu.append(p)
        self.powerups = new_pu

        # Partículas
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 1/FPS
        self.particles = [p for p in self.particles if p[4] > 0]

        if self.bomb_flash > 0: self.bomb_flash -= 1

        self._collisions()

        # Morte do boss
        if self.boss and self.boss['hp'] <= 0:
            spawn_particles(self.particles, self.boss['x'], self.boss['y'], self.pal['bc'], n=40, spd=6)
            self._play('explosion')
            self.score += 500 + self.phase_idx * 100
            self.boss = None
            self.state = self.PHASE_CLEAR
            self.state_timer = FPS * 3

    # ── Lógica de jogo ─────────────────────────────────────────────────────────
    def _player_shoot(self):
        col  = self.pal['bp']
        bspd = 10.0
        angles = {1:[0], 2:[-8,8], 3:[-18,0,18], 4:[-22,-7,7,22], 5:[-28,-14,0,14,28]}
        for deg in angles.get(self.weapon_lvl, [0]):
            ang = math.radians(deg)
            self.p_bullets.append([self.px, self.py-16, bspd*math.sin(ang), -bspd*math.cos(ang), col, 1])
        self._play('shoot')

    def _use_bomb(self):
        if self.bombs <= 0: return
        self.bombs -= 1
        self.bomb_flash = 50
        self._play('bomb')
        for e in self.enemies:   e['hp'] = 0
        for a in self.asteroids: a['hp'] = 0
        if self.boss: self.boss['hp'] -= 80
        self.e_bullets.clear()
        spawn_particles(self.particles, W//2, H//2, self.pal['ui'], n=60, spd=9)

    def _do_spawn(self):
        if self.spawned >= self.target_kills: return
        self.spawn_cd -= 1
        if self.spawn_cd > 0: return
        if random.random() < 0.22:
            r   = random.choice([18, 28])
            spd = random.uniform(1.0, 2.2) * self.pspd
            self.asteroids.append({
                'x': random.uniform(r, W-r), 'y': float(-r),
                'r': r, 'vy': spd, 'seed': random.randint(0, 99999),
                'hp': 3 if r > 20 else 1, 'alive': True
            })
        else:
            etype = random.choices([0, 1, 2], weights=[5, 3, 2])[0]
            si    = max(50, int(110 / self.pspd))
            hp    = [1, 1, 3][etype]
            self.enemies.append({
                'x': float(random.uniform(18, W-18)), 'y': -18.0,
                'vx': random.uniform(-1.2, 1.2)*self.pspd,
                'vy': random.uniform(1.2, 2.0)*self.pspd,
                'etype': etype, 'hp': hp, 'max_hp': hp,
                'shoot_cd': random.randint(20, si),
                'shoot_int': si, 'strafe_t': random.randint(30, 80),
                'alive': True, 'flash': 0,
                'drop': random.random(),
            })
        self.spawned += 1
        self.spawn_cd = max(18, int(55 / self.pspd))

    def _update_enemy(self, e):
        e['x'] += e['vx']; e['y'] += e['vy']
        e['strafe_t'] -= 1
        if e['strafe_t'] <= 0:
            e['vx'] = random.uniform(-2.0, 2.0) * self.pspd
            e['strafe_t'] = random.randint(30, 80)
        if e['x'] < 15 or e['x'] > W-15: e['vx'] *= -1
        if e['y'] > H+30 or e['hp'] <= 0: e['alive'] = False
        if e['flash'] > 0: e['flash'] -= 1
        e['shoot_cd'] -= 1
        if e['shoot_cd'] <= 0 and 10 < e['y'] < H-10:
            dx = self.px - e['x']; dy = self.py - e['y']
            d  = math.hypot(dx, dy) or 1
            sp = 4.0 * self.pspd
            shots = 2 if e['etype'] == 2 else 1
            for s in range(shots):
                spread = (s - (shots-1)/2) * 0.18
                self.e_bullets.append([e['x'], e['y'], (dx/d+spread)*sp, (dy/d)*sp, self.pal['be']])
            e['shoot_cd'] = e['shoot_int']

    def _update_asteroid(self, a):
        a['y'] += a['vy']
        if a['y'] > H + a['r'] + 10 or a['hp'] <= 0: a['alive'] = False

    def _spawn_boss(self):
        self.boss = {
            'x': float(W/2), 'y': -80.0,
            'hp': 300, 'entering': True,
            'atk_cd': 130, 'flash': 0
        }

    def _update_boss(self):
        b = self.boss
        if b['entering']:
            b['y'] += 1.4
            if b['y'] >= 110: b['y'] = 110.0; b['entering'] = False
            return
        b['x'] += self.boss_vx
        if b['x'] > W-55 or b['x'] < 55: self.boss_vx *= -1
        if b['flash'] > 0: b['flash'] -= 1
        b['atk_cd'] -= 1
        if b['atk_cd'] <= 0:
            b['atk_cd'] = max(38, int(88 / self.pspd))
            hp_f = b['hp'] / 300
            spread = 5 if hp_f < 0.5 else 3
            for i in range(spread):
                ang = math.radians((i-(spread-1)/2) * (28 if hp_f < 0.5 else 18))
                sp  = 5.0 * self.pspd
                self.e_bullets.append([b['x'], b['y']+30, math.sin(ang)*sp, math.cos(ang)*sp, self.pal['be']])
            if hp_f < 0.5:
                dx = self.px - b['x']; dy = self.py - b['y']
                d  = math.hypot(dx, dy) or 1
                sp = 5.5 * self.pspd
                self.e_bullets.append([b['x'], b['y']+30, dx/d*sp, dy/d*sp, self.pal['be']])

    def _collisions(self):
        prect = pygame.Rect(int(self.px)-10, int(self.py)-13, 20, 26)

        # Projéteis do jogador vs inimigos / asteroides / boss
        bullets_keep = []
        for b in self.p_bullets:
            bx, by = b[0], b[1]
            brect = pygame.Rect(int(bx)-2, int(by)-6, 4, 12)
            removed = False

            if not removed:
                for e in self.enemies:
                    if not e['alive']: continue
                    ew = [14, 10, 24][e['etype']]
                    eh = [28, 22, 36][e['etype']]
                    if brect.colliderect(pygame.Rect(int(e['x'])-ew//2, int(e['y'])-eh//2, ew, eh)):
                        removed = True
                        e['hp'] -= b[5]; e['flash'] = 8
                        self._play('hit')
                        if e['hp'] <= 0:
                            spawn_particles(self.particles, e['x'], e['y'], self.pal['ec'])
                            self._play('explosion')
                            self.score += [10, 15, 30][e['etype']]
                            self.kills += 1
                            if e['drop'] < [0.14, 0.08, 0.40][e['etype']]:
                                pt = 0 if random.random() < 0.65 else 1
                                self.powerups.append([e['x'], e['y'], pt, 0])
                        break

            if not removed:
                for a in self.asteroids:
                    if not a['alive']: continue
                    if math.hypot(bx-a['x'], by-a['y']) < a['r']:
                        removed = True
                        a['hp'] -= b[5]
                        self._play('hit')
                        if a['hp'] <= 0:
                            spawn_particles(self.particles, a['x'], a['y'], self.pal['star'])
                            self._play('explosion')
                            self.score += 5
                        break

            if not removed and self.boss and not self.boss['entering']:
                bossrect = pygame.Rect(int(self.boss['x'])-50, int(self.boss['y'])-28, 100, 56)
                if brect.colliderect(bossrect):
                    removed = True
                    self.boss['hp'] -= b[5]
                    self.boss['flash'] = 6
                    self._play('hit')
                    spawn_particles(self.particles, bx, by, self.pal['bc'], n=6, spd=2)

            if not removed:
                bullets_keep.append(b)
        self.p_bullets = bullets_keep

        # Projéteis inimigos vs jogador
        if self.inv <= 0:
            bullets_keep = []
            for b in self.e_bullets:
                if math.hypot(b[0]-self.px, b[1]-self.py) < 10:
                    self._hit_player()
                else:
                    bullets_keep.append(b)
            self.e_bullets = bullets_keep

            # Colisão direta com inimigos
            for e in self.enemies:
                if not e['alive']: continue
                ew = [14, 10, 24][e['etype']]
                if prect.colliderect(pygame.Rect(int(e['x'])-ew//2, int(e['y'])-14, ew, 28)):
                    self._hit_player(); e['hp'] = 0; break

            # Colisão com asteroides
            for a in self.asteroids:
                if not a['alive']: continue
                if math.hypot(self.px-a['x'], self.py-a['y']) < a['r']+10:
                    self._hit_player(); break

        # Coletar powerups
        pu_keep = []
        for p in self.powerups:
            if math.hypot(self.px-p[0], self.py-p[1]) < 20:
                self._play('powerup')
                if p[2] == 0:
                    self.weapon_lvl = min(5, self.weapon_lvl + 1)
                else:
                    self.bombs = min(5, self.bombs + 1)
            else:
                pu_keep.append(p)
        self.powerups = pu_keep

    def _hit_player(self):
        if self.inv > 0: return
        self.lives -= 1
        self.weapon_lvl = max(1, self.weapon_lvl - 1)
        self.inv = 120
        self._play('player_dmg')
        spawn_particles(self.particles, self.px, self.py, self.pal['ui'], n=20, spd=4)
        if self.lives <= 0:
            save_hs(self.score)
            self.highscore = max(self.highscore, self.score)
            self.state = self.GAME_OVER

    # ── Desenho ────────────────────────────────────────────────────────────────
    def _draw(self):
        pal = self.pal
        screen.fill(pal['bg'])
        draw_stars(screen, self.stars, pal['star'])

        if self.state == self.MENU:
            self._draw_menu()
        elif self.state == self.BOSS_WARN:
            self._draw_hud()
            self._draw_game_objects()
            self._draw_boss_warn()
        elif self.state == self.PHASE_CLEAR:
            self._draw_hud()
            self._draw_game_objects()
            self._draw_phase_clear()
        elif self.state == self.PLAYING:
            self._draw_hud()
            self._draw_game_objects()
        elif self.state == self.GAME_OVER:
            self._draw_game_over()
        elif self.state == self.VICTORY:
            self._draw_victory()

        screen.blit(_scanline, (0, 0))
        pygame.display.flip()

    def _draw_game_objects(self):
        pal = self.pal
        # Partículas
        for p in self.particles:
            alpha = p[4] / p[5]
            c = dim(p[6], alpha)
            if 0 <= int(p[0]) < W and 0 <= int(p[1]) < H:
                screen.set_at((int(p[0]), int(p[1])), c)

        # Projéteis inimigos
        for b in self.e_bullets:
            draw_bullet_enemy(screen, b[0], b[1], b[4])

        # Asteroides
        for a in self.asteroids:
            draw_asteroid(screen, a['x'], a['y'], a['r'], pal['star'], a['seed'])

        # Inimigos
        for e in self.enemies:
            draw_enemy(screen, int(e['x']), int(e['y']), pal['ec'], e['etype'], e['flash'])

        # Boss
        if self.boss:
            draw_boss(screen, int(self.boss['x']), int(self.boss['y']), pal['bc'], self.boss['hp'], self.boss['flash'])

        # Powerups
        for p in self.powerups:
            draw_powerup(screen, int(p[0]), int(p[1]), p[2], pal['ui'], pal['bp'])

        # Projéteis do jogador
        for b in self.p_bullets:
            draw_bullet_player(screen, b[0], b[1], b[4])

        # Nave do jogador
        draw_player(screen, int(self.px), int(self.py), pal['ui'], self.inv)

        # Flash de bomba
        if self.bomb_flash > 0:
            alpha = int(180 * self.bomb_flash / 50)
            flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            flash_surf.fill((*pal['ui'], alpha))
            screen.blit(flash_surf, (0, 0))

    def _draw_hud(self):
        pal = self.pal
        c   = pal['ui']
        # Pontuação
        glow_text(screen, f"SCORE  {self.score:06d}", _font_sm, c, 10, 10)
        glow_text(screen, f"MELHOR {self.highscore:06d}", _font_sm, c, 10, 30)
        # Fase
        glow_text(screen, PHASES[self.phase_idx % len(PHASES)]['name'], _font_sm, c, W//2, 10, center=True)
        # Vidas
        glow_text(screen, "VIDAS", _font_sm, c, W-130, 10)
        for i in range(self.lives):
            lx = W-60 + i*18 - self.lives*9
            pts = [(lx,5),(lx-7,18),(lx,14),(lx+7,18)]
            pygame.draw.polygon(screen, c, pts, 1)
        # Arma
        glow_text(screen, f"PWR{'█'*self.weapon_lvl}{'░'*(5-self.weapon_lvl)}", _font_sm, c, 10, H-28)
        # Bombas
        glow_text(screen, f"BOMB x{self.bombs}", _font_sm, c, W-110, H-28)

    def _draw_menu(self):
        pal = self.pal
        c   = pal['ui']
        t   = pygame.time.get_ticks() / 1000
        glow_text(screen, "NAVE RETRÔ", _font_lg, c, W//2, H//2-90, center=True)
        if int(t * 1.5) % 2 == 0:
            glow_text(screen, "PRESSIONE ENTER PARA INICIAR", _font_sm, c, W//2, H//2-20, center=True)
        glow_text(screen, "SETAS / WASD  — MOVER", _font_sm, dim(c,0.6), W//2, H//2+30, center=True)
        glow_text(screen, "ESPAÇO / Z    — ATIRAR", _font_sm, dim(c,0.6), W//2, H//2+54, center=True)
        glow_text(screen, "B / X         — BOMBA", _font_sm, dim(c,0.6), W//2, H//2+78, center=True)
        glow_text(screen, f"MELHOR: {self.highscore:06d}", _font_sm, dim(c,0.7), W//2, H//2+118, center=True)
        # Preview das fases
        for i, ph in enumerate(PHASES):
            col = ph['ui']
            pygame.draw.circle(screen, col, (W//2 - 60 + i*40, H//2+160), 8, 1 if i != 0 else 0)

    def _draw_boss_warn(self):
        c = self.pal['ui']
        t = pygame.time.get_ticks() // 250 % 2
        if t:
            glow_text(screen, "⚠ CHEFE APROXIMANDO ⚠", _font_md, c, W//2, H//2-14, center=True)

    def _draw_phase_clear(self):
        c = self.pal['ui']
        glow_text(screen, "FASE CONCLUÍDA", _font_lg, c, W//2, H//2-30, center=True)
        glow_text(screen, f"PONTOS: {self.score:06d}", _font_md, c, W//2, H//2+20, center=True)

    def _draw_game_over(self):
        pal  = PHASES[self.phase_idx % len(PHASES)]
        c    = pal['ui']
        draw_stars(screen, self.stars, pal['star'])
        glow_text(screen, "GAME OVER", _font_lg, c, W//2, H//2-60, center=True)
        glow_text(screen, f"PONTUAÇÃO: {self.score:06d}", _font_md, c, W//2, H//2, center=True)
        hs = load_hs()
        if self.score >= hs:
            glow_text(screen, "NOVO RECORDE!", _font_sm, c, W//2, H//2+38, center=True)
        glow_text(screen, "ENTER — JOGAR NOVAMENTE", _font_sm, dim(c,0.6), W//2, H//2+70, center=True)

    def _draw_victory(self):
        pal = PHASES[0]
        c   = pal['ui']
        draw_stars(screen, self.stars, pal['star'])
        t   = pygame.time.get_ticks() / 1000
        cyc = int(t*2) % len(PHASES)
        cc  = PHASES[cyc]['ui']
        glow_text(screen, "VITÓRIA!", _font_lg, cc, W//2, H//2-70, center=True)
        glow_text(screen, "TODOS OS SETORES LIBERADOS", _font_md, c, W//2, H//2-10, center=True)
        glow_text(screen, f"PONTUAÇÃO FINAL: {self.score:06d}", _font_md, c, W//2, H//2+32, center=True)
        glow_text(screen, "ENTER — MENU", _font_sm, dim(c,0.6), W//2, H//2+76, center=True)


# ── Entrada ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
