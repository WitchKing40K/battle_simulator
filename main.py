"""Battle simulator map prototype. Run with: python main.py."""
from dataclasses import dataclass
import math

import pygame


@dataclass
class Camera:
    """Map coordinates are meters, with positive Y pointing north (up)."""

    x: float = 0.0
    y: float = 0.0
    scale: float = 20.0  # pixels per meter

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
        self.scale = max(0.05, min(1000.0, self.scale))
        after = self.to_world(position, size)
        self.x += anchor[0] - after[0]
        self.y += anchor[1] - after[1]


def grid_spacing(scale):
    """Choose readable 1/2/5 meter intervals at any zoom."""
    target = 60 / scale
    power = 10 ** math.floor(math.log10(target))
    return next(n * power for n in (1, 2, 5, 10) if n * power >= target)


def draw_map(screen, camera, font, selected):
    screen.fill('#151e28')
    size = screen.get_size()
    spacing = grid_spacing(camera.scale)
    left, top = camera.to_world((0, 0), size)
    right, bottom = camera.to_world(size, size)
    for axis, low, high in ((0, left, right), (1, bottom, top)):
        for index in range(math.ceil(low / spacing), math.floor(high / spacing) + 1):
            value = index * spacing
            point = camera.to_screen((value, value), size)
            color = '#354555' if index % 5 == 0 else '#253340'
            if axis == 0:
                pygame.draw.line(screen, color, (point[0], 0), (point[0], size[1]))
                label_pos = (point[0] + 5, size[1] - 25)
            else:
                pygame.draw.line(screen, color, (0, point[1]), (size[0], point[1]))
                label_pos = (8, point[1] + 4)
            screen.blit(font.render(f'{value:g} m', True, '#8296a9'), label_pos)
    origin = camera.to_screen((0, 0), size)
    pygame.draw.line(screen, '#567b8d', (origin[0], 0), (origin[0], size[1]))
    pygame.draw.line(screen, '#567b8d', (0, origin[1]), (size[0], origin[1]))
    if selected is not None:
        point = camera.to_screen(selected, size)
        pygame.draw.circle(screen, '#ffc875', point, 7, 2)
        pygame.draw.line(screen, '#ffc875', (point[0] - 12, point[1]), (point[0] + 12, point[1]))
        pygame.draw.line(screen, '#ffc875', (point[0], point[1] - 12), (point[0], point[1] + 12))
    lines = [
        'BATTLE SIMULATOR  /  MAP',
        'Drag: pan   |   Wheel: zoom   |   Click: coordinates   |   Home: reset   |   Esc: quit',
        f'Grid: {spacing:g} m   |   Scale: {camera.scale:.2f} pixels/m   |   +X east, +Y north',
        ('Click the map to select a position.' if selected is None else
         f'Selected: X = {selected[0]:.2f} m, Y = {selected[1]:.2f} m'),
    ]
    panel = pygame.Surface((size[0], 122), pygame.SRCALPHA)
    panel.fill((12, 19, 27, 235))
    screen.blit(panel, (0, 0))
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, '#ffc875' if i == 3 else '#d4e0eb'), (18, 14 + i * 25))


def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1100, 760), pygame.RESIZABLE)
    pygame.display.set_caption('Battle Simulator — Map prototype')
    font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    camera = Camera()
    selected = None
    press = None
    dragging = False
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_HOME:
                        camera = Camera()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
                    if press is None:
                        press = (event.button, event.pos)
                        dragging = False
                elif event.type == pygame.MOUSEMOTION and press is not None:
                    if not dragging and math.dist(event.pos, press[1]) >= 4:
                        dragging = True
                        camera.pan((event.pos[0] - press[1][0], event.pos[1] - press[1][1]))
                    elif dragging:
                        camera.pan(event.rel)
                elif event.type == pygame.MOUSEBUTTONUP and press is not None and event.button == press[0]:
                    if not dragging:
                        selected = camera.to_world(event.pos, screen.get_size())
                    press = None
                    dragging = False
                elif event.type == pygame.WINDOWFOCUSLOST:
                    press = None
                    dragging = False
                elif event.type == pygame.MOUSEWHEEL:
                    camera.zoom(event.y, pygame.mouse.get_pos(), screen.get_size())
            draw_map(screen, camera, font, selected)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
