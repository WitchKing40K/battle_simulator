"""Battle simulator map prototype. Run with: python main.py."""
from dataclasses import dataclass
import math
import random
from functools import lru_cache

import pygame

from maneuvers import angle_delta
from units import Army, MAP_SIZE, MAP_HALF
from selection import SelectionGesture, FormationGesture


def speed_buttons(size):
    width, height = size
    buttons = ((0, 'Pause'), (1, '1×'), (2, '2×'), (5, '5×'))
    left = width - 286
    for index, (speed, label) in enumerate(buttons):
        yield speed, label, pygame.Rect(left + index * 70, height - 48, 64, 34)


def draw_speed_controls(screen, font, speed):
    for multiplier, label, rect in speed_buttons(screen.get_size()):
        active = multiplier == speed
        pygame.draw.rect(screen, '#ffc875' if active else '#182532', rect, border_radius=5)
        pygame.draw.rect(screen, '#ffc875' if active else '#65798a', rect, 1, border_radius=5)
        text = font.render(label, True, '#182532' if active else '#d4e0eb')
        screen.blit(text, text.get_rect(center=rect.center))


@dataclass
class Camera:
    """Map coordinates are meters, with positive Y pointing north (up)."""

    x: float = 0.0
    y: float = 0.0
    scale: float = 0.14  # pixels per meter

    @classmethod
    def overview(cls, size):
        scale = max(0.02, min((size[0] - 80) / MAP_SIZE,
                              (size[1] - 202) / MAP_SIZE))
        return cls(y=61 / scale, scale=scale)

    def to_world(self, position, size):
        return (self.x + (position[0] - size[0] / 2) / self.scale,
                self.y - (position[1] - size[1] / 2) / self.scale)

    def to_screen(self, position, size):
        return (round(size[0] / 2 + (position[0] - self.x) * self.scale),
                round(size[1] / 2 - (position[1] - self.y) * self.scale))

    def pan(self, delta):
        self.x -= delta[0] / self.scale
        self.y += delta[1] / self.scale

    def zoom(self, steps, position, size):
        anchor = self.to_world(position, size)
        self.scale *= 1.2 ** max(-50, min(50, steps))
        self.scale = max(0.02, min(4.0, self.scale))
        after = self.to_world(position, size)
        self.x += anchor[0] - after[0]
        self.y += anchor[1] - after[1]


@lru_cache(maxsize=1)
def field_texture():
    """Stable grass detail, generated once and anchored to the world."""
    rng = random.Random(42)
    texture = pygame.Surface((1024, 1024))
    texture.fill('#708747')
    for _ in range(6000):
        color = rng.choice(('#73894a', '#6b8243', '#788e4d', '#698143'))
        pygame.draw.ellipse(texture, color,
                            (rng.randrange(-30, 1024), rng.randrange(-30, 1024),
                             rng.randrange(8, 55), rng.randrange(5, 35)))
    for _ in range(22000):
        x, y = rng.randrange(1024), rng.randrange(1024)
        color = rng.choice(('#829754', '#627c40', '#8b9b5b', '#758b49'))
        pygame.draw.line(texture, color, (x, y), (x + rng.randrange(-2, 3), y - 2))
    return texture


def draw_map(screen, camera, font):
    screen.fill('#30382b')
    size = screen.get_size()
    top_left = camera.to_screen((-MAP_HALF, MAP_HALF), size)
    bottom_right = camera.to_screen((MAP_HALF, -MAP_HALF), size)
    field = pygame.Rect(top_left, (bottom_right[0] - top_left[0],
                                   bottom_right[1] - top_left[1]))
    visible = field.clip(screen.get_rect())
    if visible.width and visible.height:
        texture = field_texture()
        ratio = texture.get_width() / field.width
        # Crop before scaling so zooming never allocates a map-sized image.
        left = max(0, math.floor((visible.left - field.left) * ratio))
        top = max(0, math.floor((visible.top - field.top) * ratio))
        right = min(1024, math.ceil((visible.right - field.left) * ratio))
        bottom = min(1024, math.ceil((visible.bottom - field.top) * ratio))
        source = pygame.Rect(left, top, right - left, bottom - top)
        dest = pygame.Rect(round(field.left + left / ratio),
                           round(field.top + top / ratio), 0, 0)
        dest.width = max(1, round(field.left + right / ratio) - dest.left)
        dest.height = max(1, round(field.top + bottom / ratio) - dest.top)
        screen.blit(pygame.transform.smoothscale(texture.subsurface(source), dest.size), dest)
    pygame.draw.rect(screen, '#c4ba83', field, 3)


def draw_facing(screen, center, heading, length, color):
    if length < 3:
        return
    dx, dy = math.cos(heading), -math.sin(heading)
    tip = (round(center[0] + dx * length), round(center[1] + dy * length))
    base = (center[0] + dx * length * 0.45, center[1] + dy * length * 0.45)
    wing = max(2, length * 0.25)
    pygame.draw.line(screen, color, center, tip, 1)
    pygame.draw.polygon(screen, color, [tip, (base[0] - dy * wing, base[1] + dx * wing),
                                       (base[0] + dy * wing, base[1] - dx * wing)])


def draw_units(screen, camera, army):
    for unit in army.units:
        size = screen.get_size()
        points = [camera.to_screen(p, size) for p in unit.corners()]
        center = camera.to_screen((unit.x, unit.y), size)
        side = unit.size * camera.scale
        pygame.draw.polygon(screen, '#000000', points)
        if unit.size > 10:
            interior = [camera.to_screen(p, size) for p in unit.corners(padding=-5)]
            pygame.draw.polygon(screen, '#5799e0' if unit.team == 'friendly' else '#d65b57',
                                interior)
        draw_facing(screen, center, unit.facing,
                    max(3, side * 0.38) if side >= 6 else 0, '#eef2dc')
        if unit.selected:
            outline = [camera.to_screen(p, size)
                       for p in unit.corners(padding=3 / camera.scale)]
            pygame.draw.polygon(screen, '#ffe18a', outline, 2)


def draw_destinations(screen, camera, army, selected_only=False):
    """Draw selected orders, or all friendly orders for the Space overlay."""
    for unit in army.units:
        if unit.team != 'friendly' or (selected_only and not unit.selected):
            continue
        destination = unit.destination
        heading = unit.ordered_facing
        if destination is None:
            if (unit.engagement is not None or heading is None or
                    abs(angle_delta(heading, unit.facing)) <= 1e-6):
                continue
            destination = (unit.x, unit.y)
        center = camera.to_screen(destination, screen.get_size())
        current = camera.to_screen((unit.x, unit.y), screen.get_size())
        side = max(4, round(unit.size * camera.scale))
        color = '#ffe18a' if unit.selected else '#9edbfa'
        pygame.draw.line(screen, color, current, center, 1)
        points = [camera.to_screen(p, screen.get_size())
                  for p in unit.corners(destination, heading)]
        pygame.draw.polygon(screen, color, points, 2)
        pygame.draw.circle(screen, color, center, 3)
        if unit.ordered_facing is not None:
            draw_facing(screen, center, unit.ordered_facing, side * 0.7, color)


def draw_interface(screen, camera, font, army, gesture, formation):
    draw_destinations(screen, camera, army,
                      selected_only=not pygame.key.get_pressed()[pygame.K_SPACE])
    for unit, position in formation.targets(pygame.mouse.get_pos(), camera, screen.get_size(), army):
        center = camera.to_screen(position, screen.get_size())
        side = max(3, round(unit.size * camera.scale))
        rect = pygame.Rect(0, 0, side, side)
        rect.center = center
        end = camera.to_world(pygame.mouse.get_pos(), screen.get_size()) if formation.dragging else None
        heading = army.order_heading(formation.start, end)
        points = [camera.to_screen(p, screen.get_size())
                  for p in unit.corners(position, heading)]
        pygame.draw.polygon(screen, '#8de0ac', points, 2)
        draw_facing(screen, center, heading, side * 0.7, '#8de0ac')
    if gesture.dragging:
        a = camera.to_screen(gesture.start, screen.get_size())
        b = pygame.mouse.get_pos()
        rect = pygame.Rect(min(a[0], b[0]), min(a[1], b[1]),
                           abs(b[0] - a[0]), abs(b[1] - a[1]))
        pygame.draw.rect(screen, '#ffe18a', rect, 2)
    marching = any(u.destination is not None for u in army.selected)
    turning = any(u.ordered_facing is not None and
                  abs(angle_delta(u.ordered_facing, u.facing)) > 1e-6
                  for u in army.selected)
    state = 'Marching' if marching else 'Turning' if turning else 'Ready'
    combat_states = {u.combat_state for u in army.selected}
    combat_state = ', '.join(label for key, label in (
        ('closing', 'Closing to engage'),
        ('fighting', ', '.join(sorted({u.combat_outcome or 'Fighting'
                                      for u in army.selected if u.combat_state == 'fighting'}))),
        ('passive', 'Passively engaged')) if key in combat_states)
    if combat_state:
        state = f'{state}, {combat_state}' if marching or turning else combat_state
    hovered = army.hit(camera.to_world(pygame.mouse.get_pos(), screen.get_size()))
    strength = ''
    if hovered:
        strength = f'   |   Hovered: {hovered.men_alive} alive, {hovered.vigour:.1f} vigour'
        if hovered.combat_outcome:
            strength += f', {hovered.combat_outcome.lower()}'
    lines = [
        'BATTLE SIMULATOR  /  REAL TIME',
        'Left: select   |   Ctrl+left: toggle   |   Right drag: formation   |   Middle: pan   |   Wheel: zoom',
        'Field: 4 km x 4 km   |   Units: 50 m x 50 m   |   Space: all orders   |   Home: overview   |   Esc: quit',
        f'Selected: {len(army.selected)}   |   {state}   |   Blue: friendly   |   Red: enemy{strength}',
    ]
    panel = pygame.Surface((screen.get_width(), 122), pygame.SRCALPHA)
    panel.fill((12, 19, 27, 235))
    screen.blit(panel, (0, 0))
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, '#ffc875' if i == 3 else '#d4e0eb'), (18, 14 + i * 25))


def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1100, 760), pygame.RESIZABLE)
    pygame.display.set_caption('Battle Simulator — Real time tactics')
    font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    camera = Camera.overview(screen.get_size())
    army = Army.test_army()
    gesture = SelectionGesture()
    formation = FormationGesture()
    speed = 1
    panning = False
    running = True
    try:
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_HOME:
                        camera = Camera.overview(screen.get_size())
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    clicked_speed = next((multiplier for multiplier, _, rect
                                          in speed_buttons(screen.get_size())
                                          if rect.collidepoint(event.pos)), None)
                    if clicked_speed is not None:
                        if event.button == 1:
                            speed = clicked_speed
                        continue
                    if event.button == 1:
                        gesture.begin(event.pos, camera, screen.get_size(), army,
                                      toggle=bool(pygame.key.get_mods() & pygame.KMOD_CTRL))
                    elif event.button == 2:
                        panning = True
                    elif event.button == 3:
                        formation.begin(event.pos, camera, screen.get_size())
                elif event.type == pygame.MOUSEMOTION:
                    if panning:
                        camera.pan(event.rel)
                    gesture.motion(event.pos)
                    formation.motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        gesture.finish(event.pos, camera, screen.get_size(), army)
                    elif event.button == 2:
                        panning = False
                    elif event.button == 3:
                        formation.finish(event.pos, camera, screen.get_size(), army)
                elif event.type == pygame.WINDOWFOCUSLOST:
                    gesture.cancel()
                    formation.cancel()
                    panning = False
                elif event.type == pygame.MOUSEWHEEL:
                    camera.zoom(event.y, pygame.mouse.get_pos(), screen.get_size())
            # Extra updates keep simulation steps the same size at every speed.
            if running:
                for _ in range(speed):
                    army.update(dt)
            draw_map(screen, camera, font)
            draw_units(screen, camera, army)
            draw_interface(screen, camera, font, army, gesture, formation)
            draw_speed_controls(screen, font, speed)
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
