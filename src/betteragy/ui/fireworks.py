"""Particle-physics firework animation engine for Quota Reset celebrations."""

import math
import random
import time
from typing import List, Optional, Tuple
from rich.console import Console
from rich.text import Text

from .key_listener import KEY_BACK, KEY_ESC, KEY_QUIT, KeyListener
from .theme_manager import get_theme_manager

SPARK_CHARS = ["*", "+", "o", "x", ".", "•", "✦", "✧"]
COLORS = ["bright_red", "bright_green", "bright_yellow", "bright_cyan", "bright_magenta", "bright_white"]


class Particle:
    """Individual firework spark with 2D kinematics and decay."""

    def __init__(self, x: float, y: float, vx: float, vy: float, color: str, life: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life

    def step(self, gravity: float = 0.09, drag: float = 0.95) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vx *= drag
        self.vy = (self.vy + gravity) * drag
        self.life -= 1

    @property
    def is_alive(self) -> bool:
        return self.life > 0

    @property
    def char(self) -> str:
        ratio = self.life / max(self.max_life, 1)
        if ratio > 0.7:
            return random.choice(["*", "✦", "O"])
        elif ratio > 0.4:
            return random.choice(["+", "o", "x"])
        return "."


class FireworkRocket:
    """Ascending rocket that bursts into expanding particle ring."""

    def __init__(self, x: int, start_y: int, target_y: int):
        self.x = float(x)
        self.y = float(start_y)
        self.target_y = float(target_y)
        self.vy = -random.uniform(1.2, 1.8)
        self.color = random.choice(COLORS)
        self.exploded = False

    def step(self) -> Optional[List[Particle]]:
        if self.exploded:
            return None
        self.y += self.vy
        if self.y <= self.target_y:
            self.exploded = True
            return self._burst()
        return None

    def _burst(self) -> List[Particle]:
        particles = []
        burst_color = random.choice(COLORS)
        count = random.randint(22, 34)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.6, 2.4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.52
            life = random.randint(10, 20)
            particles.append(Particle(self.x, self.y, vx, vy, burst_color, life))
        return particles


def render_fireworks_frame(
    width: int, height: int, rockets: List[FireworkRocket], particles: List[Particle], title: str = ""
) -> Text:
    """Compose a 2D ASCII text buffer with rockets, particles, and celebration banner."""
    grid = [[" " for _ in range(width)] for _ in range(height)]
    color_grid = [["" for _ in range(width)] for _ in range(height)]

    for p in particles:
        ix, iy = int(round(p.x)), int(round(p.y))
        if 0 <= ix < width and 0 <= iy < height:
            grid[iy][ix] = p.char
            color_grid[iy][ix] = p.color

    for r in rockets:
        if not r.exploded:
            ix, iy = int(round(r.x)), int(round(r.y))
            if 0 <= ix < width and 0 <= iy < height:
                grid[iy][ix] = "^"
                color_grid[iy][ix] = r.color

    banner = [
        " +------------------------------------------------------------+ ",
        " |       [*]  AI MODEL QUOTA RESTORED! CELEBRATION  [*]       | ",
        f" |        {title[:48]:^48}        | ",
        " |         Gemini 3.1 Pro, Flash & Claude Ready!              | ",
        " |          >> Press [ESC] or [q] to return to TUI <<         | ",
        " +------------------------------------------------------------+ ",
    ]
    b_start_y = max(2, (height - len(banner)) // 2)
    b_w = len(banner[0])
    b_start_x = max(0, (width - b_w) // 2)

    for r_idx, b_line in enumerate(banner):
        gy = b_start_y + r_idx
        if 0 <= gy < height:
            for c_idx, ch in enumerate(b_line):
                gx = b_start_x + c_idx
                if 0 <= gx < width:
                    grid[gy][gx] = ch
                    color_grid[gy][gx] = "bold cyan" if r_idx == 4 else ("bold yellow" if r_idx in (1, 3) else "bold white")

    result = Text()
    for y in range(height):
        for x in range(width):
            ch = grid[y][x]
            col = color_grid[y][x]
            if ch != " ":
                result.append(ch, style=col or "white")
            else:
                result.append(" ")
        if y < height - 1:
            result.append("\n")
    return result


def play_fireworks_celebration(
    console: Console, duration: Optional[float] = None, title: str = "7-Day Quota Refreshed 100%!"
) -> None:
    """Play full terminal firework particle animation until Escape or q is pressed."""
    width = max(console.width, 70)
    height = max(console.height - 2, 22)
    rockets: List[FireworkRocket] = []
    particles: List[Particle] = []

    start_time = time.time()
    next_rocket_time = 0.0

    with KeyListener() as listener:
        while True:
            now = time.time()
            if duration is not None and duration > 0 and (now - start_time) >= duration:
                break

            if now >= next_rocket_time and len(rockets) < 7:
                rx = random.randint(10, width - 10)
                ty = random.randint(4, height // 2)
                rockets.append(FireworkRocket(rx, height - 2, ty))
                next_rocket_time = now + random.uniform(0.18, 0.4)

            for r in list(rockets):
                new_sparks = r.step()
                if new_sparks:
                    particles.extend(new_sparks)
            rockets = [r for r in rockets if not r.exploded]

            for p in list(particles):
                p.step()
            particles = [p for p in particles if p.is_alive]

            frame = render_fireworks_frame(width, height, rockets, particles, title=title)
            console.clear()
            console.print(frame)

            key = listener.read_key()
            if key in (KEY_ESC, KEY_QUIT, "q", "Q", KEY_BACK, "\x1b"):
                break
            time.sleep(0.04)
