import pygame
import os
import math
import sys
import neat

SCREEN_WIDTH = 1244
SCREEN_HEIGHT = 1016
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("AI_CarGame | Lakshya")

TRACK = pygame.image.load(os.path.join("Assets", "track.png"))


class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join("Assets", "car.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(490, 820))
        # self.drive_state = False
        self.vel_vector = pygame.math.Vector2(0.8, 0)
        self.angle = 0
        self.rotation_vel = 5
        self.direction = 0
        self.alive = True
        self.radars = []

    def update(self):
        self.radars.clear()
        self.drive()
        self.rotate()

        for radar_angle in (-60, -30, 0, 30, 60):
            self.radar(radar_angle)
        self.collision()
        self.data()

    def drive(self):
        # if self.drive_state:
        self.rect.center += self.vel_vector * 6

    def collision(self):
        length = 40
        collision_point_r = [
            int(self.rect.center[0] + math.cos(math.radians(self.angle + 18)) * length),
            int(self.rect.center[1] - math.sin(math.radians(self.angle + 18)) * length),
        ]
        collision_point_l = [
            int(self.rect.center[0] + math.cos(math.radians(self.angle - 18)) * length),
            int(self.rect.center[1] - math.sin(math.radians(self.angle - 18)) * length),
        ]

        # Die on Collision
        if SCREEN.get_at(collision_point_r) == pygame.Color(
            2, 105, 31, 255
        ) or SCREEN.get_at(collision_point_l) == pygame.Color(2, 105, 31, 255):
            self.alive = False

        # Draw Collision Points
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_r, 4)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_l, 4)

    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel_vector.rotate_ip(self.rotation_vel)

        if self.direction == -1:
            self.angle += self.rotation_vel
            self.vel_vector.rotate_ip(-self.rotation_vel)

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.center[0])
        y = int(self.rect.center[1])

        while (
            not SCREEN.get_at((x, y)) == pygame.Color(2, 105, 31, 255) and length < 200
        ):
            length += 1
            x = int(
                self.rect.center[0]
                + math.cos(math.radians(self.angle + radar_angle)) * length
            )
            y = int(
                self.rect.center[1]
                - math.sin(math.radians(self.angle + radar_angle)) * length
            )

        # Draw Radar
        pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(SCREEN, (0, 255, 0, 0), (x, y), 3)

        dist = int(
            math.sqrt(
                math.pow(self.rect.center[0] - x, 2)
                + math.pow(self.rect.center[1] - y, 2)
            )
        )

        self.radars.append([radar_angle, dist])


def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)


# car = pygame.sprite.GroupSingle(Car())


def eval_genomes(genomes, config):
    global cars, ge, nets

    cars = []
    ge = []
    nets = []

    for genome_id, genome in genomes:
        cars.append(pygame.sprite.GroupSingle(Car()))
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0

    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.blit(TRACK, (0, 0))

        if len(cars) == 0:
            break

        for i, car in enumerate(cars):
            ge[i].fitness += 1
            if not car.sprite.alive:
                remove(i)

        for i, car in enumerate(cars):
            output = nets[i].activate(car.sprite.data())
            if output[0] > 0.7:
                car.sprite.direction = 1
            if output[1] > 0.7:
                car.sprite.direction = -1
            if output[0] <= 0.7 and output[1] <= 0.7:
                car.sprite.direction = 0

        # User Input
        # user_input = pygame.key.get_pressed()
        # if sum(pygame.key.get_pressed()) <= 1:
        #     car.sprite.drive_state = False
        #     car.sprite.direction = 0

        # # Drive
        # if user_input[pygame.K_UP]:
        #     car.sprite.drive_state = True

        # # Steer
        # if user_input[pygame.K_RIGHT]:
        #     car.sprite.direction = 1

        # if user_input[pygame.K_LEFT]:
        #     car.sprite.direction = -1

        # Update
        for car in cars:
            car.draw(SCREEN)
            car.update()
        pygame.display.update()


# Setup NEAT Neural Network
def run(config_path):
    global pop
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    pop.run(eval_genomes, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")
    run(config_path)
