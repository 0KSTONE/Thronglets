# main.py
# Basic Thronglets simulation using Pygame
# Start with two thronglets that move randomly and replicate over time.

import pygame
import random
import sys

# Configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BACKGROUND_COLOR = (30, 30, 30)
THRONGLET_COLOR = (100, 200, 100)
THRONGLET_RADIUS = 8
INITIAL_THRONGLETS = 2
REPLICATION_INTERVAL = 5000  # milliseconds

class Thronglet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.birth_time = pygame.time.get_ticks()

    def move(self):
        # Simple random walk
        dx = random.randint(-2, 2)
        dy = random.randint(-2, 2)
        self.x = max(0, min(WINDOW_WIDTH, self.x + dx))
        self.y = max(0, min(WINDOW_HEIGHT, self.y + dy))

    def should_replicate(self, current_time):
        # Replicate if enough time passed
        return (current_time - self.birth_time) >= REPLICATION_INTERVAL

    def draw(self, surface):
        pygame.draw.circle(surface, THRONGLET_COLOR, (int(self.x), int(self.y)), THRONGLET_RADIUS)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Thronglets Simulator")
    clock = pygame.time.Clock()

    # Initialize thronglets list
    thronglets = []
    for _ in range(INITIAL_THRONGLETS):
        x = random.randint(0, WINDOW_WIDTH)
        y = random.randint(0, WINDOW_HEIGHT)
        thronglets.append(Thronglet(x, y))

    running = True
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update thronglets
        new_thronglets = []
        for t in thronglets:
            t.move()
            if t.should_replicate(current_time):
                # Spawn new thronglet at parent's position
                child = Thronglet(t.x, t.y)
                new_thronglets.append(child)
                # Reset parent's birth_time
                t.birth_time = current_time
        thronglets.extend(new_thronglets)

        # Render
        screen.fill(BACKGROUND_COLOR)
        for t in thronglets:
            t.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
