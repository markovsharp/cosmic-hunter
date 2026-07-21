#!/usr/bin/env python3
"""VIANA - Ocean Adventure"""

import pygame
import random
import math
import sys

# ── Constants ────────────────────────────────────────────────────────────────
W, H = 1100, 750
FPS = 60
SEA_LEVEL = H - 140

WEAPONS = [
    {"name": "Harpoon",  "dmg": 20, "speed": 12, "color": (200, 180, 100), "range": 350},
    {"name": "Cannon",   "dmg": 50, "speed": 8,  "color": (80, 80, 80),    "range": 500, "splash": 60},
    {"name": "Net",      "dmg": 10, "speed": 10, "color": (100, 200, 200), "range": 250, "catch": True},
]

FISH_TYPES = [
    {"name": "Opah",      "color": (255, 150, 50),   "size": 14, "value": 15, "speed": 2.5},
    {"name": "Mahi Mahi", "color": (50, 200, 100),    "size": 16, "value": 20, "speed": 3.5},
    {"name": "Ahi Tuna",  "color": (30, 60, 150),     "size": 20, "value": 35, "speed": 4},
    {"name": "Rainbow Fish","color": (200, 100, 200), "size": 10, "value": 30, "speed": 3},
    {"name": "Giant Trevally","color": (180, 180, 200),"size": 22, "value": 45, "speed": 4.5},
    {"name": "Clownfish", "color": (255, 100, 50),    "size": 8,  "value": 20, "speed": 2},
]

MONSTER_TYPES = [
    {"name": "Kraken",     "color": (100, 0, 70),     "hp": 80,  "dmg": 15, "reward": 120, "size": 55},
    {"name": "Sea Serpent","color": (0, 140, 70),     "hp": 60,  "dmg": 10, "reward": 80,  "size": 45},
    {"name": "Mega Shark", "color": (70, 70, 90),     "hp": 50,  "dmg": 12, "reward": 65,  "size": 40},
    {"name": "Ghost Ship", "color": (60, 60, 90),     "hp": 100, "dmg": 18, "reward": 160, "size": 60},
]

RARE_FISH_TYPES = [
    {"name": "Golden Marlin",    "color": (255, 215, 0),   "size": 24, "value": 150, "speed": 6, "rarity": 0.05},
    {"name": "Pearl Octopus",    "color": (230, 200, 255),  "size": 12, "value": 200, "speed": 2, "rarity": 0.03},
    {"name": "Crystal Koi",      "color": (150, 255, 255),  "size": 16, "value": 250, "speed": 3, "rarity": 0.02},
    {"name": "Phoenix Grouper",  "color": (255, 100, 50),   "size": 20, "value": 300, "speed": 5, "rarity": 0.02},
]

WEATHER_TYPES = ["clear", "cloudy", "storm"]

MERCHANT_ITEMS = [
    {"name": "Hull Upgrade",  "cost": 200, "effect": "hp",       "desc": "+50 Max HP"},
    {"name": "Speed Sail",    "cost": 150, "effect": "speed",    "desc": "+1 Speed"},
    {"name": "Scope Lens",    "cost": 100, "effect": "range",    "desc": "+50 Weapon Range"},
    {"name": "Power Core",    "cost": 300, "effect": "dmg",      "desc": "+5 All DMG"},
    {"name": "Repair Kit",    "cost": 80,  "effect": "heal",     "desc": "Heal 30 HP"},
    {"name": "Lucky Charm",   "cost": 250, "effect": "luck",     "desc": "+Fish Rate"},
]

# ── Helpers ──────────────────────────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * max(0, min(1, t))

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def lerp_col(a, b, t):
    return (int(lerp(a[0], b[0], t)), int(lerp(a[1], b[1], t)), int(lerp(a[2], b[2], t)))

# ── Ocean ────────────────────────────────────────────────────────────────────
class Ocean:
    def __init__(self):
        self.time = 0
        self.weather = "clear"
        self.weather_timer = 0
        self.weather_duration = random.randint(600, 1800)
        self.storm_intensity = 0.0
        self.surface = pygame.Surface((W, H - SEA_LEVEL), pygame.SRCALPHA)
        self.seabed_decor = []
        self._init_seabed()
        self._water_gradient = None
        self._build_water_gradient()
        self._wave_pts_cache = [(x, 0) for x in range(-10, W + 20, 4)]

    def _init_seabed(self):
        self.sand_dots = []
        for _ in range(80):
            self.sand_dots.append({
                "x": random.randint(10, W - 10),
                "y": H - random.randint(2, 40),
                "size": random.uniform(1, 3),
                "shade": random.uniform(0.5, 1.0),
            })
        self.school_fish = []
        for _ in range(12):
            self.school_fish.append({
                "x": random.randint(50, W - 50),
                "y": H - random.randint(30, 70),
                "vx": random.uniform(-0.5, 0.5),
                "phase": random.uniform(0, math.pi * 2),
                "size": random.uniform(3, 5),
                "color": random.choice([
                    (180, 180, 200), (150, 200, 180), (200, 180, 150),
                    (160, 160, 220), (200, 160, 160),
                ]),
            })
        for _ in range(15):
            self.seabed_decor.append({
                "type": random.choice(["coral", "seaweed", "rock", "anemone"]),
                "x": random.randint(20, W - 20),
                "y": H - random.randint(5, 25),
                "size": random.uniform(6, 20),
                "sway": random.uniform(0, math.pi * 2),
                "color": random.choice([
                    (200, 80, 80), (80, 200, 80), (200, 180, 60),
                    (60, 100, 200), (200, 60, 150), (100, 200, 150)
                ]),
            })

    def _build_water_gradient(self):
        if self._water_gradient is not None:
            return
        # Pre-render the water gradient once
        w = 64
        h = H - SEA_LEVEL
        self._water_gradient = pygame.Surface((w, h))
        for y in range(h):
            depth = y / h
            r = max(0, 8 - depth * 8)
            g = max(0, 80 - depth * 50)
            b = max(40, 180 - depth * 80)
            if depth < 0.3:
                g += int(30 * (1 - depth / 0.3))
                b += int(20 * (1 - depth / 0.3))
            c = (int(min(r, 255)), int(min(g, 255)), int(min(b, 255)))
            pygame.draw.line(self._water_gradient, c, (0, y), (w, y))

    def update(self):
        self.time += 0.015
        self.weather_timer += 1
        if self.weather_timer > self.weather_duration:
            self._change_weather()
        # update school fish
        for f in self.school_fish:
            f["x"] += f["vx"]
            f["y"] += math.sin(self.time * 1.5 + f["phase"]) * 0.15
            if f["x"] < 10 or f["x"] > W - 10:
                f["vx"] *= -1
            f["y"] = max(SEA_LEVEL + 60, min(H - 10, f["y"]))

    def _change_weather(self):
        old = self.weather
        self.weather = random.choice(WEATHER_TYPES)
        if self.weather == "storm":
            self.storm_intensity = 0.0
        self.weather_timer = 0
        self.weather_duration = random.randint(600, 1800) if self.weather != "storm" else random.randint(400, 900)

    def get_y(self, x):
        base = (SEA_LEVEL
                + 10 * math.sin(x * 0.015 + self.time * 1.2)
                + 6 * math.sin(x * 0.03 + self.time * 1.8)
                + 4 * math.sin(x * 0.007 + self.time * 0.7)
                + 3 * math.sin(x * 0.05 + self.time * 2.5))
        if self.weather == "storm":
            base += 15 * math.sin(x * 0.02 + self.time * 4.0) * self.storm_intensity
        return base

    def draw_seabed(self, surf):
        # sandy seabed texture
        for sd in self.sand_dots:
            c = int(160 * sd["shade"]), int(140 * sd["shade"]), int(100 * sd["shade"])
            pygame.draw.circle(surf, c, (int(sd["x"]), int(sd["y"])), int(sd["size"]))
        for d in self.seabed_decor:
            bx, by = int(d["x"]), int(d["y"])
            sway = math.sin(self.time * 1.5 + d["sway"]) * 3
            sz = d["size"]
            if d["type"] == "coral":
                for i in range(3):
                    cx = bx + int(sway * (i + 1) * 0.3) + i * 6 - 6
                    cy = by - int(sz * 0.3 + i * sz * 0.15)
                    pygame.draw.circle(surf, d["color"], (cx, cy), max(2, int(sz * 0.2 + i * 1)))
                    pygame.draw.line(surf, (d["color"][0]//2, d["color"][1]//2, d["color"][2]//2),
                                     (bx, by), (cx, cy), 2)
            elif d["type"] == "seaweed":
                pts = []
                for i in range(5):
                    px = bx + int(sway * (i / 4)) + int(math.sin(self.time * 2 + i * 0.7) * 4)
                    py = by - int(i * sz * 0.25)
                    pts.append((px, py))
                if len(pts) > 1:
                    pygame.draw.lines(surf, d["color"], False, pts, 2)
            elif d["type"] == "anemone":
                for i in range(6):
                    a = math.radians(i * 60 + self.time * 30)
                    ex = bx + int(math.cos(a) * sz * 0.3) + int(sway * 0.5)
                    ey = by - int(sz * 0.2 * abs(math.sin(a)))
                    pygame.draw.line(surf, d["color"], (bx, by), (ex, ey), 2)
                    pygame.draw.circle(surf, (255, 255, 200, 100), (ex, ey), 2)
            else:
                pygame.draw.ellipse(surf, (80, 70, 60), (bx - sz // 2, by - sz // 4, sz, sz // 2))

    def draw_caustics(self, surf, now):
        count = 20 if self.weather != "storm" else 6
        for i in range(count):
            cx = (now * 30 + i * 51 + math.sin(now * 0.5 + i) * 40) % W
            cy = SEA_LEVEL + 30 + (i * 27 + now * 20) % (H - SEA_LEVEL - 60)
            size = 15 + 10 * math.sin(now * 0.7 + i * 1.3)
            alpha = int(20 + 15 * math.sin(now + i * 0.9))
            s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 200, alpha), (int(size), int(size)), int(size * 0.5), 1)
            pygame.draw.circle(s, (255, 255, 200, alpha // 2), (int(size), int(size)), int(size * 0.8), 1)
            surf.blit(s, (int(cx - size), int(cy - size)))

    def draw_bioluminescence(self, surf):
        if self.weather == "storm":
            return
        for _ in range(6):
            x = (self.time * 20 + random.randint(0, W)) % W
            y = SEA_LEVEL + random.randint(20, H - SEA_LEVEL - 20)
            sparkle = math.sin(self.time * 2 + x * 0.01 + y * 0.01) * 0.5 + 0.5
            if sparkle > 0.7:
                alpha = int((sparkle - 0.7) * 3 * 100)
                r = random.randint(2, 4)
                colors = [(0, 200, 255), (100, 255, 200), (200, 255, 100)]
                c = random.choice(colors)
                s = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, alpha), (r * 1.5, r * 1.5), r)
                pygame.draw.circle(s, (255, 255, 255, alpha // 2), (r * 1.5, r * 1.5), r * 2, 1)
                surf.blit(s, (int(x - r * 1.5), int(y - r * 1.5)))

    def draw_rain(self, surf, now):
        if self.weather != "storm" or self.storm_intensity < 0.3:
            return
        intensity = self.storm_intensity
        count = int(60 * intensity)
        for _ in range(count):
            rx = (now * 200 + random.randint(0, W * 2)) % W
            ry = random.randint(20, H - 20)
            length = 8 + 8 * intensity
            s = pygame.Surface((2, int(length)), pygame.SRCALPHA)
            s.fill((180, 200, 255, int(80 * intensity)))
            surf.blit(s, (int(rx), int(ry)))

    def draw_lightning(self, surf, now):
        if self.weather != "storm" or self.storm_intensity < 0.5:
            return
        flash = int(math.sin(now * 3.7) * math.sin(now * 5.3) * 100)
        if flash > 90:
            s = pygame.Surface((W, H), pygame.SRCALPHA)
            s.fill((255, 255, 255, int(flash - 90) * 2))
            surf.blit(s, (0, 0))

    def draw(self, surf):
        now = pygame.time.get_ticks() * 0.001

        # Storm intensity ramps up/down
        if self.weather == "storm":
            self.storm_intensity = min(1.0, self.storm_intensity + 0.002)
        else:
            self.storm_intensity = max(0.0, self.storm_intensity - 0.001)

        # deep water gradients - use tiled pre-rendered surface
        wg = self._water_gradient
        if wg:
            for tx in range(0, W, wg.get_width()):
                surf.blit(wg, (tx, SEA_LEVEL))
        else:
            for y in range(SEA_LEVEL, H):
                depth = (y - SEA_LEVEL) / (H - SEA_LEVEL)
                r = max(0, 8 - depth * 8)
                g = max(0, 80 - depth * 50)
                b = max(40, 180 - depth * 80)
                if depth < 0.3:
                    g += int(30 * (1 - depth / 0.3))
                    b += int(20 * (1 - depth / 0.3))
                pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (W, y))

        # Storm darkening overlay
        if self.weather == "storm" and self.storm_intensity > 0.1:
            overlay = pygame.Surface((W, H - SEA_LEVEL), pygame.SRCALPHA)
            overlay.fill((0, 0, 40, int(60 * self.storm_intensity)))
            surf.blit(overlay, (0, SEA_LEVEL))

        # seabed
        self.draw_seabed(surf)

        # school fish near seabed
        for f in self.school_fish:
            cx, cy = int(f["x"]), int(f["y"])
            sz = f["size"]
            c = f["color"]
            # fish body
            pygame.draw.ellipse(surf, c, (cx - sz, cy - sz // 2, sz * 2, sz))
            # tail
            tail_dir = 1 if f["vx"] > 0 else -1
            pygame.draw.polygon(surf, c, [
                (cx - tail_dir * sz, cy),
                (cx - tail_dir * sz - sz // 2, cy - sz // 2),
                (cx - tail_dir * sz - sz // 2, cy + sz // 2),
            ])
            # eye
            pygame.draw.circle(surf, (30, 30, 30), (cx + tail_dir * sz // 2, cy - 1), 1)

        # light rays (reduced in storm)
        ray_count = 9 if self.weather != "storm" else 3
        for i in range(ray_count):
            rx = 600 + math.sin(now * 0.2 + i * 2.5) * 300
            for j in range(8):
                alpha = int(20 - j * 2.5)
                if alpha <= 0:
                    continue
                x_off = math.sin(now * 0.4 + i * 0.6 + j * 0.4) * 25
                width = 10 + j * 6
                pts = [
                    (rx + x_off - width, SEA_LEVEL + j * 25),
                    (rx + x_off + width, SEA_LEVEL + j * 25),
                    (rx + x_off + width + 8, SEA_LEVEL + (j + 1) * 25),
                    (rx + x_off - width - 8, SEA_LEVEL + (j + 1) * 25),
                ]
                s = pygame.Surface((W, H), pygame.SRCALPHA)
                storm_dark = 1.0 - self.storm_intensity * 0.6
                c = (int(220 * storm_dark), int(240 * storm_dark), 255, alpha)
                pygame.draw.polygon(s, c, pts)
                surf.blit(s, (0, 0))

        # caustics
        self.draw_caustics(surf, now)

        # bioluminescence
        self.draw_bioluminescence(surf)

        # wave surface with foam edge
        pts = [(0, H)]
        for x in range(-10, W + 20, 4):
            y = self.get_y(x)
            pts.append((x, y))
        pts.append((W, H))
        wave_surf = pygame.Surface((W, H - SEA_LEVEL + 20), pygame.SRCALPHA)
        wave_color = (30, 130, 190, 130)
        if self.weather == "storm":
            wave_color = (20, 60, 110, 160)
        pygame.draw.polygon(wave_surf, wave_color, [(x, y - SEA_LEVEL + 10) for (x, y) in pts])
        surf.blit(wave_surf, (0, SEA_LEVEL - 10))

        # golden sunset reflections on water
        if self.weather != "storm":
            for i in range(25):
                rx = (self.time * 15 + i * 37 + math.sin(self.time * 0.3 + i) * 20) % W
                ry = self.get_y(rx) - 2
                shimmer = 0.5 + 0.5 * math.sin(self.time * 2 + i * 0.7)
                alpha = int(35 + 25 * shimmer)
                thickness = 1 + int(shimmer * 1.5)
                s = pygame.Surface((thickness * 6, thickness), pygame.SRCALPHA)
                gold = (255, int(180 + 50 * shimmer), int(60 + 40 * shimmer), alpha)
                pygame.draw.line(s, gold, (0, thickness // 2), (s.get_width(), thickness // 2), thickness)
                surf.blit(s, (rx, ry))

        # wave crests / foam
        foam_threshold = 0.65 if self.weather != "storm" else 0.45
        for x in range(0, W, 4):
            y = self.get_y(x)
            foam = (math.sin(x * 0.035 + self.time * 3.5) * 0.5 + 0.5)
            if foam > foam_threshold:
                alpha = int((foam - foam_threshold) * 3.5 * 200)
                alpha = min(alpha, 180)
                size = 3 + int(foam * 4)
                s = pygame.Surface((size, size), pygame.SRCALPHA)
                s.fill((255, 255, 255, alpha))
                surf.blit(s, (x, y - 2))
            elif foam > foam_threshold - 0.25 and self.weather != "storm":
                alpha = int((foam - 0.4) * 3 * 50)
                s = pygame.Surface((2, 2), pygame.SRCALPHA)
                s.fill((255, 255, 255, alpha))
                surf.blit(s, (x, y))

        # specular highlights (reduced in storm)
        spec_count = 18 if self.weather != "storm" else 4
        for i in range(spec_count):
            hx = (now * 35 + i * 73 + math.sin(now * 0.5 + i) * 30) % W
            hy = self.get_y(hx) - 3
            shimmer = math.sin(now * 2.5 + i * 0.7) * 0.5 + 0.5
            alpha = int(30 + 40 * shimmer)
            size = 4 + int(shimmer * 4)
            s = pygame.Surface((size, size // 2 + 1), pygame.SRCALPHA)
            s.fill((255, 255, 240, alpha))
            surf.blit(s, (hx, hy))

        # distant wave horizon line
        for x in range(0, W, 20):
            y = self.get_y(x)
            alpha_h = int(30 + 20 * math.sin(x * 0.01 + self.time * 0.5))
            s = pygame.Surface((20, 2), pygame.SRCALPHA)
            s.fill((180, 200, 255, alpha_h))
            surf.blit(s, (x, y - 6))

        # rain
        self.draw_rain(surf, now)

        # lightning
        self.draw_lightning(surf, now)

# ── Luxury Boat ─────────────────────────────────────────────────────────────
class LuxuryBoat:
    def __init__(self, player_id=0):
        self.player_id = player_id
        if player_id == 0:
            self.x = W // 2 - 80
            self.sail_color = (235, 245, 250)
            self.sail_highlight = (200, 225, 240)
            self.accent_color = (50, 150, 200)
            self.flag_colors = [(50, 150, 200), (100, 200, 240)]
            self.trim_color = (50, 120, 180)
        else:
            self.x = W // 2 + 80
            self.sail_color = (250, 235, 215)
            self.sail_highlight = (240, 210, 180)
            self.accent_color = (200, 100, 50)
            self.flag_colors = [(200, 100, 50), (240, 160, 80)]
            self.trim_color = (180, 80, 40)
        self.y = SEA_LEVEL - 74
        self.speed = 4.5
        self.hp = 120
        self.max_hp = 120
        self.angle = 0
        self.target_angle = 0
        self.bob = 0
        self.wake_particles = []
        self.wake_timer = 0
        self.score = 0
        self.gold = 0
        self.fish_count = 0
        self.current_weapon = 0
        self.caught_fish_values = []
        self.fish_on_deck = []
        self.fish_animations = []
        self.defense = 0
        self.weapon_dmg_bonus = 0
        self.range_bonus = 0
        self.luck_bonus = 0
        self.sx = 4.0
        self.sy = 2.0
        self.deck_y = 0
        self.cargo_crates = []
        self._init_deck_decor()

    def update(self, keys_left, keys_right, keys_up, keys_down, ocean):
        dx = dy = 0
        if keys_left:
            dx = -self.speed
        if keys_right:
            dx = self.speed
        if keys_up:
            dy = -self.speed * 0.7
        if keys_down:
            dy = self.speed * 0.7

        self.x += dx
        self.y += dy
        self.x = max(80, min(W - 80, self.x))
        self.y = max(SEA_LEVEL - 230, min(SEA_LEVEL - 15, self.y))

        self.bob = 7 * math.sin(ocean.time * 2.5 + self.x * 0.04)
        self.target_angle = -dx * 0.025
        self.angle = lerp(self.angle, self.target_angle, 0.08)

        # wake
        if abs(dx) > 1 or abs(dy) > 1:
            self.wake_timer += 1
            if self.wake_timer % 3 == 0:
                for side in [-1, 1]:
                    wx = self.x + side * 45 * math.cos(self.angle)
                    wy = self.y + self.bob + 15
                    self.wake_particles.append({
                        "x": wx, "y": wy,
                        "vx": -dx * 0.05 + side * random.uniform(-0.3, -0.1),
                        "vy": random.uniform(0.1, 0.4),
                        "life": 40, "max_life": 40, "size": random.uniform(2, 5)
                    })
        self.wake_particles = [p for p in self.wake_particles if p["life"] > 0]
        for p in self.wake_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            p["size"] *= 0.97

    def _init_deck_decor(self):
        for _ in range(6):
            self.cargo_crates.append({
                "x": random.uniform(-self.sx * 20, self.sx * 20),
                "y": random.uniform(-6, -3) * self.sy,
                "w": random.uniform(18, 28) * self.sx * 0.25,
                "h": random.uniform(14, 20) * self.sy * 0.25,
                "color": random.choice([(130, 80, 40), (150, 100, 50), (110, 70, 35), (160, 120, 60)]),
            })

    def get_pos(self):
        return (self.x, self.y + self.bob)

    def draw(self, surf):
        cx, cy = self.x, self.y + self.bob
        now = pygame.time.get_ticks() * 0.001
        sx, sy = self.sx, self.sy

        r = lambda dx, dy: (
            cx + dx * sx * math.cos(self.angle) - dy * sy * math.sin(self.angle),
            cy + dx * sx * math.sin(self.angle) + dy * sy * math.cos(self.angle),
        )
        def rp(dx, dy):
            return (cx + dx * sx, cy + dy * sy)

        # wake
        for p in self.wake_particles:
            alpha = int(180 * p["life"] / p["max_life"])
            s = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
            surf.blit(s, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))

        # bow spray (wave hitting the hull)
        spray_count = 3 + int(4 * abs(math.sin(now * 2.5)))
        for i in range(spray_count):
            sx_ = 65 + random.uniform(-3, 3)
            sy_ = 30 + random.uniform(-2, 6)
            sp = r(sx_, sy_)
            spray_alpha = int(80 + 60 * random.random())
            spray_size = random.uniform(2, 5) * sx * 0.15
            s = pygame.Surface((int(spray_size * 2), int(spray_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, spray_alpha), (int(spray_size), int(spray_size)), int(spray_size))
            surf.blit(s, (int(sp[0] - spray_size), int(sp[1] - spray_size)))

        # Main Hull (much larger)
        hull_pts = [
            r(-70, 8), r(-65, 30),
            r(-30, 42), r(30, 42),
            r(65, 30), r(70, 8),
            r(60, 2), r(-60, 2),
        ]
        pygame.draw.polygon(surf, (100, 50, 20), hull_pts)
        pygame.draw.polygon(surf, (60, 30, 10), hull_pts, 2)
        # decorative strip
        strip = [r(-55, 16), r(55, 16), r(50, 22), r(-50, 22)]
        pygame.draw.polygon(surf, (180, 120, 40), strip)
        # hull carvings
        for xx in range(-45, 46, 10):
            for yy in [20, 28]:
                dx_ = xx + 5 * math.sin(xx * 0.2)
                dy_ = yy + 2 * math.sin(yy * 0.3)
                p = r(dx_, dy_)
                pygame.draw.circle(surf, (60, 30, 10), (int(p[0]), int(p[1])), int(2 * sx * 0.3))

        # Main Deck (very large)
        deck_pts = [r(-60, 2), r(60, 2), r(55, -12), r(-55, -12)]
        pygame.draw.polygon(surf, (180, 140, 80), deck_pts)
        pygame.draw.polygon(surf, (120, 90, 50), deck_pts, 1)

        # Wooden planks on deck
        plank_count = int(12 * sx)
        for i in range(plank_count):
            py = lerp(2, -12, i / plank_count)
            shade = 160 + int(20 * math.sin(i * 1.3))
            for j in range(-58, 59, 2):
                p1 = r(j, py)
                p2 = r(j + 1, py - 0.08)
                pygame.draw.line(surf, (shade, shade - 20, shade - 40), p1, p2, 1)
        # plank edge lines
        for i in range(plank_count):
            py = lerp(2, -12, i / plank_count)
            p1 = r(-58, py)
            p2 = r(58, py)
            pygame.draw.line(surf, (100, 70, 30), p1, p2, 1)

        # Railings (left side)
        for post_x in range(-55, -25, 5):
            p_top = r(post_x, -14)
            p_bot = r(post_x, 2)
            pygame.draw.line(surf, (80, 50, 20), p_top, p_bot, int(1.5))
        railing_top_l = [r(x, -14) for x in range(-55, -20, 5)]
        if railing_top_l:
            pygame.draw.lines(surf, (60, 35, 15), False, railing_top_l, 2)

        # Railings (right side)
        for post_x in range(25, 56, 5):
            p_top = r(post_x, -14)
            p_bot = r(post_x, 2)
            pygame.draw.line(surf, (80, 50, 20), p_top, p_bot, int(1.5))
        railing_top_r = [r(x, -14) for x in range(25, 56, 5)]
        if railing_top_r:
            pygame.draw.lines(surf, (60, 35, 15), False, railing_top_r, 2)

        # Cargo crates on deck
        for crate in self.cargo_crates:
            crx, cry = crate["x"], crate["y"] + 1
            crw, crh = crate["w"], crate["h"]
            cc = crate["color"]
            c_pts = [r(crx - crw / sx, cry), r(crx + crw / sx, cry),
                     r(crx + crw / sx, cry - crh / sy), r(crx - crw / sx, cry - crh / sy)]
            pygame.draw.polygon(surf, cc, c_pts)
            pygame.draw.polygon(surf, (60, 30, 10), c_pts, 1)
            # cross bands
            pygame.draw.line(surf, (40, 20, 5), r(crx - crw / sx, cry - crh * 0.5 / sy),
                            r(crx + crw / sx, cry - crh * 0.5 / sy), 2)

        # Water barrel
        bcx, bcy = -30, -5
        bar_rx, bar_ry = 14 * sx, 10 * sy
        barrel_pts = [r(bcx - 14, bcy + 6), r(bcx + 14, bcy + 6),
                      r(bcx + 12, bcy - 4), r(bcx - 12, bcy - 4)]
        pygame.draw.polygon(surf, (120, 80, 40), barrel_pts)
        pygame.draw.polygon(surf, (80, 50, 20), barrel_pts, 2)
        for by in [-1, 3]:
            band = [r(bcx - 13, bcy + by), r(bcx + 13, bcy + by)]
            pygame.draw.line(surf, (60, 60, 60), band[0], band[1], 2)
        # fish visible inside barrel
        for fi in self.fish_on_deck[-3:]:
            fx = bcx + fi["ox"] * 0.3
            fy = bcy + fi["oy"] * 0.3
            fp = r(fx, fy)
            c = fi["color"]
            pygame.draw.ellipse(surf, c, (fp[0] - 5, fp[1] - 4, 10, 8))
            pygame.draw.circle(surf, (255, 255, 255), (int(fp[0] + 3), int(fp[1] - 1)), 2)
            pygame.draw.circle(surf, (0, 0, 0), (int(fp[0] + 3), int(fp[1] - 1)), 1)

        # Fish falling animation
        barrel_cx_real = cx + bcx * sx
        barrel_cy_real = cy + bcy * sy
        for anim in self.fish_animations[:]:
            anim["t"] += 0.05
            if anim["t"] >= 1:
                self.fish_animations.remove(anim)
                continue
            fx = lerp(anim["sx"], barrel_cx_real, anim["t"])
            fy = lerp(anim["sy"], barrel_cy_real, anim["t"]) - 20 * math.sin(anim["t"] * math.pi)
            fp = r((fx - cx) / sx, (fy - cy) / sy)
            c = anim["color"]
            alpha = int(255 * (1 - anim["t"] * 0.3))
            s = pygame.Surface((10, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*c, alpha), (0, 0, 10, 8))
            pygame.draw.circle(s, (255, 255, 255, alpha), (7, 2), 2)
            surf.blit(s, (int(fp[0] - 5), int(fp[1] - 4)))
            if anim["t"] < 0.3:
                sp = r((fx - cx) / sx + random.randint(-1, 1) * 0.5,
                       (fy - cy) / sy + random.randint(-1, 1) * 0.5)
                s2 = pygame.Surface((3, 3), pygame.SRCALPHA)
                s2.fill((255, 255, 200, 150))
                surf.blit(s2, (int(sp[0]), int(sp[1])))

        # Compass on deck
        comp_cx, comp_cy = 35, -8
        comp_base = r(comp_cx, comp_cy)
        # pedestal
        pygame.draw.line(surf, (60, 30, 10), r(comp_cx, comp_cy), r(comp_cx, comp_cy + 3), 3)
        # compass circle
        c_size = 6 * sx * 0.5
        pygame.draw.circle(surf, (200, 180, 120), (int(comp_base[0]), int(comp_base[1])), int(c_size))
        pygame.draw.circle(surf, (100, 80, 40), (int(comp_base[0]), int(comp_base[1])), int(c_size), 1)
        # compass needle
        needle_len = c_size * 0.7
        na = now * 0.3
        nx1 = comp_base[0] + math.cos(na) * needle_len
        ny1 = comp_base[1] + math.sin(na) * needle_len
        nx2 = comp_base[0] - math.cos(na) * needle_len
        ny2 = comp_base[1] - math.sin(na) * needle_len
        pygame.draw.line(surf, (200, 50, 50), (int(nx1), int(ny1)), (int(comp_base[0]), int(comp_base[1])), 2)
        pygame.draw.line(surf, (50, 50, 50), (int(comp_base[0]), int(comp_base[1])), (int(nx2), int(ny2)), 2)

        # Ropes between masts
        mmx, mmy = 0, -55
        smx, smy = 30, -40
        rope_segments = 12
        for i in range(rope_segments + 1):
            t = i / rope_segments
            rx = lerp(mmx, smx, t)
            ry = lerp(mmy, smy, t) + 3 * math.sin(t * math.pi * 3 + now * 2)
            rp_pt = r(rx, ry)
            pygame.draw.circle(surf, (120, 100, 70), (int(rp_pt[0]), int(rp_pt[1])),
                             int(1.5 + 1.5 * (1 - abs(t - 0.5) * 2)))
        # Rope from main mast to railing
        for rx, ry in [(0, -50), (-50, -10)]:
            rp_pt = r(rx, ry)
            rp_pt2 = r(rx + math.sin(now * 1.5) * 3, ry + 3)
            pygame.draw.line(surf, (120, 100, 70), rp_pt, rp_pt2, 2)

        # Cabin / main structure (scaled)
        cabin_pts = [r(-28, -10), r(28, -10), r(25, -42), r(-25, -42)]
        pygame.draw.polygon(surf, (130, 70, 30), cabin_pts)
        pygame.draw.polygon(surf, (80, 40, 20), cabin_pts, 2)
        # cabin windows
        for wx in [-12, 0, 12]:
            wp = r(wx, -24)
            pygame.draw.rect(surf, (60, 30, 15), (wp[0] - 6, wp[1] - 6, 12, 14))
            pygame.draw.rect(surf, (200, 230, 255), (wp[0] - 5, wp[1] - 5, 10, 8))
        # cabin roof
        roof_pts = [r(-32, -42), r(32, -42), r(28, -48), r(-28, -48)]
        pygame.draw.polygon(surf, (80, 40, 20), roof_pts)

        # Upper deck
        upper_pts = [r(-20, -48), r(20, -48), r(15, -55), r(-15, -55)]
        pygame.draw.polygon(surf, (160, 120, 70), upper_pts)

        # Wheel on upper deck
        wheel_cx, wheel_cy = 0, -52
        wheel_center = r(wheel_cx, wheel_cy)
        w_r = 6 * sx * 0.4
        for i in range(8):
            a = math.radians(i * 45 + now * 20)
            wx_ = wheel_cx + math.cos(a) * w_r / sx
            wy_ = wheel_cy + math.sin(a) * w_r / sy
            wp_ = r(wx_, wy_)
            pygame.draw.line(surf, (80, 50, 20), wheel_center, wp_, 2)
        pygame.draw.circle(surf, (60, 35, 15), (int(wheel_center[0]), int(wheel_center[1])), int(w_r * 0.5))
        pygame.draw.circle(surf, (100, 60, 30), (int(wheel_center[0]), int(wheel_center[1])), int(w_r), 1)

        # Main mast
        mmx, mmy = 0, -55
        p1 = r(mmx, mmy)
        p2 = r(mmx, mmy - 90)
        pygame.draw.line(surf, (50, 30, 10), p1, p2, int(5 * sx * 0.15))
        # crossbeam
        pygame.draw.line(surf, (50, 30, 10), r(mmx - 30, mmy - 30), r(mmx + 30, mmy - 30), int(3 * sx * 0.15))

        # Main sail (much larger)
        sail_pts = [r(mmx + 2, mmy - 85), r(mmx + 50, mmy - 30),
                    r(mmx + 45, mmy - 8), r(mmx + 2, mmy - 10)]
        pygame.draw.polygon(surf, self.sail_color, sail_pts)
        pygame.draw.polygon(surf, self.sail_highlight, sail_pts, 1)
        for i in range(3):
            py = lerp(-70, -15, i / 3)
            px1 = lerp(2, 7, i / 3)
            px2 = lerp(45, 35, i / 3)
            stripe_col = self.trim_color if i % 2 == 0 else self.sail_highlight
            pygame.draw.line(surf, stripe_col, r(px1, py), r(px2, py), 2)

        # Second mast
        smx, smy = 30, -40
        pygame.draw.line(surf, (50, 30, 10), r(smx, smy), r(smx, smy - 60), int(3 * sx * 0.15))
        ssail_pts = [r(smx + 1, smy - 57), r(smx + 30, smy - 20),
                     r(smx + 28, smy - 5), r(smx + 1, smy - 8)]
        pygame.draw.polygon(surf, self.sail_color, ssail_pts)
        pygame.draw.polygon(surf, self.sail_highlight, ssail_pts, 1)
        pygame.draw.line(surf, self.trim_color, r(smx + 1, smy - 35), r(smx + 28, smy - 15), 2)

        # Rigging ropes
        for (x1, y1, x2, y2) in [(mmx, mmy - 85, smx, smy - 55),
                                  (mmx, mmy - 60, smx, smy - 30),
                                  (mmx, mmy - 10, smx, smy - 5)]:
            for i in range(5):
                t = i / 4
                rx_ = lerp(x1, x2, t)
                ry_ = lerp(y1, y2, t) + 2 * math.sin(t * math.pi * 2 + now * 2)
                pygame.draw.circle(surf, (100, 80, 50), (int(r(rx_, ry_)[0]), int(r(rx_, ry_)[1])), 1)

        # Flags
        for fx, fy, col in [(mmx, mmy - 90, self.flag_colors[0]),
                            (smx, smy - 60, self.flag_colors[1])]:
            fp1 = r(fx, fy)
            fp2 = r(fx + 18, fy + 6)
            fp3 = r(fx, fy + 12)
            pygame.draw.polygon(surf, col, [fp1, fp2, fp3])

        # Lanterns
        for lx, ly in [(-40, -20), (40, -20)]:
            lp = r(lx, ly)
            glow = pygame.Surface((24, 24), pygame.SRCALPHA)
            alpha = int(60 + 40 * math.sin(now * 5))
            pygame.draw.circle(glow, (255, 200, 50, alpha), (12, 12), 12)
            surf.blit(glow, (int(lp[0] - 12), int(lp[1] - 12)))
            pygame.draw.circle(surf, (255, 180, 50), (int(lp[0]), int(lp[1])), int(4 * sx * 0.3))
            pygame.draw.circle(surf, (255, 255, 200), (int(lp[0]), int(lp[1])), int(2 * sx * 0.3))

        # Bow figurehead
        fh = r(68, 4)
        pygame.draw.circle(surf, (200, 180, 140), (int(fh[0]), int(fh[1])), int(6 * sx * 0.3))
        for i in range(3):
            a = math.radians(i * 40 - 20)
            ex = fh[0] + math.cos(a) * 10 * sx * 0.3
            ey = fh[1] + math.sin(a) * 4 * sy * 0.3
            pygame.draw.line(surf, (200, 180, 140), (int(fh[0]), int(fh[1])), (int(ex), int(ey)), 2)

        # Stern decoration
        sh = r(-68, 6)
        pygame.draw.arc(surf, (180, 120, 40), (sh[0] - 12, sh[1] - 8, 14, 16), 0.5, 2.5, 3)

        # Pennant
        for i in range(3):
            pp = r(55 + i * 5, -5 + math.sin(i * 0.5) * 3)
            pygame.draw.circle(surf, self.accent_color, (int(pp[0]), int(pp[1])),
                             int(3 * sx * 0.3))

        # HP bar (scaled)
        bar_w = int(80 * sx * 0.3)
        bar_h = int(7 * sy * 0.5)
        bx, by = int(cx - bar_w // 2), int(cy + 48 * sy * 0.5)
        pygame.draw.rect(surf, (30, 30, 30), (bx, by, bar_w, bar_h), 0, 3)
        hp_w = int(bar_w * self.hp / self.max_hp)
        if self.hp > 50:
            hp_color = (50, 200, 80)
        elif self.hp > 25:
            hp_color = (220, 200, 40)
        else:
            hp_color = (220, 40, 40)
        pygame.draw.rect(surf, hp_color, (bx + 1, by + 1, max(0, hp_w - 2), bar_h - 2), 0, 2)
        pygame.draw.rect(surf, (180, 140, 60), (bx, by, bar_w, bar_h), 1, 3)

    def rect(self):
        return pygame.Rect(self.x - 70 * self.sx, self.y - 90 * self.sy, 140 * self.sx, 150 * self.sy)

# ── Particle ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, vel=None, life=30, size=4):
        self.x, self.y = x, y
        self.color = color
        self.vx = vel[0] if vel else random.uniform(-2, 2)
        self.vy = vel[1] if vel else random.uniform(-2, 2)
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1
        self.size *= 0.97

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        s = int(max(1, self.size))
        sfc = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(sfc, (*self.color[:3], alpha), (s, s), s)
        surf.blit(sfc, (int(self.x - s), int(self.y - s)))

# ── Enhanced Particles ─────────────────────────────────────────────────────────
class SplashParticle(Particle):
    def __init__(self, x, y, color=None, vel=None, life=20, size=4):
        if color is None:
            color = (200, 220, 255)
        super().__init__(x, y, color, vel, life, size)
        self.vy = vel[1] if vel else random.uniform(-3, -0.5)

    def update(self):
        super().update()
        self.vx *= 0.98

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        s = int(max(1, self.size))
        sfc = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(sfc, (*self.color[:3], alpha), (s, s), s)
        pygame.draw.circle(sfc, (255, 255, 255, alpha // 2), (s, s), s // 2)
        surf.blit(sfc, (int(self.x - s), int(self.y - s)))

class CoinParticle(Particle):
    def __init__(self, x, y, target_x, target_y, value=0):
        super().__init__(x, y, (255, 215, 0), life=40, size=5)
        self.tx, self.ty = target_x, target_y
        self.value = value
        self.progress = 0

    def update(self):
        self.progress += 0.03
        if self.progress < 1:
            self.x = lerp(self.x, self.tx, 0.08)
            self.y = lerp(self.y, self.ty, 0.08) - 15 * math.sin(self.progress * math.pi)
        self.life -= 1
        self.size = max(1, self.size * 0.97)

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int(255 * self.life / self.max_life)
        s = int(max(2, self.size))
        sfc = pygame.Surface((s * 3, s * 3), pygame.SRCALPHA)
        # coin shape
        pygame.draw.circle(sfc, (255, 215, 0, alpha), (s * 1.5, s * 1.5), s)
        pygame.draw.circle(sfc, (255, 255, 200, alpha), (s * 1.5, s * 1.5), s - 1)
        pygame.draw.circle(sfc, (255, 215, 0, alpha), (s * 1.5, s * 1.5), s - 2, 1)
        surf.blit(sfc, (int(self.x - s * 1.5), int(self.y - s * 1.5)))

class LevelUpEffect:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t = 0
        self.max_t = 60
        self.rings = []

    def update(self):
        self.t += 1
        if self.t <= 45 and self.t % 5 == 0:
            self.rings.append({"r": 5, "alpha": 255, "speed": random.uniform(2, 4)})
        for r in self.rings[:]:
            r["r"] += r["speed"]
            r["alpha"] -= 6
            if r["alpha"] <= 0:
                self.rings.remove(r)

    @property
    def alive(self):
        return self.t < self.max_t or len(self.rings) > 0

    def draw(self, surf):
        t = self.t
        # central flash
        if t < 20:
            flash_r = 5 + t * 2
            flash_alpha = max(0, 200 - t * 10)
            s = pygame.Surface((int(flash_r * 2), int(flash_r * 2)), pygame.SRCALPHA)
            c = (255, 215, 0, flash_alpha)
            pygame.draw.circle(s, c, (int(flash_r), int(flash_r)), int(flash_r))
            c2 = (255, 255, 255, flash_alpha // 2)
            pygame.draw.circle(s, c2, (int(flash_r), int(flash_r)), int(flash_r * 0.6))
            surf.blit(s, (int(self.x - flash_r), int(self.y - flash_r)))
        # expanding rings
        for r in self.rings:
            s = pygame.Surface((int(r["r"] * 2), int(r["r"] * 2)), pygame.SRCALPHA)
            col = (255, 215, 0, max(0, r["alpha"]))
            pygame.draw.circle(s, col, (int(r["r"]), int(r["r"])), int(r["r"]), 2)
            surf.blit(s, (int(self.x - r["r"]), int(self.y - r["r"])))
        # sparkles
        if t < 40:
            for i in range(3):
                a = t * 0.3 + i * 2.1
                sx = self.x + math.cos(a) * (10 + t * 0.8)
                sy = self.y + math.sin(a) * (8 + t * 0.6)
                sparkle = pygame.Surface((3, 3), pygame.SRCALPHA)
                sparkle.fill((255, 255, 200, max(0, 200 - t * 5)))
                surf.blit(sparkle, (int(sx), int(sy)))

# ── Projectile (mouse-aimed) ─────────────────────────────────────────────────
class Projectile:
    def __init__(self, x, y, target_x, target_y, weapon, owner_id=None):
        self.x, self.y = x, y
        self.weapon = weapon
        self.color = weapon["color"]
        self.speed = weapon["speed"]
        self.dmg = weapon["dmg"]
        self.range = weapon["range"]
        self.dist_traveled = 0
        self.hit = False
        self.splash = weapon.get("splash", 0)
        self.owner_id = owner_id
        dx = target_x - self.x
        dy = target_y - self.y
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d * self.speed
        self.vy = dy / d * self.speed

    def update(self, monsters, fish_list=None, animals=None):
        self.x += self.vx
        self.y += self.vy
        self.dist_traveled += self.speed
        if self.dist_traveled > self.range:
            return ("expired", None)
        # check monster collision
        for m in monsters:
            if not m.alive:
                continue
            if dist((self.x, self.y), (m.x, m.y)) < m.size:
                m.hp -= self.dmg
                self.hit = True
                return ("hit", m)
        # if net, check fish and animal collision
        if self.weapon.get("catch"):
            if fish_list:
                for f in fish_list:
                    if not f.alive or f.caught:
                        continue
                    if dist((self.x, self.y), (f.x, f.y)) < f.size + 10:
                        f.caught = True
                        f.alive = False
                        self.hit = True
                        return ("fish", f)
            # net also catches animals
            if animals:
                for group in animals:
                    for a in group:
                        if not getattr(a, 'alive', False):
                            continue
                        if dist((self.x, self.y), (a.x, a.y)) < max(a.size, 15) + 10:
                            a.alive = False
                            self.hit = True
                            return ("animal", a)
        return (None, None)

    def draw(self, surf):
        now = pygame.time.get_ticks() * 0.001
        if self.weapon["name"] == "Cannon":
            # cannonball with fire trail
            pygame.draw.circle(surf, (30, 30, 30), (int(self.x), int(self.y)), 8)
            pygame.draw.circle(surf, (60, 60, 60), (int(self.x), int(self.y)), 6)
            pygame.draw.circle(surf, (255, 180, 50), (int(self.x), int(self.y)), 3)
            # fire/smoke trail
            for i in range(5):
                t = now * 5 + i
                alpha = int(80 - i * 15)
                r = 6 - i
                if alpha <= 0:
                    continue
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                trail_x = self.x - self.vx * (i + 1) * 2 + random.uniform(-1, 1)
                trail_y = self.y - self.vy * (i + 1) * 2 + random.uniform(-1, 1)
                col = (255, 150 + i * 20, 50, alpha) if i < 3 else (180, 180, 180, alpha // 2)
                pygame.draw.circle(s, col, (r, r), r)
                surf.blit(s, (int(trail_x - r), int(trail_y - r)))
            # wind resistance lines
            for i in range(2):
                wx = self.x - self.vx * 0.3 * (i + 1)
                wy = self.y - self.vy * 0.3 * (i + 1)
                pygame.draw.line(surf, (200, 200, 200, 40), (int(self.x), int(self.y)),
                                (int(wx), int(wy)), 1)
        elif self.weapon["name"] == "Net":
            # spinning net with radial lines
            cx, cy = int(self.x), int(self.y)
            pygame.draw.circle(surf, self.color, (cx, cy), 14, 2)
            pygame.draw.circle(surf, (255, 255, 255, 60), (cx, cy), 12, 1)
            for i in range(8):
                a = math.radians(i * 45 + now * 150)
                ex = cx + math.cos(a) * 15
                ey = cy + math.sin(a) * 15
                pygame.draw.line(surf, self.color, (cx, cy), (int(ex), int(ey)), 1)
            # cross-hatch
            for i in range(4):
                a1 = math.radians(i * 90 + now * 100)
                a2 = math.radians(i * 90 + 45 + now * 100)
                r1 = 8 + 4 * math.sin(now * 3 + i)
                ex1 = cx + math.cos(a1) * r1
                ey1 = cy + math.sin(a1) * r1
                ex2 = cx + math.cos(a2) * r1
                ey2 = cy + math.sin(a2) * r1
                pygame.draw.line(surf, (150, 220, 220, 80), (int(ex1), int(ey1)), (int(ex2), int(ey2)), 1)
        else:
            # harpoon with rope trail
            cx, cy = int(self.x), int(self.y)
            # rope
            dx, dy = self.x - self.vx * 6, self.y - self.vy * 6
            for i in range(5):
                frac = i / 5
                px = lerp(self.x, dx, frac) + math.sin(now * 10 + i) * 2
                py = lerp(self.y, dy, frac) + math.cos(now * 8 + i) * 2
                pygame.draw.circle(surf, (160, 140, 80, 150), (int(px), int(py)), 2)
            # harpoon tip
            pygame.draw.line(surf, (220, 200, 150), (cx, cy),
                            (int(cx - self.vx * 4), int(cy - self.vy * 4)), 4)
            pygame.draw.circle(surf, (255, 220, 100), (cx, cy), 4)
            pygame.draw.circle(surf, (255, 255, 200), (cx, cy), 2)
            # barb
            bx = cx - self.vx * 3
            by = cy - self.vy * 3
            perp_x, perp_y = -self.vy, self.vx
            d_perp = math.hypot(perp_x, perp_y) or 1
            perp_x /= d_perp
            perp_y /= d_perp
            for side in [-1, 1]:
                barb_x = bx + perp_x * side * 4
                barb_y = by + perp_y * side * 4
                pygame.draw.line(surf, (200, 180, 120), (int(bx), int(by)),
                                (int(barb_x), int(barb_y)), 2)

# ── ThrownFish (arc projectile) ──────────────────────────────────────────────
class ThrownFish:
    def __init__(self, x, y, target_x, target_y, value, owner_id):
        self.x, self.y = x, y
        self.value = value
        self.owner_id = owner_id
        self.alive = True
        self.hit_boat = False
        self.color = (255, 200, 50)
        dx = target_x - self.x
        dy = target_y - self.y
        d = math.hypot(dx, dy) or 1
        base_speed = 10
        self.vx = dx / d * base_speed
        self.vy = dy / d * base_speed - 6
        self.gravity = 0.3
        self.start_x, self.start_y = x, y
        self.total_dist = d
        self.dist_traveled = 0

    def update(self):
        self.x += self.vx
        self.vy += self.gravity
        self.y += self.vy
        self.dist_traveled += math.hypot(self.vx, self.vy)
        if self.y > SEA_LEVEL + 50 or self.dist_traveled > self.total_dist * 1.5:
            self.alive = False

    def check_hit_boat(self, boats):
        for b in boats:
            if b.player_id == self.owner_id:
                continue
            if dist((self.x, self.y), (b.x, b.y)) < 50:
                b.gold += self.value
                self.hit_boat = True
                self.alive = False
                return b
        return None

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # fish body
        pygame.draw.ellipse(surf, self.color, (cx - 8, cy - 5, 16, 10))
        pygame.draw.ellipse(surf, (255, 220, 100), (cx - 6, cy - 3, 12, 6))
        # tail
        tail_dir = 1 if self.vx > 0 else -1
        pygame.draw.polygon(surf, self.color, [
            (cx - tail_dir * 8, cy),
            (cx - tail_dir * 14, cy - 6),
            (cx - tail_dir * 14, cy + 6),
        ])
        # eye
        pygame.draw.circle(surf, (0, 0, 0), (cx + tail_dir * 4, cy - 1), 2)
        # arc trail
        for i in range(3):
            frac = (i + 1) * 0.15
            tx = self.x - self.vx * frac
            ty = self.y - self.vy * frac - self.gravity * frac * frac * 5
            alpha = 100 - i * 30
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            s.fill((255, 255, 200, alpha))
            surf.blit(s, (int(tx - 2), int(ty - 2)))

# ── Crosshair ─────────────────────────────────────────────────────────────────
class Crosshair:
    def __init__(self):
        self.x = W // 2
        self.y = H // 2

    def update(self, pos):
        self.x, self.y = pos

    def draw(self, surf, game=None):
        cx, cy = int(self.x), int(self.y)
        # range indicator (for current weapon)
        if game and not game.paused and not game.game_over:
            boat = game.boats[0]
            w = game.weapons[boat.current_weapon]
            d = dist((boat.x, boat.y), (cx, cy))
            in_range = d <= w["range"]
            range_color = (100, 255, 100, 40) if in_range else (255, 100, 100, 30)
            s = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.circle(s, range_color, (cx, cy), 18, 0)
            surf.blit(s, (0, 0))
            # range arc from boat to cursor
            if game.two_player and len(game.boats) > 1:
                bx2, by2 = game.boats[1].get_pos()
                w2 = game.weapons[game.boats[1].current_weapon]
                d2 = dist((bx2, by2), (cx, cy))
                in_range2 = d2 <= w2["range"]
                rc2 = (100, 255, 100, 30) if in_range2 else (255, 100, 100, 20)
                s2 = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.circle(s2, rc2, (cx, cy), 14, 0)
                surf.blit(s2, (0, 0))
        # outer circle
        pygame.draw.circle(surf, (255, 255, 255, 160), (cx, cy), 16, 1)
        pygame.draw.circle(surf, (255, 80, 80, 100), (cx, cy), 15, 1)
        # cross lines with gap
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            sx = cx + dx * 20
            sy = cy + dy * 20
            ex = cx + dx * 28
            ey = cy + dy * 28
            pygame.draw.line(surf, (255, 255, 255), (sx, sy), (ex, ey), 2)
        # tick marks
        for i in range(4):
            a = math.radians(i * 90 + 45)
            tx = cx + math.cos(a) * 20
            ty = cy + math.sin(a) * 20
            tx2 = cx + math.cos(a) * 24
            ty2 = cy + math.sin(a) * 24
            pygame.draw.line(surf, (200, 200, 200, 120), (int(tx), int(ty)), (int(tx2), int(ty2)), 1)
        # center dot with glow
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 3)
        pygame.draw.circle(surf, (255, 60, 60), (cx, cy), 2)
        # glow pulse
        pulse = 3 + 2 * math.sin(pygame.time.get_ticks() * 0.005)
        glow = pygame.Surface((int(pulse * 4), int(pulse * 4)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 100, 100, 40), (int(pulse * 2), int(pulse * 2)), int(pulse * 2))
        surf.blit(glow, (int(cx - pulse * 2), int(cy - pulse * 2)))

# ── Fish ─────────────────────────────────────────────────────────────────────
class Fish:
    def __init__(self, wave=1):
        if random.random() < 0.04 + wave * 0.005:
            ft = random.choice(RARE_FISH_TYPES)
            self.rare = True
        else:
            ft = random.choice(FISH_TYPES)
            self.rare = False
        self.name = ft["name"]
        self.color = ft["color"]
        self.size = ft["size"]
        self.value = ft["value"]
        self.speed = ft["speed"] + random.uniform(-0.5, 0.5)
        self.x = random.randint(50, W - 50)
        self.y = random.randint(int(SEA_LEVEL) + 20, H - 30)
        self.vx = random.choice([-1, 1]) * self.speed
        self.vy = 0
        self.caught = False
        self.alive = True
        self.wobble = random.uniform(0, math.pi * 2)
        self.flash = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.wobble += 0.05
        self.flash += 0.1
        self.x += self.vx
        self.vy = math.sin(self.wobble) * 0.5
        self.y += self.vy
        if self.x < 20 or self.x > W - 20:
            self.vx *= -1
        self.y = max(SEA_LEVEL + 10, min(H - 20, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        d = -1 if self.vx > 0 else 1
        cx, cy = int(self.x), int(self.y)
        # body
        body_rect = (cx - self.size, cy - self.size // 2, self.size * 2, self.size)
        pygame.draw.ellipse(surf, self.color, body_rect)
        # scale shimmer
        shimmer = int(60 + 40 * math.sin(self.flash))
        s = pygame.Surface((self.size, self.size // 2), pygame.SRCALPHA)
        s.fill((255, 255, 255, shimmer))
        surf.blit(s, (cx - self.size // 2, cy - self.size // 4))
        # tail
        tx = cx - d * self.size
        pygame.draw.polygon(surf, self.color, [
            (tx, cy), (tx - d * self.size // 2, cy - self.size // 2),
            (tx - d * self.size // 2, cy + self.size // 2),
        ])
        # dorsal fin
        pygame.draw.polygon(surf, self.color, [
            (cx, cy - self.size // 2), (cx + d * 3, cy - self.size),
            (cx + d * 6, cy - self.size // 2),
        ])
        # eye
        ex = cx + d * self.size // 3
        pygame.draw.circle(surf, (255, 255, 255), (ex, cy - 2), 3)
        pygame.draw.circle(surf, (0, 0, 0), (ex, cy - 2), 2)
        # mouth
        pygame.draw.circle(surf, (200, 100, 100), (cx + d * self.size - 2, cy), 2)

# ── Monster ──────────────────────────────────────────────────────────────────
class Monster:
    def __init__(self, wave=1):
        mt = random.choice(MONSTER_TYPES)
        self.name = mt["name"]
        self.color = mt["color"]
        scale = 1.0 + (wave - 1) * 0.25
        self.max_hp = int(mt["hp"] * scale)
        self.hp = self.max_hp
        self.base_dmg = mt["dmg"]
        self.dmg = int(mt["dmg"] * (1 + (wave - 1) * 0.15))
        self.reward = int(mt["reward"] * (1 + (wave - 1) * 0.2))
        self.size = mt["size"]
        self.x = random.choice([-90, W + 90])
        self.y = SEA_LEVEL + random.randint(10, 80)
        self.speed = random.uniform(1.5, 2.5 + wave * 0.2)
        self.alive = True
        self.attack_cooldown = 0
        self.float_offset = random.uniform(0, math.pi * 2)
        self.dir = -1 if self.x > 0 else 1
        self.vx = self.dir * self.speed

    def update(self, boats, ocean):
        if not self.alive:
            return
        self.float_offset += 0.03
        self.x += self.vx
        self.y = SEA_LEVEL + 30 + math.sin(self.float_offset) * 12
        self.x = max(-120, min(W + 120, self.x))
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        # attack nearest boat
        for b in boats:
            if dist((self.x, self.y), (b.x, b.y)) < self.size + 45:
                if self.attack_cooldown <= 0:
                    dmg_dealt = max(1, self.dmg - getattr(b, 'defense', 0))
                    b.hp -= dmg_dealt
                    self.attack_cooldown = 40
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        t = pygame.time.get_ticks() * 0.003

        if "Kraken" in self.name:
            # tentacles
            for i in range(8):
                a = math.radians(i * 45 + t * 20)
                tl = self.size * 0.7 + math.sin(t * 2 + i) * 10
                ex = cx + math.cos(a) * tl
                ey = cy + math.sin(a) * tl + 10
                # tapered
                for j in range(5):
                    frac = j / 5
                    px = lerp(cx, ex, frac)
                    py = lerp(cy, ey, frac)
                    r = int(self.size * 0.3 * (1 - frac * 0.7))
                    pygame.draw.circle(surf, (lerp(100, 60, frac), 0, lerp(70, 40, frac)),
                                     (int(px), int(py)), max(r, 2))
                # suckers
                if i % 2 == 0:
                    sx = lerp(cx, ex, 0.6)
                    sy = lerp(cy, ey, 0.6)
                    pygame.draw.circle(surf, (60, 0, 40), (int(sx), int(sy)), 3)
            # body
            pygame.draw.circle(surf, (80, 0, 60), (cx, cy), self.size // 2)
            pygame.draw.circle(surf, (120, 0, 80), (cx, cy), self.size // 3)
            # eyes
            for ex, ey in [(cx - 8, cy - 6), (cx + 8, cy - 6)]:
                pygame.draw.circle(surf, (255, 50, 50), (ex, ey), 6)
                pygame.draw.circle(surf, (0, 0, 0), (ex, ey), 3)

        elif "Serpent" in self.name:
            segs = 8
            for i in range(segs):
                sx = cx + math.sin(t + i * 0.5) * 18 - i * 8
                sy = cy + math.cos(t * 0.6 + i * 0.3) * 12 + math.sin(t + i) * 5
                r = self.size // 2 - i * 1.5
                c = (lerp(0, 20, i / segs), lerp(140, 80, i / segs), lerp(70, 40, i / segs))
                pygame.draw.circle(surf, c, (int(sx), int(sy)), max(int(r), 3))
                # scales
                if i < segs - 1:
                    nsx = cx + math.sin(t + (i + 1) * 0.5) * 18 - (i + 1) * 8
                    nsy = cy + math.cos(t * 0.6 + (i + 1) * 0.3) * 12 + math.sin(t + i + 1) * 5
                    pygame.draw.line(surf, (0, 180, 90), (int(sx), int(sy)), (int(nsx), int(nsy)), 3)
            # head
            hx = cx + math.sin(t) * 18
            hy = cy + math.cos(t * 0.6) * 12
            pygame.draw.circle(surf, (0, 160, 80), (int(hx), int(hy)), 10)
            pygame.draw.circle(surf, (255, 200, 50), (int(hx - 5), int(hy - 3)), 3)
            pygame.draw.circle(surf, (255, 200, 50), (int(hx + 5), int(hy - 3)), 3)
            pygame.draw.circle(surf, (0, 0, 0), (int(hx - 5), int(hy - 3)), 1)
            pygame.draw.circle(surf, (0, 0, 0), (int(hx + 5), int(hy - 3)), 1)

        elif "Shark" in self.name:
            # body
            pts = [(cx - self.size, cy), (cx + self.size - 12, cy - 10),
                   (cx + self.size, cy), (cx + self.size - 12, cy + 10)]
            pygame.draw.polygon(surf, (80, 80, 100), pts)
            # dorsal
            pygame.draw.polygon(surf, (60, 60, 90),
                               [(cx + 5, cy - 10), (cx + 10, cy - self.size // 2), (cx + 20, cy - 10)])
            # pectoral
            pygame.draw.polygon(surf, (60, 60, 90),
                               [(cx - 10, cy + 2), (cx - 20, cy + 12), (cx - 5, cy + 6)])
            # teeth
            for tx in range(-8, 12, 5):
                pygame.draw.polygon(surf, (255, 255, 255),
                                   [(cx + self.size - 8 + tx, cy - 4), (cx + self.size - 6 + tx, cy),
                                    (cx + self.size - 10 + tx, cy)])
            # eye
            pygame.draw.circle(surf, (255, 255, 255), (cx + 15, cy - 3), 4)
            pygame.draw.circle(surf, (30, 30, 30), (cx + 15, cy - 3), 2)
            # gills
            for g in range(3):
                pygame.draw.line(surf, (50, 50, 70), (cx - 10 + g * 3, cy - 4), (cx - 10 + g * 3, cy + 4), 1)

        elif "Ghost" in self.name:
            # ghostly glow
            for i in range(6):
                tt = t + i
                px = cx + math.sin(tt) * 25
                py = cy + math.cos(tt * 0.7) * 15 - i * 10
                r = self.size // 3 - i * 1
                alpha = 80 - i * 10
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 100, 160, max(alpha, 10)), (r, r), r)
                surf.blit(s, (int(px - r), int(py - r)))
            # hull
            hull = [(cx - 20, cy + 5), (cx - 18, cy + 20), (cx + 18, cy + 20), (cx + 20, cy + 5)]
            pygame.draw.polygon(surf, (50, 50, 80), hull)
            pygame.draw.polygon(surf, (80, 80, 110), hull, 1)
            # cabin
            cab = [(cx - 12, cy - 5), (cx + 12, cy - 5), (cx + 10, cy - 18), (cx - 10, cy - 18)]
            pygame.draw.polygon(surf, (40, 40, 70), cab)
            # ghostly windows
            for wx in [-5, 5]:
                pygame.draw.rect(surf, (150, 200, 255, 100), (cx + wx - 3, cy - 14, 6, 6))
            # mast
            pygame.draw.line(surf, (40, 40, 60), (cx, cy - 18), (cx, cy - 40), 3)
            # torn sail
            sail = [(cx + 2, cy - 38), (cx + 22, cy - 18), (cx + 2, cy - 5)]
            pygame.draw.polygon(surf, (80, 80, 120, 150), sail)
            # ghost eyes
            pygame.draw.circle(surf, (200, 220, 255), (cx - 4, cy - 10), 3)
            pygame.draw.circle(surf, (200, 220, 255), (cx + 4, cy - 10), 3)

        # HP bar
        bar_w = self.size
        bx = cx - bar_w // 2
        by = cy - self.size // 2 - 12
        pygame.draw.rect(surf, (40, 40, 40), (bx, by, bar_w, 5), 0, 2)
        hp_w = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surf, (220, 40, 40), (bx + 1, by + 1, max(0, hp_w - 2), 3), 0, 1)

# ── Treasure ─────────────────────────────────────────────────────────────────
class Treasure:
    def __init__(self, x, y, value=0):
        self.x = x
        self.y = y
        self.value = value if value > 0 else random.randint(20, 80)
        self.collected = False
        self.bob = random.uniform(0, math.pi * 2)
        self.sparkle = 0

    def update(self):
        self.bob += 0.04
        self.sparkle += 0.1

    def draw(self, surf):
        if self.collected:
            return
        cx, cy = int(self.x), int(self.y + math.sin(self.bob) * 5)
        # glow
        glow = pygame.Surface((40, 30), pygame.SRCALPHA)
        alpha = int(40 + 30 * math.sin(self.sparkle))
        pygame.draw.ellipse(glow, (255, 215, 0, alpha), (0, 0, 40, 30))
        surf.blit(glow, (cx - 20, cy - 15))
        # chest
        pygame.draw.rect(surf, (160, 120, 50), (cx - 14, cy - 9, 28, 18))
        pygame.draw.rect(surf, (200, 160, 70), (cx - 14, cy - 9, 28, 9))
        pygame.draw.rect(surf, (100, 80, 30), (cx - 14, cy - 9, 28, 18), 2)
        # lock
        pygame.draw.rect(surf, (220, 200, 120), (cx - 4, cy - 3, 8, 5))
        # gems
        gem_colors = [(255, 50, 50), (50, 255, 50), (50, 100, 255), (255, 255, 50)]
        for i, gc in enumerate(gem_colors):
            gx = cx - 8 + i * 5
            gy = cy + 2
            pygame.draw.circle(surf, gc, (gx, gy), 2)
        # sparkles
        for i in range(4):
            a = self.sparkle + i * 1.57
            sx = cx + math.cos(a) * 20
            sy = cy + math.sin(a) * 14 - 4
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            s.fill((255, 255, 200, int(200 + 55 * math.sin(self.sparkle * 2 + i))))
            surf.blit(s, (int(sx - 2), int(sy - 2)))

# ── Dolphin ──────────────────────────────────────────────────────────────────
class Dolphin:
    def __init__(self):
        self.x = random.randint(50, W - 50)
        self.y = SEA_LEVEL + random.randint(5, 35)
        self.vx = random.choice([-1, 1]) * random.uniform(2, 4)
        self.alive = True
        self.jump_timer = random.randint(60, 200)
        self.jumping = False
        self.jump_progress = 0
        self.jump_dir = 1 if self.vx > 0 else -1
        self.wobble = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.wobble += 0.04
        self.jump_timer -= 1
        if self.jump_timer <= 0 and not self.jumping:
            self.jumping = True
            self.jump_progress = 0
            self.jump_timer = random.randint(120, 300)
        if self.jumping:
            self.jump_progress += 0.04
            arc = math.sin(self.jump_progress * math.pi)
            self.y = SEA_LEVEL - 30 * arc
            self.x += self.vx * 1.5
            if self.jump_progress >= 1:
                self.jumping = False
                self.y = SEA_LEVEL + random.randint(5, 20)
        else:
            self.x += self.vx
            self.y += math.sin(self.wobble) * 0.3
        if self.x < 20 or self.x > W - 20:
            self.vx *= -1
            self.jump_dir *= -1
        self.y = max(SEA_LEVEL - 35, min(SEA_LEVEL + 40, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        d = self.jump_dir
        body_color = (70, 145, 210)
        highlight = (100, 180, 240)
        # body (more organic shape)
        body = [(cx - 24, cy + 1), (cx - 14, cy - 9), (cx + 2, cy - 10),
                (cx + 16, cy - 7), (cx + 24, cy - 1), (cx + 26, cy + 1),
                (cx + 24, cy + 3), (cx + 16, cy + 6), (cx + 2, cy + 8),
                (cx - 14, cy + 7), (cx - 24, cy + 3)]
        pygame.draw.polygon(surf, body_color, body)
        pygame.draw.polygon(surf, highlight, body, 1)
        # belly gradient
        belly = [(cx - 18, cy + 1), (cx - 8, cy + 5), (cx + 8, cy + 4), (cx + 16, cy + 2)]
        pygame.draw.polygon(surf, (190, 220, 245), belly)
        # dorsal fin (more curved)
        dorsal = [(cx - 3, cy - 9), (cx + 4, cy - 19), (cx + 10, cy - 10)]
        pygame.draw.polygon(surf, (60, 130, 200), dorsal)
        pygame.draw.polygon(surf, highlight, dorsal, 1)
        # tail flukes (more realistic)
        fluke = [(cx - 24, cy), (cx - 34, cy - 10), (cx - 30, cy), (cx - 34, cy + 10)]
        pygame.draw.polygon(surf, body_color, fluke)
        pygame.draw.polygon(surf, highlight, fluke, 1)
        # pectoral fin
        pec = [(cx + 2, cy + 2), (cx - 8, cy + 10), (cx - 2, cy + 6)]
        pygame.draw.polygon(surf, (60, 130, 200), pec)
        # beak / rostrum
        beak = [(cx + 24, cy - 1), (cx + 32, cy - 3), (cx + 34, cy + 1), (cx + 32, cy + 3)]
        pygame.draw.polygon(surf, (90, 160, 220), beak)
        pygame.draw.polygon(surf, highlight, beak, 1)
        # eye detail
        pygame.draw.circle(surf, (255, 255, 255), (cx + 18, cy - 2), 4)
        pygame.draw.circle(surf, (20, 20, 30), (cx + 18, cy - 2), 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 17, cy - 3), 1)
        # smile line
        pygame.draw.arc(surf, (50, 110, 170), (cx + 20, cy - 1, 10, 6), 0.1, 2.8, 1)

        # splash effects when jumping
        if self.jumping:
            if self.jump_progress < 0.3:
                for i in range(5):
                    sx = cx + random.randint(-20, 20)
                    sy = SEA_LEVEL + random.randint(-2, 6)
                    sz = random.randint(2, 6)
                    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
                    alpha = random.randint(100, 200)
                    s.fill((255, 255, 255, alpha))
                    surf.blit(s, (sx, sy))
            # water droplets
            if 0.2 < self.jump_progress < 0.7:
                for i in range(3):
                    dx = cx + random.randint(-12, 12)
                    dy = SEA_LEVEL - random.randint(2, 10) - int(math.sin(self.jump_progress * math.pi) * 20)
                    s = pygame.Surface((2, 3), pygame.SRCALPHA)
                    s.fill((200, 230, 255, random.randint(80, 160)))
                    surf.blit(s, (dx, dy))

# ── Whale ────────────────────────────────────────────────────────────────────
class Whale:
    def __init__(self):
        self.x = random.randint(80, W - 80)
        self.y = SEA_LEVEL + 15
        self.vx = random.choice([-1, 1]) * random.uniform(0.8, 1.5)
        self.alive = True
        self.size = 45
        self.spout_timer = 0
        self.spouting = False
        self.spout_particles = []
        self.wobble = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.wobble += 0.02
        self.x += self.vx
        self.y += math.sin(self.wobble) * 0.2
        if self.x < 40 or self.x > W - 40:
            self.vx *= -1
        self.y = max(SEA_LEVEL, min(SEA_LEVEL + 30, self.y))

        self.spout_timer += 1
        if self.spout_timer > 120 + random.randint(0, 100):
            self.spouting = True
            self.spout_timer = 0
        if self.spouting:
            for i in range(2):
                sx = self.x + random.uniform(-3, 3)
                sy = self.y - self.size // 2 - 5
                self.spout_particles.append({
                    "x": sx, "y": sy,
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(-1.5, -0.5),
                    "life": 20, "max_life": 20, "size": random.uniform(2, 5)
                })
            self.spouting = False
        for p in self.spout_particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] -= 0.02
            p["life"] -= 1
            if p["life"] <= 0:
                self.spout_particles.remove(p)

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        d = -1 if self.vx > 0 else 1
        t = pygame.time.get_ticks() * 0.001
        # body (more volumetric)
        body_rect = pygame.Rect(cx - self.size, cy - self.size // 3 - 2, self.size * 2, self.size * 2 // 3 + 4)
        pygame.draw.ellipse(surf, (35, 38, 65), body_rect)
        pygame.draw.ellipse(surf, (50, 55, 85), body_rect, 1)
        # body highlight
        hl = pygame.Rect(cx - self.size + 8, cy - self.size // 3 + 2, self.size // 2, self.size // 4)
        pygame.draw.ellipse(surf, (60, 65, 95, 80), hl)
        # belly (lighter)
        belly = pygame.Rect(cx - self.size // 2 - 4, cy, self.size + 8, self.size // 3 + 2)
        pygame.draw.ellipse(surf, (90, 90, 130), belly)
        pygame.draw.ellipse(surf, (110, 110, 150), belly, 1)
        # belly grooves
        for i in range(4):
            gy = cy + 4 + i * 4
            pygame.draw.arc(surf, (70, 70, 110), (cx - self.size // 2, gy - 3, self.size, 6), 0.1, 3.0, 1)
        # head / jaw (more pronounced)
        head_rect = pygame.Rect(cx + d * (self.size - 12), cy - self.size // 3 - 4, 18, self.size * 2 // 3 + 8)
        pygame.draw.ellipse(surf, (30, 33, 60), head_rect)
        # jaw line
        jaw_y = cy + 4
        pygame.draw.line(surf, (20, 20, 45), (cx + d * (self.size - 4), jaw_y),
                        (cx - d * 5, jaw_y), 1)
        # eye with detail
        ex = cx + d * (self.size - 6)
        pygame.draw.circle(surf, (255, 255, 255), (ex, cy - 4), 4)
        pygame.draw.circle(surf, (15, 15, 25), (ex, cy - 4), 2)
        pygame.draw.circle(surf, (255, 255, 255), (ex - 1, cy - 5), 1)
        # tail flukes (larger, more detailed)
        tail_base = cx - self.size + 3
        fluke_top = (tail_base, cy - 8)
        fluke_bot = (tail_base, cy + 8)
        fluke_tip_top = (tail_base - 18, cy - 18 + 5 * math.sin(t))
        fluke_tip_bot = (tail_base - 18, cy + 18 - 5 * math.sin(t * 0.7))
        fluke_mid = (tail_base - 22 + 4 * math.sin(t * 0.5), cy)
        fluke_pts = [fluke_top, fluke_tip_top, fluke_mid, fluke_tip_bot, fluke_bot]
        pygame.draw.polygon(surf, (35, 38, 65), fluke_pts)
        pygame.draw.polygon(surf, (50, 55, 85), fluke_pts, 1)
        # flipper (more detailed)
        flipper_pts = [(cx - 8, cy + 4), (cx - 18, cy + 14), (cx - 5, cy + 10), (cx, cy + 6)]
        pygame.draw.polygon(surf, (30, 33, 60), flipper_pts)
        # blowhole
        bh = (cx + d * 5, cy - self.size // 3 - 4)
        pygame.draw.ellipse(surf, (20, 20, 45), (bh[0] - 3, bh[1] - 2, 6, 4))
        # spout (more dramatic)
        for p in self.spout_particles:
            alpha = int(220 * p["life"] / p["max_life"])
            size = p["size"] * (1 + 0.3 * (1 - p["life"] / p["max_life"]))
            s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
            col = (180 + int(50 * (1 - p["life"] / p["max_life"])),
                   220 + int(30 * (1 - p["life"] / p["max_life"])), 255, alpha)
            pygame.draw.circle(s, col, (int(size), int(size)), int(size))
            pygame.draw.circle(s, (255, 255, 255, alpha // 2), (int(size), int(size)), int(size * 0.5))
            surf.blit(s, (int(p["x"] - size), int(p["y"] - size)))

# ── Sea Turtle ───────────────────────────────────────────────────────────────
class SeaTurtle:
    def __init__(self):
        self.x = random.randint(50, W - 50)
        self.y = SEA_LEVEL + random.randint(10, 40)
        self.vx = random.choice([-1, 1]) * random.uniform(0.8, 1.8)
        self.alive = True
        self.size = 18
        self.wobble = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.wobble += 0.03
        self.x += self.vx
        self.y += math.sin(self.wobble) * 0.2
        if self.x < 30 or self.x > W - 30:
            self.vx *= -1
        self.y = max(SEA_LEVEL + 5, min(SEA_LEVEL + 50, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        d = -1 if self.vx > 0 else 1
        t = pygame.time.get_ticks() * 0.003
        # shell (more 3D with highlight)
        shell_rect = pygame.Rect(cx - self.size, cy - self.size // 2 - 3, self.size * 2, self.size + 4)
        pygame.draw.ellipse(surf, (45, 120, 45), shell_rect)
        pygame.draw.ellipse(surf, (60, 150, 60), shell_rect, 1)
        # shell highlight
        hl = pygame.Rect(cx - self.size // 2, cy - self.size // 3, self.size, self.size // 3)
        pygame.draw.ellipse(surf, (70, 160, 70, 100), hl)
        # shell hexagonal pattern
        for i in range(3):
            for j in range(2):
                px = cx - self.size // 2 + i * self.size // 2
                py = cy - 2 + j * 5
                hex_size = 4 + int(2 * math.sin(t + i + j))
                pygame.draw.ellipse(surf, (35, 95, 35), (px - hex_size // 2, py - 3, hex_size, 6), 1)
        # shell center line
        pygame.draw.line(surf, (35, 95, 35), (cx, cy - self.size // 2 + 2), (cx, cy + self.size // 2 - 2), 1)
        # head (animated bob)
        head_bob = math.sin(t * 2) * 1
        head_cx = cx + d * (self.size + 2)
        head_cy = cy + head_bob
        pygame.draw.circle(surf, (65, 155, 55), (int(head_cx), int(head_cy)), 7)
        pygame.draw.circle(surf, (50, 130, 45), (int(head_cx), int(head_cy)), 7, 1)
        # eye
        eye_cx = head_cx + d * 3
        pygame.draw.circle(surf, (255, 255, 255), (int(eye_cx), int(head_cy - 1)), 3)
        pygame.draw.circle(surf, (10, 10, 10), (int(eye_cx), int(head_cy - 1)), 2)
        pygame.draw.circle(surf, (255, 255, 255), (int(eye_cx - 1), int(head_cy - 2)), 1)
        # mouth
        pygame.draw.arc(surf, (40, 100, 40), (int(head_cx - 2), int(head_cy), 6, 3), 0.1, 3.0, 1)
        # front flippers (animated)
        for i, (fx, fy, fa, flip_dir) in enumerate([
            (cx - self.size // 2 + 2, cy + 2, -0.4 + 0.2 * math.sin(t * 1.5), 1),
            (cx + self.size // 2 - 2, cy + 2, 0.4 + 0.2 * math.sin(t * 1.5 + 1), -1),
        ]):
            ex = fx + d * flip_dir * (8 + 2 * math.sin(t * 1.5 + i))
            ey = fy + 6 * math.sin(fa)
            pygame.draw.ellipse(surf, (55, 135, 50), (min(ex, ex + 6) - 3, ey - 2, 7, 5))
        # back flippers
        for fx, fy, fa in [(cx - self.size // 3, cy + 3, -0.2),
                          (cx + self.size // 3, cy + 3, 0.2)]:
            ex = fx + d * 5
            ey = fy + 4 * math.sin(fa)
            pygame.draw.ellipse(surf, (50, 125, 45), (ex - 2, ey - 1, 5, 3))

# ── Jellyfish ────────────────────────────────────────────────────────────────
class Jellyfish:
    def __init__(self):
        self.x = random.randint(50, W - 50)
        self.y = SEA_LEVEL + random.randint(30, H - 40)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.3, 0.3)
        self.alive = True
        self.size = 12
        self.pulse = random.uniform(0, math.pi * 2)
        self.color = random.choice([(200, 100, 255), (100, 200, 255), (255, 150, 200), (100, 255, 200)])

    def update(self):
        if not self.alive:
            return
        self.pulse += 0.04
        self.x += self.vx + math.sin(self.pulse * 0.5) * 0.2
        self.y += self.vy + math.sin(self.pulse * 0.3) * 0.15
        if self.x < 20 or self.x > W - 20:
            self.vx *= -1
        if self.y < SEA_LEVEL + 10 or self.y > H - 20:
            self.vy *= -1

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        now = pygame.time.get_ticks() * 0.001
        pulse_size = self.size + 2 * math.sin(self.pulse)
        # outer glow (larger)
        glow = pygame.Surface((int(pulse_size * 4), int(pulse_size * 4)), pygame.SRCALPHA)
        alpha_outer = int(20 + 15 * math.sin(self.pulse))
        pygame.draw.circle(glow, (*self.color, alpha_outer), (int(pulse_size * 2), int(pulse_size * 2)), int(pulse_size * 2))
        pygame.draw.circle(glow, (255, 255, 255, alpha_outer // 3), (int(pulse_size * 2), int(pulse_size * 2)), int(pulse_size * 1.5), 1)
        surf.blit(glow, (int(cx - pulse_size * 2), int(cy - pulse_size * 2)))
        # inner glow
        inner_glow = pygame.Surface((int(pulse_size * 2.5), int(pulse_size * 2.5)), pygame.SRCALPHA)
        alpha_inner = int(40 + 30 * math.sin(self.pulse))
        pygame.draw.circle(inner_glow, (*self.color, alpha_inner), (int(pulse_size * 1.25), int(pulse_size * 1.25)), int(pulse_size * 1.25))
        surf.blit(inner_glow, (int(cx - pulse_size * 1.25), int(cy - pulse_size * 1.25)))
        # dome (bell shape)
        dome_pts = []
        for angle in range(0, 181, 15):
            a = math.radians(angle - 90)
            r = pulse_size * (0.7 + 0.3 * math.sin(angle * 0.05 + self.pulse))
            dx = math.cos(a) * r
            dy = math.sin(a) * r + pulse_size * 0.2
            dome_pts.append((cx + dx, cy + dy))
        if dome_pts:
            pygame.draw.polygon(surf, self.color, dome_pts)
            pygame.draw.polygon(surf, (255, 255, 255, 60), dome_pts, 1)
        # dome top highlight
        hl = pygame.Rect(cx - pulse_size * 0.4, cy - pulse_size * 0.3, pulse_size * 0.8, pulse_size * 0.3)
        pygame.draw.ellipse(surf, (255, 255, 255, 80), hl)
        # internal organ lines
        for i in range(4):
            a = math.radians(i * 90 + 45)
            ox = cx + math.cos(a) * pulse_size * 0.3
            oy = cy + math.sin(a) * pulse_size * 0.15
            pygame.draw.line(surf, (255, 255, 255, 40), (cx, cy + 2), (ox, oy), 1)
        # tentacles (more, with wave motion)
        for i in range(10):
            a = math.radians(i * 36 + now * 30)
            tl = pulse_size * 1.2 + 6 * math.sin(self.pulse + i * 0.5) + 4 * math.sin(now * 2 + i)
            segments = 6
            for s in range(segments):
                frac = s / segments
                px = cx + math.cos(a) * tl * frac + math.sin(now * 3 + i + s * 0.5) * 3 * frac
                py = cy + pulse_size * 0.4 + math.sin(a) * tl * frac + math.cos(now * 2.5 + i + s) * 2 * frac
                r = max(1, int(3 * (1 - frac * 0.7)))
                alpha_t = int(200 * (1 - frac * 0.4))
                # gradient from color to transparent
                tc = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*tc, alpha_t), (r, r), r)
                surf.blit(s, (int(px - r), int(py - r)))
        # glowing center
        pygame.draw.circle(surf, (255, 255, 255, 100), (cx, cy), 3)
        pygame.draw.circle(surf, (255, 255, 255, 60), (cx, cy), 5, 1)

# ── Manta Ray ────────────────────────────────────────────────────────────────
class MantaRay:
    def __init__(self):
        self.x = random.randint(50, W - 50)
        self.y = SEA_LEVEL + random.randint(15, 60)
        self.vx = random.choice([-1, 1]) * random.uniform(1.5, 2.5)
        self.alive = True
        self.size = 28
        self.wobble = random.uniform(0, math.pi * 2)
        self.wing_flap = random.uniform(0, math.pi * 2)
        self.color = random.choice([(30, 30, 50), (50, 40, 60), (40, 35, 55), (60, 50, 70)])

    def update(self):
        if not self.alive:
            return
        self.wobble += 0.03
        self.wing_flap += 0.08
        self.x += self.vx
        self.y += math.sin(self.wobble) * 0.4
        if self.x < 30 or self.x > W - 30:
            self.vx *= -1
        self.y = max(SEA_LEVEL + 10, min(H - 15, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        d = -1 if self.vx > 0 else 1
        t = pygame.time.get_ticks() * 0.003
        wing_angle = math.sin(self.wing_flap) * 0.4
        # body disc
        body_rect = pygame.Rect(cx - self.size // 2, cy - self.size // 4, self.size, self.size // 2)
        pygame.draw.ellipse(surf, self.color, body_rect)
        pygame.draw.ellipse(surf, (60, 55, 80), body_rect, 1)
        # wings (large triangular)
        wing_pts = [
            (cx - self.size // 2, cy),
            (cx - self.size - 5, cy - 8 - 15 * wing_angle),
            (cx - self.size // 2, cy + 2),
        ]
        pygame.draw.polygon(surf, self.color, wing_pts)
        pygame.draw.polygon(surf, (60, 55, 80), wing_pts, 1)
        wing_pts2 = [
            (cx + self.size // 2, cy),
            (cx + self.size + 5, cy - 8 + 15 * wing_angle),
            (cx + self.size // 2, cy + 2),
        ]
        pygame.draw.polygon(surf, self.color, wing_pts2)
        pygame.draw.polygon(surf, (60, 55, 80), wing_pts2, 1)
        # tail
        tail_len = 20 + 5 * math.sin(t * 2)
        pygame.draw.line(surf, self.color, (cx - self.size // 4, cy),
                        (cx - self.size // 4 - tail_len, cy + 2 * math.sin(t)), 2)
        # underbelly
        belly = pygame.Rect(cx - self.size // 3, cy - self.size // 6, self.size * 2 // 3, self.size // 3)
        pygame.draw.ellipse(surf, (80, 75, 100, 120), belly)
        # mouth / cephalic lobes
        for i, mult in enumerate([-1, 1]):
            lx = cx + mult * (self.size // 4 + 2)
            ly = cy - 2
            pygame.draw.ellipse(surf, (40, 40, 60), (lx - 2, ly - 2, 5, 4))
        # eyes (on top of head)
        for ex_off in [-4, 4]:
            eye_off = d * 1
            pygame.draw.circle(surf, (255, 255, 255), (cx + ex_off + eye_off, cy - 4), 3)
            pygame.draw.circle(surf, (10, 10, 20), (cx + ex_off + eye_off, cy - 4), 2)
        # gill slits
        for i in range(3):
            gx = cx - d * (self.size // 3 - i * 4)
            pygame.draw.line(surf, (20, 20, 40), (gx, cy - 2), (gx, cy + 2), 1)

# ── Bird ─────────────────────────────────────────────────────────────────────
class Bird:
    def __init__(self):
        self.x = random.randint(50, W - 50)
        self.y = random.randint(20, SEA_LEVEL - 50)
        self.vx = random.choice([-1, 1]) * random.uniform(1.5, 3)
        self.alive = True
        self.wing = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.wing += 0.1
        self.x += self.vx
        self.y += math.sin(self.wing * 1.5) * 0.4
        if self.x < 10 or self.x > W - 10:
            self.vx *= -1
        self.y = max(10, min(SEA_LEVEL - 30, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        wing_up = math.sin(self.wing)
        # body (white/gray seagull)
        body_color = (220, 220, 230)
        wing_color = (180, 180, 190)
        tip_color = (40, 40, 50)
        # body - elliptical
        pygame.draw.ellipse(surf, body_color, (cx - 5, cy - 2, 10, 5))
        pygame.draw.ellipse(surf, (200, 200, 210), (cx - 5, cy - 2, 10, 5), 1)
        # wings - V shape with black tips
        # left wing
        lw_angle = -0.6 - wing_up * 0.8
        lw_end_x = cx - 10 + math.cos(lw_angle) * 8
        lw_end_y = cy + math.sin(lw_angle) * 6
        pygame.draw.line(surf, wing_color, (cx - 2, cy), (lw_end_x, lw_end_y), 3)
        pygame.draw.line(surf, tip_color, (lw_end_x, lw_end_y),
                        (lw_end_x - math.cos(lw_angle) * 4, lw_end_y - math.sin(lw_angle) * 3), 2)
        # right wing
        rw_angle = math.pi + 0.6 - wing_up * 0.8
        rw_end_x = cx + 10 + math.cos(rw_angle) * 8
        rw_end_y = cy + math.sin(rw_angle) * 6
        pygame.draw.line(surf, wing_color, (cx + 2, cy), (rw_end_x, rw_end_y), 3)
        pygame.draw.line(surf, tip_color, (rw_end_x, rw_end_y),
                        (rw_end_x - math.cos(rw_angle) * 4, rw_end_y - math.sin(rw_angle) * 3), 2)
        # tail (forked)
        pygame.draw.line(surf, body_color, (cx - 5, cy), (cx - 9, cy + 2), 2)
        pygame.draw.line(surf, body_color, (cx - 5, cy), (cx - 9, cy - 1), 2)
        # head
        pygame.draw.circle(surf, body_color, (cx + 5, cy - 1), 3)
        # eye
        pygame.draw.circle(surf, (30, 30, 30), (cx + 6, cy - 1), 1)
        # beak
        pygame.draw.line(surf, (240, 200, 100), (cx + 7, cy - 1), (cx + 10, cy), 1)

# ── Merchant ─────────────────────────────────────────────────────────────────
class Merchant:
    def __init__(self):
        self.x = random.choice([-100, W + 100])
        self.y = SEA_LEVEL - 40
        self.vx = 2 if self.x < 0 else -2
        self.alive = True
        self.timer = 0
        self.items = random.sample(MERCHANT_ITEMS, min(3, len(MERCHANT_ITEMS)))
        self.sail_color = (200, 80, 80)
        self.bob = 0

    def update(self, boats, ocean):
        self.timer += 1
        self.bob = 5 * math.sin(ocean.time * 2 + self.x * 0.03)
        self.x += self.vx
        if self.timer > 600:
            self.alive = False
            return
        for b in boats:
            if dist((self.x, self.y), (b.x, b.y)) < 70:
                self.vx *= -0.5
                self.x += self.vx

    def draw(self, surf):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y + self.bob)
        # simple merchant boat
        hull = [(cx - 35, cy + 5), (cx - 30, cy + 18), (cx + 30, cy + 18), (cx + 35, cy + 5)]
        pygame.draw.polygon(surf, (100, 60, 30), hull)
        pygame.draw.polygon(surf, (60, 30, 10), hull, 2)
        # cabin
        cab = [(cx - 15, cy - 8), (cx + 15, cy - 8), (cx + 12, cy - 25), (cx - 12, cy - 25)]
        pygame.draw.polygon(surf, (80, 40, 20), cab)
        # mast
        pygame.draw.line(surf, (40, 20, 10), (cx, cy - 25), (cx, cy - 55), 3)
        # red sail
        sail = [(cx + 1, cy - 53), (cx + 25, cy - 20), (cx + 22, cy - 5), (cx + 1, cy - 8)]
        pygame.draw.polygon(surf, self.sail_color, sail)
        pygame.draw.polygon(surf, (255, 150, 150), sail, 1)
        # merchant flag
        flag = [(cx, cy - 55), (cx + 12, cy - 50), (cx, cy - 45)]
        pygame.draw.polygon(surf, (255, 215, 0), flag)
        # golden glow
        glow = pygame.Surface((80, 60), pygame.SRCALPHA)
        a = int(30 + 20 * math.sin(pygame.time.get_ticks() * 0.003))
        pygame.draw.ellipse(glow, (255, 215, 0, a), (0, 0, 80, 60))
        surf.blit(glow, (cx - 40, cy - 30))
        # price sign
        if hasattr(self, 'items') and self.items:
            for i, item in enumerate(self.items):
                txt = f"{item['name']}: {item['cost']}g"
                ts = pygame.font.Font(None, 16)
                t = ts.render(txt, True, (255, 215, 0))
                surf.blit(t, (cx - 35, cy - 35 - i * 14))

# ── UI ───────────────────────────────────────────────────────────────────────
class UI:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 36)
        self.transition_alpha = 0

    def draw(self, surf):
        g = self.game
        panel = pygame.Surface((W, 145), pygame.SRCALPHA)
        panel.fill((0, 0, 20, 100))
        surf.blit(panel, (0, 0))

        if g.two_player:
            self._draw_player_stats(surf, g.boats[0], 20, "P1", (100, 200, 255))
            self._draw_player_stats(surf, g.boats[1], W // 2 + 20, "P2", (255, 180, 100))
        else:
            self._draw_player_stats(surf, g.boats[0], 20, "", (255, 255, 200))

        # Weapon info
        boat = g.boats[0]
        w = g.weapons[boat.current_weapon]
        effective_dmg = w['dmg'] + boat.weapon_dmg_bonus
        effective_range = w['range'] + boat.range_bonus
        col = (255, 255, 100)
        w_name = self.font.render(w["name"], True, col)
        surf.blit(w_name, (W // 2 - 60, 5))
        w_info = self.small_font.render(f"DMG: {effective_dmg}  RNG: {effective_range}", True, (180, 180, 200))
        surf.blit(w_info, (W // 2 - 60, 32))
        w_hint = self.small_font.render("Q / E to switch", True, (120, 120, 150))
        surf.blit(w_hint, (W // 2 - 50, 50))

        if g.two_player:
            w2 = g.weapons[g.boats[1].current_weapon]
            w2_name = self.font.render(f"P2: {w2['name']}", True, (255, 220, 150))
            surf.blit(w2_name, (W // 2 - 60, 75))
            w2_hint = self.small_font.render("[/] to switch", True, (120, 120, 150))
            surf.blit(w2_hint, (W // 2 - 50, 95))

        # Stats right side
        stats = [
            (f"Wave {g.wave}", (200, 200, 255)),
            (f"Lv.{g.level}", (255, 215, 0)),
            (f"Creatures: {g.animals_caught}", (150, 255, 150)),
            (f"Monsters: {g.monsters_killed}", (255, 150, 150)),
        ]
        if g.ocean.weather == "storm":
            stats.insert(0, ("STORM", (200, 100, 255)))
        elif g.ocean.weather == "cloudy":
            stats.insert(0, ("Cloudy", (180, 180, 200)))
        for i, (text, color) in enumerate(stats):
            txt = self.small_font.render(text, True, color)
            surf.blit(txt, (W - 130, 5 + i * 18))

        # XP bar
        xp_bar_x, xp_bar_y = W // 2 - 60, 118
        xp_bar_w, xp_bar_h = 120, 6
        pygame.draw.rect(surf, (30, 30, 50), (xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h), 0, 3)
        if g.xp_to_next > 0:
            xp_fill = int(xp_bar_w * g.xp / g.xp_to_next)
            if xp_fill > 0:
                pygame.draw.rect(surf, (100, 200, 255), (xp_bar_x + 1, xp_bar_y + 1, min(xp_fill, xp_bar_w - 2), xp_bar_h - 2), 0, 2)
        pygame.draw.rect(surf, (100, 100, 140), (xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h), 1, 3)
        xp_label = self.small_font.render(f"XP {g.xp}/{g.xp_to_next}", True, (150, 200, 255))
        surf.blit(xp_label, (xp_bar_x + xp_bar_w // 2 - xp_label.get_width() // 2, xp_bar_y - 14))

        # weapon slots
        for i, w in enumerate(g.weapons):
            bx = W // 2 - 190 + i * 130
            by = H - 60
            active = i == g.boats[0].current_weapon
            active2 = g.two_player and i == g.boats[1].current_weapon
            bg = (50, 50, 80) if active else (30, 30, 50)
            if active2 and not active:
                bg = (80, 50, 30)
            border = (255, 255, 100) if active else ((200, 150, 50) if active2 else (100, 100, 120))
            pygame.draw.rect(surf, bg, (bx, by, 115, 42), 0, 6)
            pygame.draw.rect(surf, border, (bx, by, 115, 42), 2, 6)
            txt = self.small_font.render(w["name"], True, (255, 255, 200) if active or active2 else (150, 150, 180))
            surf.blit(txt, (bx + 58 - txt.get_width() // 2, by + 8))
            eff_dmg = w['dmg'] + (boat.weapon_dmg_bonus if active else 0)
            dmg_txt = self.small_font.render(f"DMG {eff_dmg}", True, (120, 120, 150))
            surf.blit(dmg_txt, (bx + 58 - dmg_txt.get_width() // 2, by + 24))
            key_hint = self.small_font.render(str(i + 1), True, (80, 80, 100))
            surf.blit(key_hint, (bx + 5, by + 5))

        # message
        if g.message and g.message_timer > 0:
            mc = getattr(g, 'message_color', (255, 255, 100))
            msg = self.font.render(g.message, True, mc)
            msg_rect = msg.get_rect(center=(W // 2, 160))
            surf.blit(msg, msg_rect)

        # merchant hint
        if g.merchant and g.merchant.alive:
            hint = self.font.render("Press M to trade with merchant", True, (255, 215, 0))
            hr = hint.get_rect(center=(W // 2, 190))
            surf.blit(hint, hr)

        g.crosshair.draw(surf, g)
        self._draw_controls(surf)

        # transition overlay
        if self.transition_alpha > 0:
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(self.transition_alpha)
            overlay.fill((0, 0, 0))
            surf.blit(overlay, (0, 0))
            if self.transition_alpha > 128:
                txt = self.big_font.render(f"Wave {g.wave}", True, (255, 255, 200))
                r = txt.get_rect(center=(W // 2, H // 2 - 20))
                surf.blit(txt, r)
                sub = self.font.render("New dangers arise on the sea!", True, (200, 200, 180))
                sr = sub.get_rect(center=(W // 2, H // 2 + 20))
                surf.blit(sub, sr)

    def _draw_player_stats(self, surf, boat, x, label, label_color):
        # row 1: score icon + text
        score_text = self.font.render(f"{boat.score}", True, (255, 255, 200))
        surf.blit(score_text, (x + 35, 8))
        s_icon = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(s_icon, (255, 215, 0), (7, 7), 6)
        pygame.draw.circle(s_icon, (255, 255, 200), (7, 7), 3)
        surf.blit(s_icon, (x + 15, 10))

        # gold
        gold_text = self.font.render(f"{boat.gold}", True, (255, 215, 0))
        surf.blit(gold_text, (x + 35, 34))
        g_icon = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(g_icon, (255, 215, 0), (7, 7), 6)
        pygame.draw.rect(g_icon, (255, 220, 50), (3, 3, 8, 8))
        surf.blit(g_icon, (x + 15, 36))

        # label
        if label:
            lbl = self.small_font.render(label, True, label_color)
            surf.blit(lbl, (x + 15, 58))

        # HP bar
        hp_y = 72
        hp_bar_w, hp_bar_h = 130, 10
        pygame.draw.rect(surf, (30, 30, 30), (x + 10, hp_y, hp_bar_w, hp_bar_h), 0, 3)
        if boat.hp > 0:
            hp_w = int(hp_bar_w * boat.hp / boat.max_hp)
            if boat.hp / boat.max_hp > 0.5:
                hp_c = (50, 200, 80)
            elif boat.hp / boat.max_hp > 0.25:
                hp_c = (220, 200, 40)
            else:
                hp_c = (220, 40, 40)
            pygame.draw.rect(surf, hp_c, (x + 11, hp_y + 1, max(0, hp_w - 2), hp_bar_h - 2), 0, 2)
        pygame.draw.rect(surf, (100, 100, 120), (x + 10, hp_y, hp_bar_w, hp_bar_h), 1, 3)
        hp_txt = self.small_font.render(f"{boat.hp}/{boat.max_hp}", True, (200, 200, 220))
        surf.blit(hp_txt, (x + hp_bar_w // 2 - hp_txt.get_width() // 2 + 10, hp_y + 1))

        # fish count
        fish_txt = self.small_font.render(f"Fish: {boat.fish_count}", True, (150, 200, 255))
        surf.blit(fish_txt, (x + 15, 92))

        # defense
        if boat.defense > 0:
            def_txt = self.small_font.render(f"Def: +{boat.defense}", True, (100, 200, 255))
            surf.blit(def_txt, (x + 100, 92))

        # luck
        if boat.luck_bonus > 0:
            luck_txt = self.small_font.render(f"Luck: +{boat.luck_bonus}", True, (200, 200, 100))
            surf.blit(luck_txt, (x + 15, 108))

    def _draw_controls(self, surf):
        g = self.game
        if g.two_player:
            lines = [
                "P1: WASD Move | Q/E Weapon | Left Click Fire | F Throw Fish",
                "P2: IJKL Move | [/] Weapon | Right Click Fire | G Throw Fish",
                "ESC: Pause | P: 1P/2P | R: Restart",
            ]
        else:
            lines = [
                "WASD/Arrows: Sail | Click: Fire | Q/E: Weapon | F: Throw Fish",
                "M: Trade | P: 2-Player | ESC: Pause | R: Restart",
            ]
        y_offset = H - 36
        for line in lines:
            txt = self.small_font.render(line, True, (160, 160, 180, 160))
            surf.blit(txt, (W // 2 - txt.get_width() // 2, y_offset))
            y_offset += 18

# ── Game ─────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.wave = 1
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50
        self.animals_caught = 0
        self.monsters_killed = 0
        self.message = ""
        self.message_timer = 0
        self.message_color = (255, 255, 100)
        self.paused = False
        self.game_over = False
        self.two_player = False

        self.weapons = [dict(w) for w in WEAPONS]
        self.base_weapons = [dict(w) for w in WEAPONS]

        self.ocean = Ocean()
        self.boats = [LuxuryBoat(0)]
        self.projectiles = []
        self.thrown_fish = []
        self.fish_list = []
        self.monsters = []
        self.treasures = []
        self.dolphins = []
        self.whales = []
        self.turtles = []
        self.jellyfish_list = []
        self.manta_rays = []
        self.birds = []
        self.particles = []
        self.level_up_effects = []
        self.crosshair = Crosshair()
        self.merchant = None
        self.merchant_timer = 0

        self.ui = UI(self)
        self.wave_timer = 0
        self.spawn_cooldown = 0
        self.mx, self.my = W // 2, H // 2

        self.init_wave()

    @property
    def boat(self):
        return self.boats[0]

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.show_message(f"Level Up! You are now Level {self.level}!", 120, (255, 215, 0))
            # level up effects
            for b in self.boats:
                bx, by = b.get_pos()
                self.level_up_effects.append(LevelUpEffect(bx, by))
                b.max_hp += 10
                b.hp = min(b.hp + 20, b.max_hp)
                b.defense += 1

    def init_wave(self):
        self.fish_list = []
        self.monsters = []
        self.treasures = []
        self.dolphins = []
        self.whales = []
        self.turtles = []
        self.jellyfish_list = []
        self.manta_rays = []
        self.birds = []
        self.projectiles = []
        self.thrown_fish = []

        for _ in range(6 + self.wave * 2):
            self.fish_list.append(Fish(self.wave))
        for _ in range(min(self.wave, 4)):
            self.dolphins.append(Dolphin())
        for _ in range(min(self.wave // 2 + 1, 3)):
            self.whales.append(Whale())
        for _ in range(min(self.wave, 3)):
            self.turtles.append(SeaTurtle())
        for _ in range(min(self.wave + 1, 5)):
            self.jellyfish_list.append(Jellyfish())
        for _ in range(min(self.wave // 2 + 1, 3)):
            self.manta_rays.append(MantaRay())
        for _ in range(min(self.wave + 4, 10)):
            self.birds.append(Bird())
        for _ in range(min(self.wave, 5)):
            self.monsters.append(Monster(self.wave))
        for _ in range(random.randint(1, 3)):
            tx = random.randint(100, W - 100)
            ty = SEA_LEVEL + random.randint(10, 60)
            self.treasures.append(Treasure(tx, ty, random.randint(20, 50 + self.wave * 10)))

    def show_message(self, msg, duration=90, color=None):
        self.message = msg
        self.message_timer = duration
        if color:
            self.message_color = color
        else:
            self.message_color = (255, 255, 100)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEMOTION:
                self.mx, self.my = event.pos
                self.crosshair.update(event.pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                    return True
                if event.key == pygame.K_p:
                    self.toggle_two_player()
                if event.key == pygame.K_m and not self.paused and not self.game_over:
                    if self.merchant and self.merchant.alive:
                        self.interact_merchant()
                if not self.paused and not self.game_over:
                    if event.key == pygame.K_q:
                        self.boats[0].current_weapon = (self.boats[0].current_weapon - 1) % len(self.weapons)
                    if event.key == pygame.K_e:
                        self.boats[0].current_weapon = (self.boats[0].current_weapon + 1) % len(self.weapons)
                    if event.key == pygame.K_f:
                        self.throw_fish(0)
                    if self.two_player and len(self.boats) > 1:
                        if event.key == pygame.K_LEFTBRACKET:
                            self.boats[1].current_weapon = (self.boats[1].current_weapon - 1) % len(self.weapons)
                        if event.key == pygame.K_RIGHTBRACKET:
                            self.boats[1].current_weapon = (self.boats[1].current_weapon + 1) % len(self.weapons)
                        if event.key == pygame.K_g:
                            self.throw_fish(1)
                    if event.key == pygame.K_1:
                        self.boats[0].current_weapon = 0
                    if event.key == pygame.K_2:
                        self.boats[0].current_weapon = 1
                    if event.key == pygame.K_3:
                        self.boats[0].current_weapon = 2
            if event.type == pygame.MOUSEBUTTONDOWN and not self.paused and not self.game_over:
                if event.button == 1:
                    self.fire_weapon(0)
                if event.button == 3 and self.two_player:
                    self.fire_weapon(1)
        return True

    def toggle_two_player(self):
        self.two_player = not self.two_player
        if self.two_player and len(self.boats) == 1:
            b2 = LuxuryBoat(1)
            b2.x = W // 2 + 80
            b2.y = SEA_LEVEL - 35
            self.boats.append(b2)
            self.show_message("Two Player Mode - Press P to toggle", 90)
        elif not self.two_player and len(self.boats) > 1:
            self.boats[0].gold += self.boats[1].gold
            self.boats[0].score += self.boats[1].score
            self.boats[0].fish_count += self.boats[1].fish_count
            self.boats.pop(1)
            self.show_message("Single Player Mode", 60)

    def fire_weapon(self, player_id):
        boat = self.boats[player_id]
        w = self.weapons[boat.current_weapon]
        bx, by = boat.get_pos()

        d = dist((bx, by), (self.mx, self.my))
        effective_range = w["range"] + boat.range_bonus
        if d > effective_range:
            self.show_message(f"{w['name']} out of range ({int(d)}/{effective_range})!")
            return

        effective_dmg = w["dmg"] + boat.weapon_dmg_bonus

        if w.get("catch"):
            nearest_fish = None
            nearest_dist = float('inf')
            for f in self.fish_list:
                if not f.alive or f.caught:
                    continue
                fd = dist((self.mx, self.my), (f.x, f.y))
                if fd < 60 and fd < nearest_dist:
                    nearest_dist = fd
                    nearest_fish = f
            if nearest_fish:
                nearest_fish.caught = True
                nearest_fish.alive = False
                boat.fish_count += 1
                boat.gold += nearest_fish.value
                boat.score += nearest_fish.value
                self.add_xp(nearest_fish.value // 2)
                boat.caught_fish_values.append(nearest_fish.value)
                bx, by = boat.get_pos()
                boat.fish_animations.append({
                    "sx": nearest_fish.x, "sy": nearest_fish.y,
                    "t": 0, "color": nearest_fish.color
                })
                boat.fish_on_deck.append({
                    "ox": random.uniform(-8, 8),
                    "oy": random.uniform(-3, 3),
                    "color": nearest_fish.color
                })
                rare_tag = " ★ RARE!" if getattr(nearest_fish, 'rare', False) else ""
                self.show_message(f"Caught {nearest_fish.name}! +{nearest_fish.value} gold{rare_tag}", 60)
                for _ in range(10):
                    self.particles.append(CoinParticle(
                        nearest_fish.x, nearest_fish.y,
                        bx, by, nearest_fish.value
                    ))
                    self.particles.append(SplashParticle(
                        nearest_fish.x, nearest_fish.y,
                        (200, 220, 255),
                        (random.uniform(-2, 2), random.uniform(-2, 0)),
                        life=20, size=4
                    ))
                return

        # Apply dmg bonus to projectile
        w_modified = dict(w)
        w_modified["dmg"] = effective_dmg
        p = Projectile(bx, by, self.mx, self.my, w_modified, player_id)
        self.projectiles.append(p)
        self.show_message(f"Fired {w['name']}!", 30)

        flash_x = bx + (self.mx - bx) * 0.1
        flash_y = by + (self.my - by) * 0.1
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append(Particle(
                flash_x + random.uniform(-5, 5),
                flash_y + random.uniform(-5, 5),
                (255, 220, 100),
                (math.cos(angle) * speed, math.sin(angle) * speed),
                life=random.randint(5, 12), size=random.uniform(2, 5)
            ))
        for _ in range(3):
            self.particles.append(Particle(
                flash_x, flash_y,
                (255, 255, 200),
                (random.uniform(-1, 1), random.uniform(-1, 1)),
                life=8, size=random.uniform(6, 12)
            ))
        for _ in range(6):
            self.particles.append(Particle(
                bx + random.randint(-8, 8), by + 8,
                (180, 180, 180),
                (random.uniform(-0.5, 0.5), random.uniform(-1, 0)),
                life=random.randint(20, 35), size=random.uniform(3, 7)
            ))
        boat.target_angle += (bx - self.mx) * 0.002

    def interact_merchant(self):
        if not self.merchant or not self.merchant.alive:
            return
        boat = self.boats[0]
        if dist((boat.x, boat.y), (self.merchant.x, self.merchant.y)) > 90:
            self.show_message("Get closer to the merchant!", 60)
            return
        items = self.merchant.items
        if not items:
            self.show_message("Merchant has nothing left!", 60)
            return
        item = items[0]
        if boat.gold < item["cost"]:
            self.show_message(f"Not enough gold! {item['name']} costs {item['cost']}g", 60)
            return
        boat.gold -= item["cost"]
        effect = item["effect"]
        if effect == "hp":
            boat.max_hp += 50
            boat.hp = min(boat.hp + 50, boat.max_hp)
        elif effect == "speed":
            boat.speed += 1
        elif effect == "range":
            boat.range_bonus += 50
        elif effect == "dmg":
            boat.weapon_dmg_bonus += 5
        elif effect == "heal":
            boat.hp = min(boat.hp + 30, boat.max_hp)
        elif effect == "luck":
            boat.luck_bonus += 1
        self.show_message(f"Bought {item['name']}! {item['desc']}", 90, (100, 255, 100))
        self.merchant.items.remove(item)
        for _ in range(15):
            self.particles.append(CoinParticle(
                boat.x + random.randint(-20, 20),
                boat.y + random.randint(-20, 20),
                self.merchant.x, self.merchant.y, 0
            ))
        if not self.merchant.items:
            self.merchant.alive = False

    def throw_fish(self, player_id):
        boat = self.boats[player_id]
        if not boat.caught_fish_values:
            self.show_message("No fish to throw!")
            return
        value = boat.caught_fish_values.pop(0)
        bx, by = boat.get_pos()
        tf = ThrownFish(bx, by, self.mx, self.my, value, player_id)
        self.thrown_fish.append(tf)
        self.show_message(f"Threw fish! (+{value} gold to other player)", 60)

    def try_observe_animal(self, boat):
        for group in [self.dolphins, self.whales, self.turtles, self.jellyfish_list, self.manta_rays]:
            for ani in group:
                if not ani.alive:
                    continue
                if dist((boat.x, boat.y), (ani.x, ani.y)) < 55:
                    if random.random() < 0.02 + boat.luck_bonus * 0.005:
                        ani.alive = False
                        self.animals_caught += 1
                        bonus = random.randint(15, 50) + boat.luck_bonus * 5
                        boat.gold += bonus
                        boat.score += bonus
                        self.add_xp(bonus // 2)
                        names = {"Dolphin": "Dolphin", "Whale": "Whale", "SeaTurtle": "Sea Turtle", "Jellyfish": "Jellyfish", "MantaRay": "Manta Ray"}
                        name = type(ani).__name__
                        self.show_message(f"Observed {names.get(name, name)}! +{bonus} gold", 60)
                        for _ in range(8):
                            self.particles.append(CoinParticle(
                                ani.x, ani.y, boat.x, boat.y, bonus
                            ))
                        return True
        return False

    def update(self):
        if self.paused or self.game_over:
            return

        self.ocean.update()

        keys = pygame.key.get_pressed()

        # update P1
        self.boats[0].update(
            keys[pygame.K_LEFT] or keys[pygame.K_a],
            keys[pygame.K_RIGHT] or keys[pygame.K_d],
            keys[pygame.K_UP] or keys[pygame.K_w],
            keys[pygame.K_DOWN] or keys[pygame.K_s],
            self.ocean
        )

        # update P2 - use separate keys that don't conflict
        if self.two_player and len(self.boats) > 1:
            self.boats[1].update(
                keys[pygame.K_j],  # P2 left
                keys[pygame.K_l],  # P2 right
                keys[pygame.K_i],  # P2 up
                keys[pygame.K_k],  # P2 down
                self.ocean
            )

        # projectiles
        for p in self.projectiles[:]:
            animals_list = [self.dolphins, self.whales, self.turtles, self.jellyfish_list, self.manta_rays]
            result, target = p.update(self.monsters, self.fish_list, animals_list)
            if result == "hit" and target:
                if p.splash > 0:
                    for m in self.monsters:
                        if m.alive and dist((target.x, target.y), (m.x, m.y)) < p.splash:
                            m.hp -= p.dmg // 2
                    for _ in range(20):
                        self.particles.append(SplashParticle(
                            target.x, target.y, (255, 150, 50),
                            (random.uniform(-5, 5), random.uniform(-5, 5)),
                            life=20, size=5
                        ))
                else:
                    for _ in range(10):
                        self.particles.append(SplashParticle(
                            target.x, target.y, (255, 200, 100),
                            (random.uniform(-4, 4), random.uniform(-4, 4)),
                            life=15, size=4
                        ))
                if not target.alive:
                    self.monsters_killed += 1
                    reward = target.reward
                    if p.owner_id is not None and p.owner_id < len(self.boats):
                        self.boats[p.owner_id].gold += reward
                        self.boats[p.owner_id].score += reward
                    else:
                        self.boats[0].gold += reward
                        self.boats[0].score += reward
                    self.add_xp(reward)
                    self.show_message(f"Defeated {target.name}! +{reward} gold!", 90)
                    self.treasures.append(Treasure(
                        target.x + random.randint(-20, 20),
                        target.y + random.randint(-10, 10),
                        reward // 2
                    ))
                    for _ in range(30):
                        self.particles.append(SplashParticle(
                            target.x, target.y, target.color,
                            (random.uniform(-6, 6), random.uniform(-6, 6)),
                            life=30, size=6
                        ))
                    # big flash on death
                    for _ in range(10):
                        self.particles.append(Particle(
                            target.x, target.y, (255, 255, 200),
                            (random.uniform(-3, 3), random.uniform(-3, 3)),
                            life=10, size=random.uniform(4, 8)
                        ))
                self.projectiles.remove(p)
            elif result == "fish" and target:
                boat = self.boats[p.owner_id] if p.owner_id is not None and p.owner_id < len(self.boats) else self.boats[0]
                boat.fish_count += 1
                boat.gold += target.value
                boat.score += target.value
                self.add_xp(target.value // 2)
                boat.caught_fish_values.append(target.value)
                bx, by = boat.get_pos()
                boat.fish_animations.append({
                    "sx": target.x, "sy": target.y,
                    "t": 0, "color": target.color
                })
                boat.fish_on_deck.append({
                    "ox": random.uniform(-8, 8),
                    "oy": random.uniform(-3, 3),
                    "color": target.color
                })
                rare_tag = " ★ RARE!" if getattr(target, 'rare', False) else ""
                self.show_message(f"Caught {target.name}! +{target.value} gold{rare_tag}", 60)
                for _ in range(10):
                    self.particles.append(CoinParticle(
                        target.x, target.y, bx, by, target.value
                    ))
                self.projectiles.remove(p)
            elif result == "animal" and target:
                boat = self.boats[p.owner_id] if p.owner_id is not None and p.owner_id < len(self.boats) else self.boats[0]
                bonus = random.randint(20, 60) + boat.luck_bonus * 3
                boat.gold += bonus
                boat.score += bonus
                self.add_xp(bonus // 2)
                names = {Dolphin: "Dolphin", Whale: "Whale", SeaTurtle: "Sea Turtle", Jellyfish: "Jellyfish", MantaRay: "Manta Ray"}
                name = names.get(type(target), "Creature")
                self.show_message(f"Netted {name}! +{bonus} gold", 60)
                for _ in range(12):
                    self.particles.append(CoinParticle(
                        target.x, target.y, boat.x, boat.y, bonus
                    ))
                self.projectiles.remove(p)
            elif result == "expired":
                if p.y < SEA_LEVEL + 10:
                    for _ in range(5):
                        self.particles.append(SplashParticle(
                            p.x, SEA_LEVEL,
                            (200, 220, 255),
                            (random.uniform(-2, 2), random.uniform(-1, 1)),
                            life=15, size=3
                        ))
                self.projectiles.remove(p)

        # thrown fish
        for tf in self.thrown_fish[:]:
            tf.update()
            hit_boat = tf.check_hit_boat(self.boats)
            if hit_boat:
                self.show_message(f"Fish delivered! +{tf.value} gold to P{tf.owner_id + 1}", 90)
                for _ in range(12):
                    self.particles.append(CoinParticle(
                        tf.x, tf.y, hit_boat.x, hit_boat.y, tf.value
                    ))
                self.thrown_fish.remove(tf)
            elif not tf.alive:
                self.thrown_fish.remove(tf)

        # monsters
        for m in self.monsters:
            m.update(self.boats, self.ocean)
        self.monsters = [m for m in self.monsters if m.alive]

        # fish
        for f in self.fish_list:
            f.update()
        self.fish_list = [f for f in self.fish_list if f.alive]
        if len(self.fish_list) < 6 + self.wave * 2 and random.random() < 0.03:
            self.fish_list.append(Fish(self.wave))

        # animals
        for g in [self.dolphins, self.whales, self.turtles, self.jellyfish_list, self.manta_rays, self.birds]:
            for a in g:
                a.update()
            self.respawn_animals(g)

        # treasures
        for t in self.treasures[:]:
            t.update()
            for b in self.boats:
                if not t.collected and dist((b.x, b.y), (t.x, t.y)) < 45:
                    t.collected = True
                    b.gold += t.value
                    b.score += t.value
                    self.add_xp(t.value)
                    self.show_message(f"Found treasure! +{t.value} gold!", 60)
                    for _ in range(15):
                        self.particles.append(CoinParticle(
                            t.x, t.y, b.x, b.y, t.value
                        ))
            if t.collected:
                self.treasures.remove(t)

        # auto-fishing with luck bonus
        for b in self.boats:
            for fish in self.fish_list:
                if not fish.alive or fish.caught:
                    continue
                dist_to_fish = dist((b.x, b.y), (fish.x, fish.y))
                if dist_to_fish < 80:
                    catch_rate = 0.04 + b.luck_bonus * 0.01 + (1 - dist_to_fish / 80) * 0.03
                    if random.random() < catch_rate:
                        fish.caught = True
                        fish.alive = False
                        b.fish_count += 1
                        b.gold += fish.value
                        b.score += fish.value
                        self.add_xp(fish.value // 2)
                        b.caught_fish_values.append(fish.value)
                        b.fish_animations.append({
                            "sx": fish.x, "sy": fish.y,
                            "t": 0, "color": fish.color
                        })
                        b.fish_on_deck.append({
                            "ox": random.uniform(-8, 8),
                            "oy": random.uniform(-3, 3),
                            "color": fish.color
                        })
                        rare_tag = " ★ RARE!" if getattr(fish, 'rare', False) else ""
                        self.show_message(f"Caught {fish.name}! +{fish.value} gold{rare_tag}", 60)
                        for _ in range(10):
                            self.particles.append(CoinParticle(
                                fish.x, fish.y, b.x, b.y, fish.value
                            ))
                        break

        # animal observation
        for b in self.boats:
            self.try_observe_animal(b)

        # particles
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        # level up effects
        for eff in self.level_up_effects[:]:
            eff.update()
            if not eff.alive:
                self.level_up_effects.remove(eff)

        # merchant
        if self.merchant and self.merchant.alive:
            self.merchant.update(self.boats, self.ocean)
            if not self.merchant.alive:
                self.merchant = None
        else:
            self.merchant_timer += 1
            if self.merchant_timer > 600 + random.randint(0, 600):
                if random.random() < 0.3:
                    self.merchant = Merchant()
                    self.show_message("A traveling merchant approaches! Press M to trade.", 120, (255, 215, 0))
                self.merchant_timer = 0

        # wave logic
        if len(self.monsters) == 0:
            self.wave_timer += 1
            if self.wave_timer > 120:
                self.wave += 1
                self.wave_timer = 0
                self.ui.transition_alpha = 255
                self.init_wave()
                self.show_message(f"Wave {self.wave} begins!", 120)
                # level up effect on wave clear
                for b in self.boats:
                    bx, by = b.get_pos()
                    self.level_up_effects.append(LevelUpEffect(bx, by))
                    self.add_xp(20 + self.wave * 5)
        else:
            self.wave_timer = 0

        if self.ui.transition_alpha > 0:
            self.ui.transition_alpha -= 3
            if self.ui.transition_alpha < 0:
                self.ui.transition_alpha = 0

        if self.message_timer > 0:
            self.message_timer -= 1

        for b in self.boats:
            if b.hp <= 0:
                self.game_over = True
                break

        self.spawn_cooldown += 1
        spawn_delay = max(120, 300 - self.wave * 15)
        if self.spawn_cooldown > spawn_delay and len(self.monsters) < min(3 + self.wave // 2, 6):
            self.monsters.append(Monster(self.wave))
            self.spawn_cooldown = 0

    def respawn_animals(self, group):
        if not group:
            return
        group[:] = [a for a in group if a.alive]
        if group and len(group) < 2 and random.random() < 0.01:
            cls = type(group[0])
            group.append(cls())
        elif not group:
            pass

    def draw(self, surf):
        now = pygame.time.get_ticks() * 0.001
        weather = self.ocean.weather
        storm_i = self.ocean.storm_intensity

        # Camera sway (cinematic boat rocking)
        shake_x = int(3 * math.sin(now * 0.3))
        shake_y = int(2 * math.sin(now * 0.5 + 1.0))

        # sky gradient based on weather
        if weather == "storm":
            sky_colors = [(40, 40, 60), (50, 45, 65), (60, 55, 80), (50, 50, 70)]
        elif weather == "cloudy":
            sky_colors = [(180, 160, 140), (160, 170, 180), (150, 170, 200), (140, 160, 190)]
        else:
            sky_colors = [(45, 25, 75), (100, 40, 100), (220, 80, 60), (255, 160, 50)]

        for i in range(SEA_LEVEL):
            frac = i / SEA_LEVEL
            if frac < 0.3:
                c = lerp_col(sky_colors[0], sky_colors[1], frac / 0.3)
            elif frac < 0.6:
                c = lerp_col(sky_colors[1], sky_colors[2], (frac - 0.3) / 0.3)
            else:
                c = lerp_col(sky_colors[2], sky_colors[3], (frac - 0.6) / 0.4)
            pygame.draw.line(surf, c, (0, i), (W, i))

        # Sun glow (large halo)
        if weather != "storm":
            sun_x, sun_y = 850, SEA_LEVEL - 15
            sun_visible = 1.0 if weather == "clear" else 0.3
            # large atmospheric glow
            for r in range(120, 10, -10):
                alpha = int(max(0, (120 - r) * 2 * sun_visible))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 180, 60, max(alpha, 1)), (r, r), r)
                surf.blit(s, (sun_x - r, sun_y - r + shake_y))
            # inner glow
            for r in range(60, 10, -10):
                alpha = int(max(0, (60 - r) * 4 * sun_visible))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 220, 100, max(alpha, 1)), (r, r), r)
                surf.blit(s, (sun_x - r, sun_y - r + shake_y))
            # setting sun (half circle clipped at horizon)
            sun_clip = pygame.Rect(sun_x - 50, sun_y + shake_y - 50, 100, 100)
            sun_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            sun_center = (50, 50 - 10)
            pygame.draw.circle(sun_surf, (255, 200, 80 + int(55 * sun_visible)),
                             sun_center, 40)
            pygame.draw.circle(sun_surf, (255, 240, 180 + int(15 * sun_visible)),
                             sun_center, 30)
            # clip bottom half to horizon
            clip_y = 50 + 10
            if clip_y < 100:
                sun_surf.fill((0, 0, 0, 0), (0, clip_y, 100, 100 - clip_y))
            surf.blit(sun_surf, (sun_x - 50, sun_y + shake_y - 50))
            # Sun rays (god rays)
            if weather == "clear":
                for i in range(16):
                    a = -math.pi / 2 + math.radians((i - 8) * 6)
                    for j in range(4):
                        r1 = 50 + j * 35
                        r2 = r1 + 30
                        alpha = max(0, 25 - j * 6)
                        sx1 = sun_x + math.cos(a) * r1
                        sy1 = sun_y + shake_y + math.sin(a) * r1
                        sx2 = sun_x + math.cos(a) * r2
                        sy2 = sun_y + shake_y + math.sin(a) * r2
                        s = pygame.Surface((W, H), pygame.SRCALPHA)
                        pygame.draw.line(s, (255, 200, 80, int(alpha * sun_visible)),
                                        (sx1, sy1), (sx2, sy2), 3 - j)
                        surf.blit(s, (0, 0))

        # Distant island silhouettes on horizon
        if weather != "storm":
            vis = 1.0 if weather == "clear" else 0.6
            islands = [
                (120, SEA_LEVEL - 3, 90, 45, 30),
                (380, SEA_LEVEL - 2, 130, 60, 45),
                (680, SEA_LEVEL - 3, 100, 50, 35),
                (980, SEA_LEVEL - 2, 150, 70, 50),
            ]
            for ix, iy, iw, ih, peak_x in islands:
                iy = iy + shake_y
                island_surf = pygame.Surface((iw + 10, ih + 10), pygame.SRCALPHA)
                base_col = (45, 35, 55)
                haze = int(30 * (1 - vis))
                col = (base_col[0] + haze, base_col[1] + haze, base_col[2] + haze)
                alpha = int(180 * vis)
                # mountain shape
                pts = [(5, ih), (5 + peak_x, 5), (iw - 5, ih)]
                pygame.draw.polygon(island_surf, (*col, alpha), pts)
                # hill on left side
                pts2 = [(5, ih), (5 + peak_x // 2, 5 + ih // 3), (5 + peak_x * 2 // 3, ih)]
                pygame.draw.polygon(island_surf, (*col, int(alpha * 0.7)), pts2)
                # beach strip
                pygame.draw.ellipse(island_surf, (60, 50, 45, alpha),
                                   (5, ih - 6, iw - 10, 8))
                # palm tree silhouette on island
                for tree_x in [peak_x * 0.3, peak_x * 1.2]:
                    tx = 5 + tree_x
                    ty = 5 + ih * 0.25 + 10 * math.sin(tree_x)
                    pygame.draw.line(island_surf, (30, 25, 35, alpha),
                                    (tx, ty), (tx, ty + 12), 2)
                    for frond in range(4):
                        fa = math.radians(frond * 40 - 60)
                        fx = tx + math.cos(fa) * 8
                        fy = ty + math.sin(fa) * 4
                        pygame.draw.line(island_surf, (40, 35, 45, alpha),
                                        (tx, ty), (fx, fy), 1)
                surf.blit(island_surf, (ix - iw // 2 - 5, iy - ih))

        # Clouds (sunset colors for clear weather)
        if weather == "storm":
            cloud_data = [(150, 50, 1.8, (60, 60, 80)), (450, 35, 1.5, (50, 50, 70)),
                          (700, 65, 1.6, (70, 65, 85)), (300, 80, 1.2, (55, 55, 75)),
                          (550, 90, 1.4, (65, 60, 80))]
            cloud_colors = [(60, 60, 80), (50, 50, 70), (70, 65, 85), (55, 55, 75), (65, 60, 80)]
        elif weather == "cloudy":
            cloud_data = [(150, 50, 1.2, None), (450, 35, 0.9, None), (700, 65, 1.0, None),
                          (300, 80, 0.6, None), (200, 100, 1.1, None), (600, 55, 0.8, None)]
            cloud_colors = [(220, 180, 160), (200, 190, 180), (210, 180, 170),
                           (190, 200, 210), (220, 170, 150), (200, 200, 210)]
        else:
            cloud_data = [(150, 50 + shake_y * 0.3, 1.2, None),
                          (450, 35 + shake_y * 0.2, 0.9, None),
                          (700, 65 + shake_y * 0.3, 1.0, None),
                          (300, 80 + shake_y * 0.2, 0.6, None),
                          (900, 45 + shake_y * 0.3, 0.8, None)]
            cloud_colors = [(255, 200, 120), (255, 180, 100), (240, 160, 90),
                           (255, 200, 140), (255, 170, 80)]
        for idx, (cx, cy, s, _) in enumerate(cloud_data):
            cc = cloud_colors[idx] if idx < len(cloud_colors) else (255, 255, 255)
            for i in range(-2, 3):
                alpha = int(160 + 60 * math.sin(now * 0.1 + cx + i))
                if weather != "storm":
                    alpha = min(alpha, 200)
                c = pygame.Surface((int(55 * s), int(25 * s)), pygame.SRCALPHA)
                c.fill((cc[0], cc[1], cc[2], alpha))
                surf.blit(c, (cx + i * 35 * s - 25 * s, cy - 10 * s))

        # ocean
        self.ocean.draw(surf)

        # underwater creatures
        for j in self.jellyfish_list:
            if j.y > SEA_LEVEL:
                j.draw(surf)

        # fish
        for f in self.fish_list:
            if f.y > SEA_LEVEL:
                f.draw(surf)

        # turtles
        for t in self.turtles:
            if t.y > SEA_LEVEL:
                t.draw(surf)

        # whales
        for w in self.whales:
            if w.y > SEA_LEVEL:
                w.draw(surf)

        # dolphins
        for d in self.dolphins:
            d.draw(surf)

        # manta rays
        for m in self.manta_rays:
            if m.y > SEA_LEVEL:
                m.draw(surf)

        # birds
        for b in self.birds:
            if b.y < SEA_LEVEL:
                b.draw(surf)

        # treasures
        for t in self.treasures:
            if t.y > SEA_LEVEL:
                t.draw(surf)

        # monsters
        for m in self.monsters:
            m.draw(surf)

        # boats
        for b in self.boats:
            b.draw(surf)

        # thrown fish
        for tf in self.thrown_fish:
            tf.draw(surf)

        # projectiles
        for p in self.projectiles:
            p.draw(surf)

        # merchant
        if self.merchant and self.merchant.alive:
            self.merchant.draw(surf)

        # particles
        for p in self.particles:
            p.draw(surf)

        # level up effects
        for eff in self.level_up_effects:
            eff.draw(surf)

        # Warm amber overlay for cinematic sunset feel
        if weather != "storm":
            warmth = pygame.Surface((W, H), pygame.SRCALPHA)
            warmth.fill((180, 100, 40, 25))
            surf.blit(warmth, (0, 0))
            # vignette effect (darker edges)
            vignette = pygame.Surface((W, H), pygame.SRCALPHA)
            for i in range(H):
                dist_top = i
                dist_bot = H - i
                dist_l = min(i, W)
                edge_factor = min(dist_top, dist_bot) / (H * 0.35)
                edge_factor = max(0, 1 - edge_factor)
                alpha = int(70 * edge_factor * edge_factor)
                if alpha > 0:
                    pygame.draw.line(vignette, (0, 0, 0, alpha), (0, i), (W, i))
            # side vignette
            for side_x in range(80):
                alpha = int(50 * (1 - side_x / 80))
                pygame.draw.line(vignette, (0, 0, 0, alpha), (side_x, 0), (side_x, H))
                pygame.draw.line(vignette, (0, 0, 0, alpha), (W - side_x - 1, 0), (W - side_x - 1, H))
            surf.blit(vignette, (0, 0))

        # UI
        self.ui.draw(surf)

        # pause
        if self.paused:
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(160)
            overlay.fill((0, 0, 0))
            surf.blit(overlay, (0, 0))
            txt = self.ui.big_font.render("PAUSED", True, (255, 255, 255))
            r = txt.get_rect(center=(W // 2, H // 2))
            surf.blit(txt, r)
            t2 = self.ui.font.render("Press ESC to continue", True, (200, 200, 200))
            r2 = t2.get_rect(center=(W // 2, H // 2 + 40))
            surf.blit(t2, r2)

        # game over
        if self.game_over:
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            surf.blit(overlay, (0, 0))
            t1 = self.ui.big_font.render("GAME OVER", True, (255, 100, 100))
            r1 = t1.get_rect(center=(W // 2, H // 2 - 50))
            surf.blit(t1, r1)
            if self.two_player and len(self.boats) > 1:
                stats_str = f"P1 Score: {self.boats[0].score}  Gold: {self.boats[0].gold}"
                stats_str2 = f"P2 Score: {self.boats[1].score}  Gold: {self.boats[1].gold}"
                t2 = self.ui.font.render(stats_str, True, (100, 200, 255))
                surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2))
                t2b = self.ui.font.render(stats_str2, True, (255, 180, 100))
                surf.blit(t2b, (W // 2 - t2b.get_width() // 2, H // 2 + 25))
            else:
                stats_str = f"Score: {self.boats[0].score}  Gold: {self.boats[0].gold}"
                t2 = self.ui.font.render(stats_str, True, (255, 215, 0))
                surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2))
            lvl_str = f"Level: {self.level}  Wave: {self.wave}  Fish: {self.boats[0].fish_count}"
            t3 = self.ui.small_font.render(lvl_str, True, (200, 200, 200))
            surf.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 50))
            t4 = self.ui.font.render("Press R to restart", True, (200, 200, 200))
            r4 = t4.get_rect(center=(W // 2, H // 2 + 80))
            surf.blit(t4, r4)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Viana - Ocean Adventure")
    clock = pygame.time.Clock()
    game = Game()
    running = True

    # icon
    icon = pygame.Surface((32, 32))
    icon.fill((20, 80, 140))
    pygame.draw.polygon(icon, (120, 60, 30), [(16, 20), (6, 28), (26, 28)])
    pygame.draw.polygon(icon, (240, 240, 220), [(16, 8), (28, 20), (16, 22)])
    pygame.draw.circle(icon, (255, 215, 0), (16, 16), 3)
    pygame.display.set_icon(icon)

    while running:
        running = game.handle_events()
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
