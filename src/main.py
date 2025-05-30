# main.py
# Combined Thronglet simulation with energy-based, randomized replication,
# food-seeking, and food-dropping behaviors using Pygame.

import pygame
import random
import sys
import logging
import os

# --- Configuration ---
CONFIG = {
    "WORLD_WIDTH": 800,
    "WORLD_HEIGHT": 600,
    "BACKGROUND_COLOR": (30, 30, 30),

    # Thronglet appearance
    "THRONGLET_COLOR": (100, 200, 100),
    "THRONGLET_RADIUS": 8,

    # Movement
    "WALK_SPEED": 2,
    "SEEK_SPEED": 2.5,

    # Energy & food
    "ENERGY_MAX": 50,
    "ENERGY_GAIN_PER_FOOD": 20,
    "REPLICATION_ENERGY_COST": 50,
    "DROP_FOOD_ENERGY_COST": 10,

    # Replication timing (mean interval in ms)
    "REPLICATION_INTERVAL_MEAN": 5000,

    # Initial population
    "INITIAL_THRONGLETS": 2,
}

# Setup logging
def setup_logging():    
    os.makedirs("data", exist_ok=True)
    RUN_NUMBER_FILE = "data/run_number.txt"
    if os.path.exists(RUN_NUMBER_FILE):
        with open(RUN_NUMBER_FILE, "r") as f:
            RUN_NUMBER = int(f.read().strip()) + 1
    else:
        RUN_NUMBER = 1
    with open(RUN_NUMBER_FILE, "w") as f:
        f.write(str(RUN_NUMBER))

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(f"../data/log_{RUN_NUMBER}.txt", mode='w'),
            logging.StreamHandler()
        ]
    )

# --- World stub for food management ---
class World:
    def __init__(self, config):
        self.config = config
        # simple set of food positions
        self.food = set()

    def get_nearest_food(self, x, y):
        if not self.food:
            return None
        # find nearest by Euclidean distance
        nearest = min(self.food, key=lambda p: (p[0]-x)**2 + (p[1]-y)**2)
        return nearest

    def consume_food_at(self, x, y):
        # consume if exact match
        if (x, y) in self.food:
            self.food.remove((x, y))
            return True
        return False

    def add_food_at(self, x, y):
        self.food.add((x, y))

# --- Thronglet Agent ---
class Thronglet:
    counter = 0  # Class-level counter

    def __init__(self, x, y, config):
        self.x = x
        self.y = y
        self.config = config
        self.energy = config["ENERGY_MAX"]
        now = pygame.time.get_ticks()
        self.next_replicate = now + self._random_interval()
        Thronglet.counter += 1
        self.id = Thronglet.counter

    def _random_interval(self):
        mean = self.config["REPLICATION_INTERVAL_MEAN"]
        return int(random.expovariate(1.0 / mean))

    def _apply_movement(self, dx, dy):
        self.x = max(0, min(self.config["WORLD_WIDTH"], self.x + dx))
        self.y = max(0, min(self.config["WORLD_HEIGHT"], self.y + dy))

    def move_random(self):
        dx = random.randint(-self.config["WALK_SPEED"], self.config["WALK_SPEED"])
        dy = random.randint(-self.config["WALK_SPEED"], self.config["WALK_SPEED"])
        self._apply_movement(dx, dy)
        logging.info(f"Thronglet {self.id} random move to ({self.x:.1f}, {self.y:.1f})")

    def move_away_from_others(self, thronglets, min_dist=5, speed=1):
        move_x, move_y = 0, 0
        count = 0
        for other in thronglets:
            if other is self:
                continue
            dx = self.x - other.x
            dy = self.y - other.y
            dist = (dx**2 + dy**2)**0.5
            if dist < min_dist and dist > 0:
                move_x += dx / dist
                move_y += dy / dist
                count += 1
        if count > 0:
            self._apply_movement(move_x * speed, move_y * speed)
            logging.info(f"Thronglet {self.id} moved away from others to ({self.x:.1f}, {self.y:.1f})")

    def seek_food(self, world):
        target = world.get_nearest_food(int(self.x), int(self.y))
        if not target:
            self.move_random()
            return
        tx, ty = target
        dx, dy = tx - self.x, ty - self.y
        dist = (dx**2 + dy**2)**0.5
        if dist == 0:
            return  # Already at food
        step = min(self.config["SEEK_SPEED"], dist)  # Smoother, no overshoot
        self._apply_movement((dx/dist)*step, (dy/dist)*step)
        logging.info(f"Thronglet {self.id} seeking food at ({tx}, {ty}), moved to ({self.x:.1f}, {self.y:.1f})")

    def can_replicate(self, current_time):
        # Only allow replication if energy is at max (must have eaten)
        return (current_time >= self.next_replicate
                and self.energy >= self.config["ENERGY_MAX"])

    def replicate(self, current_time):
        self.energy -= self.config["REPLICATION_ENERGY_COST"]
        self.next_replicate = current_time + self._random_interval()
        logging.info(f"Thronglet {self.id} replicated at ({self.x:.1f}, {self.y:.1f})")
        return Thronglet(self.x, self.y, self.config)

    def drop_food(self, world):
        cost = self.config.get("DROP_FOOD_ENERGY_COST", 0)
        if self.energy >= cost:
            world.add_food_at(int(self.x), int(self.y))
            self.energy -= cost

    def forage(self, world):
        if world.consume_food_at(int(self.x), int(self.y)):
            self.energy = min(self.config["ENERGY_MAX"],
                              self.energy + self.config["ENERGY_GAIN_PER_FOOD"])

    def update(self, current_time, world, thronglets):
        # Move away from others if too close
        self.move_away_from_others(thronglets)
        # forage first
        self.forage(world)
        # if ready but low energy, seek food
        if current_time >= self.next_replicate and \
           self.energy < self.config["ENERGY_MAX"]:
            self.seek_food(world)
        elif self.can_replicate(current_time):
            return self.replicate(current_time)
        else:
            self.move_random()
        return None

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.config["THRONGLET_COLOR"],
            (int(self.x), int(self.y)),
            self.config["THRONGLET_RADIUS"]
        )
        # Draw ID counter
        font = pygame.font.SysFont(None, 16)
        img = font.render(str(self.id), True, (255, 255, 255))
        surface.blit(img, (int(self.x) - 6, int(self.y) - 6))

# --- Main Loop ---
def main():
    setup_logging()  # Only call ONCE, before the loop!
    pygame.init()
    screen = pygame.display.set_mode(
        (CONFIG["WORLD_WIDTH"], CONFIG["WORLD_HEIGHT"]))
    pygame.display.set_caption("Thronglets Simulator")
    clock = pygame.time.Clock()

    world = World(CONFIG)
    thronglets = []
    for _ in range(CONFIG["INITIAL_THRONGLETS"]):
        x = random.randint(0, CONFIG["WORLD_WIDTH"])
        y = random.randint(0, CONFIG["WORLD_HEIGHT"])
        thronglets.append(Thronglet(x, y, CONFIG))

    running = True
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # example: drop food on mouse click
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                world.add_food_at(mx, my)

        # Update thronglets and collect new babies
        new_thronglets = []
        for t in thronglets:
            baby = t.update(current_time, world, thronglets)
            if baby:
                new_thronglets.append(baby)
        thronglets.extend(new_thronglets)

        # Render
        screen.fill(CONFIG["BACKGROUND_COLOR"])
        # draw food
        for fx, fy in world.food:
            pygame.draw.rect(screen, (200, 150, 50), (fx-4, fy-4, 8, 8))
        # draw agents
        for t in thronglets:
            t.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
