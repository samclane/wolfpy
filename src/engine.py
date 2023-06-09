"""
Engine for FPS games using raycasting.
Based on https://github.com/jdah/doomenstein-3d/blob/main/src/main_wolf.c
"""

import json
import math
import os
import random
import sys

from vector import Vector2D, Hit

import openai
import pygame
from noise import pnoise2

openai.api_key = os.getenv("OPENAI_API_KEY")

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class Map:
    def __init__(self, data, size):
        self.data = data
        self.size = size

class PerlinMap(Map):
    size: int
    data: list[int]

    def __init__(self, seed: int, size: int, octaves=4, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024):
        self.size = size
        if seed is None:
            seed = random.randint(0, 9999)

        scale = 8.0
        threshold = 0.2

        self.data = []

        for y in range(size):
            for x in range(size):
                value = pnoise2(x / scale, y / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=repeatx, repeaty=repeaty, base=seed)
                if value > threshold:
                    self.data.append(1)  # Wall
                else:
                    self.data.append(0)  # Empty space

class LLMMap(Map):
    # can put you inside walls sometimes 
    size: int
    data: list[int]

    def __init__(self, size: int):
        self.size = size
        self.user_prompt = f"""As a flat JSON array of 0s and 1s, give a {size}x{size} maze:"""
        completion = openai.Completion.create(
            model="text-davinci-003",
            prompt=self.user_prompt,
            max_tokens=300,
        )
        self.data = json.loads(completion.choices[0].text)

class HeldItem:
    def __init__(self, path: str):
        self.sprite = pygame.image.load(path).convert_alpha()
    
    def render(self, state: "State", item_offset: float = 0):
        """Render the item to the bottom middle screen."""
        x = SCREEN_WIDTH // 2 - self.sprite.get_width() // 2
        y = SCREEN_HEIGHT - self.sprite.get_height() + item_offset
        state.pixel_buffer.blit(self.sprite, (x, y))

class State:
    def __init__(self, map: Map, items: list[HeldItem]):
        self.pixel_buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.pos = Vector2D(2, 2)
        self.dir = Vector2D(-1, 0.1)
        self.plane = Vector2D(0, 0.66)
        self.map = map
        self.items: list[HeldItem] = items
        self.bobbing_offset = 0.

    def draw_pixel(self, x, y, color):
        x, y = int(x), int(y)
        self.pixel_buffer.set_at((x, y), color)  # type: ignore

    def vertical_line(self, x: int, y1: int, y2: int, color):
        pygame.draw.line(self.pixel_buffer, color, (x, y1), (x, y2))

    def rotate(self, rot):
        self.dir = Vector2D(
            self.dir.x * math.cos(rot) - self.dir.y * math.sin(rot),
            self.dir.x * math.sin(rot) + self.dir.y * math.cos(rot),
        )
        self.plane = Vector2D(
            self.plane.x * math.cos(rot) - self.plane.y * math.sin(rot),
            self.plane.x * math.sin(rot) + self.plane.y * math.cos(rot),
        )


class ColorMap:
    def __init__(self, colors: dict, floor: str, ceiling: str):
        self.colors = colors
        self.floor = floor
        self.ceiling = ceiling

    def __getitem__(self, key):
        return self.colors[key]


def render(s: State, color_map: ColorMap):
    for x in range(SCREEN_WIDTH):
        xcam = 2 * x / SCREEN_WIDTH - 1
        dir = Vector2D(s.dir.x + s.plane.x * xcam, s.dir.y + s.plane.y * xcam)
        pos = s.pos
        ipos = Vector2D(int(pos.x), int(pos.y))

        # distance ray must travel from one x/y side to the next
        delta_dist = Vector2D(
            1e30 if abs(dir.x) < 1e-20 else abs(1 / dir.x),
            1e30 if abs(dir.y) < 1e-20 else abs(1 / dir.y),
        )

        # distance from start to first x/y side
        side_dist = Vector2D(
            delta_dist.x * ((pos.x - ipos.x) if dir.x < 0 else (ipos.x + 1 - pos.x)),
            delta_dist.y * ((pos.y - ipos.y) if dir.y < 0 else (ipos.y + 1 - pos.y)),
        )

        # integer direction to step in x/y calculated overall diff
        step = Vector2D(-1 if dir.x < 0 else 1, -1 if dir.y < 0 else 1)

        # dda hit
        hit = Hit(0, 0, Vector2D(0, 0))

        while hit.val == 0:
            if side_dist.x < side_dist.y:
                side_dist.x += delta_dist.x
                ipos.x += step.x
                hit.side = 0
            else:
                side_dist.y += delta_dist.y
                ipos.y += step.y
                hit.side = 1

            if 0 <= ipos.x < s.map.size and 0 <= ipos.y < s.map.size:
                hit.val = s.map.data[ipos.x + ipos.y * s.map.size]
            else:
                break

        color = color_map[hit.val]

        if hit.side == 1:
            # darken color if hit side is y
            r = int(color[1:3], 16) >> 1
            g = int(color[3:5], 16) >> 1
            b = int(color[5:7], 16) >> 1
            color = f"#{r:02x}{g:02x}{b:02x}"

        hit.pos = Vector2D(pos.x + side_dist.x, pos.y + side_dist.y)

        dperp = (
            (side_dist.x - delta_dist.x)
            if hit.side == 0
            else (side_dist.y - delta_dist.y)
        )

        h = int(SCREEN_HEIGHT / (dperp + 1e-20))
        y0 = max((SCREEN_HEIGHT / 2) - (h / 2), 0)
        y1 = min((SCREEN_HEIGHT / 2) + (h / 2), SCREEN_HEIGHT - 1)

        pygame.draw.rect(s.pixel_buffer, color_map.floor, (x, 0, 1, y0))
        pygame.draw.rect(s.pixel_buffer, color, (x, y0, 1, y1 - y0))
        pygame.draw.rect(s.pixel_buffer, color_map.ceiling, (x, y1, 1, SCREEN_HEIGHT - y1))


def is_valid_position(pos: Vector2D, map: Map) -> bool:
    x, y = int(pos.x), int(pos.y)
    if x < 0 or x >= map.size or y < 0 or y >= map.size:
        return False
    return map.data[x + y * map.size] == 0


def handle_keys(s: State):
    keys = pygame.key.get_pressed()
    move_speed = 0.1
    bobbing_speed = 0.15

    moved = False

    if keys[pygame.K_UP]:
        new_pos = s.pos + s.dir * move_speed
        if is_valid_position(new_pos, s.map):
            s.pos = new_pos
            moved = True

    if keys[pygame.K_DOWN]:
        new_pos = s.pos - s.dir * move_speed
        if is_valid_position(new_pos, s.map):
            s.pos = new_pos
            moved = True

    if moved:
        s.bobbing_offset += bobbing_speed

    if keys[pygame.K_LEFT]:
        s.rotate(0.1)

    if keys[pygame.K_RIGHT]:
        s.rotate(-0.1)



def main_loop(s: State, color_map: ColorMap):
    handle_keys(s)
    render(s, color_map)
    bobbing_amplitude = 5
    bobbing_offset = int(math.sin(s.bobbing_offset) * bobbing_amplitude)
    for item in s.items:
        item.render(s, bobbing_offset)
    screen.blit(s.pixel_buffer, (0, 0))
    pygame.display.flip()
    clock.tick(144)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    # m = Map([
    #     1, 1, 1, 1, 1, 1, 1, 1,
    #     1, 0, 0, 0, 0, 0, 0, 1,
    #     1, 0, 0, 0, 0, 3, 0, 1,
    #     1, 0, 0, 0, 0, 0, 0, 1,
    #     1, 0, 2, 0, 4, 4, 0, 1,
    #     1, 0, 0, 0, 4, 0, 0, 1,
    #     1, 0, 3, 0, 0, 0, 0, 1,
    #     1, 1, 1, 1, 1, 1, 1, 1,
    # ], 8)
    # m = PerlinMap(42, 16)
    m = LLMMap(10)
    s = State(m, [HeldItem("./res/gun.png")])
    color_map = ColorMap(
        {
            0: "#000000",
            1: "#ffffff",
            2: "#00ff00",
            3: "#0000ff",
            4: "#ff0000",
            5: "#ffff00",
            6: "#00ffff",
        },
        "#000000",
        "#cccccc",
    )
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        main_loop(s, color_map)
