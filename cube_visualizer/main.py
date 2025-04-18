import pygame
import sys
import math
from pygame.locals import QUIT, KEYDOWN, K_LEFT, K_RIGHT, K_UP, K_DOWN, K_1, K_2

# Screen settings
WIDTH, HEIGHT = 800, 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# 4D objects definitions
# Tesseract (hypercube) vertices and edges
tesseract_vertices = [[x, y, z, w] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1) for w in (-1, 1)]
tesseract_edges = []
for i, v in enumerate(tesseract_vertices):
    for j, u in enumerate(tesseract_vertices):
        if j > i and sum(abs(v[k] - u[k]) for k in range(4)) == 2:
            tesseract_edges.append((i, j))

# 4-simplex (5-cell) approximate vertices and edges
simplex_vertices = [
    [1, 1, 1, -1],
    [1, -1, -1, -1],
    [-1, 1, -1, -1],
    [-1, -1, 1, -1],
    [0, 0, 0, 3]
]
simplex_edges = [(i, j) for i in range(len(simplex_vertices))
                 for j in range(i+1, len(simplex_vertices))]

objects = {
    'Tesseract': (tesseract_vertices, tesseract_edges),
    '4-Simplex': (simplex_vertices, simplex_edges)
}
object_names = list(objects.keys())
current_idx = 0

# Rotation angles and speeds for 4D planes
angles = {'xy': 0, 'xz': 0, 'xw': 0, 'yz': 0, 'yw': 0, 'zw': 0}
# disable all rotation speeds to keep object static
speeds = dict.fromkeys(angles.keys(), 0.0)

# Projection settings
distance_4d = 5
projection_scale = 200

def rotate_4d(point):
    x, y, z, w = point
    for plane, angle in angles.items():
        c, s = math.cos(angle), math.sin(angle)
        if plane == 'xy':
            x, y = x * c - y * s, x * s + y * c
        elif plane == 'xz':
            x, z = x * c - z * s, x * s + z * c
        elif plane == 'xw':
            x, w = x * c - w * s, x * s + w * c
        elif plane == 'yz':
            y, z = y * c - z * s, y * s + z * c
        elif plane == 'yw':
            y, w = y * c - w * s, y * s + w * c
        elif plane == 'zw':
            z, w = z * c - w * s, z * s + w * c
    return [x, y, z, w]


def project_point_4d_to_2d(pt4d):
    x, y, z, w = rotate_4d(pt4d)
    # project 4D->3D
    factor4 = distance_4d / (distance_4d - w)
    x3, y3, z3 = x * factor4, y * factor4, z * factor4
    # project 3D->2D
    factor3 = projection_scale / (z3 + distance_4d)
    x2 = x3 * factor3 + WIDTH / 2
    y2 = y3 * factor3 + HEIGHT / 2
    return (int(x2), int(y2))


def draw_object(screen, name):
    vertices, edges = objects[name]
    points = [project_point_4d_to_2d(v) for v in vertices]
    for i, j in edges:
        pygame.draw.line(screen, WHITE, points[i], points[j], 1)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('4D Object Visualizer')
    font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    global current_idx
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                # number keys still switch objects
                if event.key == K_1:
                    current_idx = 0
                elif event.key == K_2:
                    current_idx = 1

        # no automatic rotation (speeds are zero)

        screen.fill(BLACK)
        name = object_names[current_idx]
        draw_object(screen, name)
        txt = font.render(f'Object: {name} (1:Tesseract 2:4-Simplex)', True, WHITE)
        screen.blit(txt, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()