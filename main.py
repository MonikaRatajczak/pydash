"""CONTROLS
Anywhere -> ESC: exit
Main menu -> 1: go to previous level. 2: go to next level. 3: go to level 3. SPACE: start game.
Game -> SPACE/UP: jump, and activate orb
    orb: jump in midair when activated
If you die or beat the level, press SPACE to restart or go to the next level
"""

import csv
import os
import random

# import the pygame module
import pygame

# will make it easier to use pygame functions
from pygame.math import Vector2
from pygame.draw import rect

# ZADANIE 1 -  initializuj pygame
pygame.init()

# stwórz screen 800 x 600
screen = pygame.display.set_mode((800, 600))

# controls the main game while loop
done = False

# controls whether or not to start the game from the main menu
start = False

# stwórz zegar clock
clock = pygame.time.Clock()

"""
CONSTANTS
"""
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

color = lambda: tuple([random.randint(0, 255) for i in range(3)])
GRAVITY = Vector2(0, 0.45)

"""
Main player class - ZMODYFIKOWANY
"""


class Player(pygame.sprite.Sprite):
    """Class for player. Holds update method, win and die variables, collisions and more."""
    win: bool
    died: bool

    def __init__(self, image, platforms, pos, *groups):
        super().__init__(*groups)
        self.onGround = False
        self.platforms = platforms
        self.died = False
        self.win = False

        self.image = pygame.transform.smoothscale(image, (32, 32))
        self.rect = self.image.get_rect(center=pos)
        self.jump_amount = 14  # ZWIĘKSZONY skok (było 10)
        self.particles = []
        self.isjump = False
        self.vel = Vector2(0, 0)

    def draw_particle_trail(self, x, y, color=(255, 255, 255)):
        self.particles.append(
            [[x - 5, y - 8], [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
             random.randint(5, 8)])

        for particle in self.particles[:]:  # DODANE [:] żeby uniknąć błędu przy usuwaniu
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[2] -= 0.5
            particle[1][0] -= 0.4
            rect(alpha_surf, color,
                 ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for i in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)

    def collide(self, yvel, platforms):
        global coins, keys

        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                # DODANY BUFOR dla kolizji - łatwiejsze lądowanie
                buffer = 4
                if isinstance(p, Orb) and (keys[pygame.K_UP] or keys[pygame.K_SPACE]):
                    pygame.draw.circle(alpha_surf, (255, 255, 0), p.rect.center, 18)
                    screen.blit(pygame.image.load("images/editor-0.9s-47px.gif"), p.rect.center)
                    self.jump_amount = 15  # Mocniejszy orb
                    self.jump()
                    self.jump_amount = 14

                if isinstance(p, End):
                    self.win = True

                # ── KOLCE (normalne i odwrócone) ──────────────────────────────────
                if isinstance(p, Spike):
                    if p.upside_down:
                        # Kolec na suficie – zabija gdy gracz dotknie go od dołu
                        if self.rect.top < p.rect.bottom - buffer:
                            self.died = True
                    else:
                        # Kolec na podłodze – zabija gdy gracz dotknie od góry
                        if self.rect.bottom > p.rect.top + buffer:
                            self.died = True
                # ─────────────────────────────────────────────────────────────────

                if isinstance(p, Coin):
                    coins += 1
                    p.rect.x = 0
                    p.rect.y = 0

                if isinstance(p, Platform):
                    if yvel > 0:
                        self.rect.bottom = p.rect.top
                        self.vel.y = 0
                        self.onGround = True
                        self.isjump = False
                    elif yvel < 0:
                        self.rect.top = p.rect.bottom
                    else:
                        self.vel.x = 0
                        self.rect.right = p.rect.left

    def check_screen_collision(self):
        # Game over gdy klocek dotknie lewej krawędzi ekranu (x <= 0)
        if self.rect.left <= 0:
            self.died = True

    def jump(self):
        self.vel.y = -self.jump_amount

    def update(self):
        if self.isjump:
            if self.onGround:
                self.jump()

        if not self.onGround:
            self.vel += GRAVITY
            if self.vel.y > 80:  # ZMNIEJSZONA maksymalna prędkość spadania (było 100)
                self.vel.y = 80

        self.collide(0, self.platforms)
        self.rect.top += self.vel.y
        self.onGround = False
        self.collide(self.vel.y, self.platforms)

        # DODANE: Sprawdzenie kolizji z lewą krawędzią ekranu
        self.check_screen_collision()

        eval_outcome(self.win, self.died)


class Draw(pygame.sprite.Sprite):
    def __init__(self, image, pos, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)


class Platform(Draw):
    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


# ── ZMODYFIKOWANA klasa Spike ─────────────────────────────────────────────────
class Spike(Draw):
    def __init__(self, image, pos, upside_down=False, *groups):
        super().__init__(image, pos, *groups)
        self.upside_down = upside_down
# ─────────────────────────────────────────────────────────────────────────────


class Coin(Draw):
    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Orb(Draw):
    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Trick(Draw):
    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class End(Draw):
    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


def init_level(map_):
    x = 0
    y = 0
    for row in map_:
        for col in row:
            if col == "0":
                Platform(block, (x, y), elements)
            if col == "Coin":
                Coin(coin, (x, y), elements)
            if col == "Spike":
                # Normalny kolec – ostrze skierowane w górę
                Spike(spike, (x, y), False, elements)
            if col == "SpikeUp":
                # Odwrócony kolec – ostrze skierowane w dół (na suficie)
                Spike(spike_up, (x, y), True, elements)
            if col == "Orb":
                orbs.append([x, y])
                Orb(orb, (x, y), elements)
            if col == "T":
                Trick(trick, (x, y), elements)
            if col == "End":
                End(avatar, (x, y), elements)
            x += 32
        y += 32
        x = 0


def blitRotate(surf, image, pos, originpos: tuple, angle: float):
    w, h = image.get_size()
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]
    min_box = (min(box_rotate, key=lambda p: p[0])[0],
               min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0],
               max(box_rotate, key=lambda p: p[1])[1])

    pivot = Vector2(originpos[0], -originpos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0],
              pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    rotated_image = pygame.transform.rotozoom(image, angle, 1)
    surf.blit(rotated_image, origin)


def won_screen():
    global attempts, level, fill
    attempts = 0
    player_sprite.clear(player.image, screen)
    screen.fill(pygame.Color("yellow"))
    txt_win1 = txt_win2 = "Nothing"
    if level == 1:
        if coins == 6:
            txt_win1 = f"Coin{coins}/6! "
            txt_win2 = "the game, Congratulations"
    else:
        txt_win1 = f"level{level}"
        txt_win2 = f"Coins: {coins}/6. "
    txt_win = f"{txt_win1} You beat {txt_win2}! Press SPACE to restart, or ESC to exit"
    won_game = font.render(txt_win, True, BLUE)
    screen.blit(won_game, (200, 300))
    level += 1
    if level >= len(levels):
        level = 0
    wait_for_key()
    reset()


def death_screen():
    global attempts, fill
    fill = 0
    player_sprite.clear(player.image, screen)
    attempts += 1
    game_over = font.render("Game Over. [SPACE] to restart", True, WHITE)
    screen.fill(pygame.Color("sienna1"))
    screen.blits([[game_over, (100, 100)], [tip, (100, 400)]])
    wait_for_key()
    reset()


def eval_outcome(won: bool, died: bool):
    if won:
        won_screen()
    if died:
        death_screen()


def block_map(level_num):
    lvl = []
    with open(level_num, newline='') as csvfile:
        trash = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in trash:
            lvl.append(row)
    return lvl


def start_screen():
    global level
    if not start:
        screen.fill(BLACK)
        keys_local = pygame.key.get_pressed()
        if keys_local[pygame.K_1]:
            level = 0
        if keys_local[pygame.K_2]:
            level = 1
        if keys_local[pygame.K_3]:
            level = 2
        if keys_local[pygame.K_4]:
            level = 3
        if keys_local[pygame.K_5]:
            level = 4
        welcome = font.render(
            f"Welcome to Pydash. choose level({level + 1})",
            True,
            WHITE,
        )
        controls = font.render("Controls: jump: Space/Up exit: Esc", True, GREEN)
        easy_tip = font.render("TIP: ", True, (0, 255, 0))
        screen.blits([[welcome, (50, 100)],
                      [controls, (100, 400)],
                      [easy_tip, (100, 450)]])
        level_memo = font.render(f"Level {level + 1}.", True, (255, 255, 0))
        screen.blit(level_memo, (100, 200))


def reset():
    global player, elements, player_sprite, level, coins, fill
    coins = 0
    fill = 0
    if level == 1:
        pygame.mixer.music.load(os.path.join("music", "castle-town.mp3"))
    else:
        pygame.mixer.music.load(os.path.join("music", "bossfight-Vextron.mp3"))
    pygame.mixer_music.play()
    player_sprite = pygame.sprite.Group()
    elements = pygame.sprite.Group()
    player = Player(avatar, elements, (150, 150), player_sprite)
    init_level(block_map(levels[level]))


def move_map():
    for sprite in elements:
        sprite.rect.x -= CameraX


def draw_stats(surf, money=0):
    global fill
    progress_colors = [pygame.Color("red"), pygame.Color("orange"),
                       pygame.Color("yellow"), pygame.Color("lightgreen"),
                       pygame.Color("green")]
    tries = font.render(f" Attempt {str(attempts)}", True, WHITE)
    BAR_LENGTH = 600
    BAR_HEIGHT = 10
    for i in range(1, money):
        screen.blit(coin, (BAR_LENGTH, 25))
    fill += 0.3  # WOLNIEJSZY pasek postępu (było 0.5)
    outline_rect = pygame.Rect(0, 0, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(0, 0, fill, BAR_HEIGHT)
    col = progress_colors[int(fill / 100)] if fill < 500 else progress_colors[-1]
    rect(surf, col, fill_rect, 0, 4)
    rect(surf, WHITE, outline_rect, 3, 4)
    screen.blit(tries, (BAR_LENGTH, 0))


def wait_for_key():
    global level, start
    waiting = True
    while waiting:
        clock.tick(60)
        pygame.display.flip()
        if not start:
            start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start = True
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()


def coin_count(coins_param):
    if coins_param >= 3:
        coins_param = 3
    coins_param += 1
    return coins_param


def resize(img, size=(32, 32)):
    return pygame.transform.smoothscale(img, size)


"""
Global variables
"""
font = pygame.font.SysFont("lucidaconsole", 20)
avatar = pygame.image.load(os.path.join("images", "avatar.png"))
pygame.display.set_icon(avatar)
alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

player_sprite = pygame.sprite.Group()
elements = pygame.sprite.Group()

# images
spike = resize(pygame.image.load(os.path.join("images", "obj-spike.png")))
# ── NOWE: obraz kolca odwróconego (flip w pionie) ─────────────────────────────
spike_up = pygame.transform.flip(spike, False, True)
# ─────────────────────────────────────────────────────────────────────────────
coin = pygame.transform.smoothscale(
    pygame.image.load(os.path.join("images", "coin.png")), (32, 32)
)
block = pygame.transform.smoothscale(
    pygame.image.load(os.path.join("images", "block_1.png")), (32, 32)
)
orb = pygame.transform.smoothscale(
    pygame.image.load(os.path.join("images", "orb-yellow.png")), (32, 32)
)
trick = pygame.transform.smoothscale(
    pygame.image.load(os.path.join("images", "obj-breakable.png")), (32, 32)
)

# ints
fill = 0
num = 0
CameraX = 0
attempts = 0
coins = 0
angle = 0
level = 0

# lists
particles = []
orbs = []
win_cubes = []

# UWAGA: dodany level_3 i poprawiona spacja w level_2.csv
levels = ["level_1.csv", "level_2.csv", "level_3.csv", "level_4.csv", "level_5.csv"]
level_list = block_map(levels[level])
level_width = (len(level_list[0]) * 32)
level_height = len(level_list) * 32
init_level(level_list)

pygame.display.set_caption('Pydash')
text = font.render('image', False, (255, 255, 0))

# music
pygame.mixer_music.load(os.path.join("music", "bossfight-Vextron.mp3"))
pygame.mixer_music.play()

bg = pygame.image.load(os.path.join("images", "bg.png"))
player = Player(avatar, elements, (150, 150), player_sprite)
tip = font.render(
    "", True, (0, 255, 0)
)

while not done:
    keys = pygame.key.get_pressed()

    if not start:
        wait_for_key()
        reset()
        start = True

    player.vel.x = 4  # ZMNIEJSZONA prędkość gracza (było 6)

    eval_outcome(player.win, player.died)
    if keys[pygame.K_UP] or keys[pygame.K_SPACE]:
        player.isjump = True
    else:
        player.isjump = False

    alpha_surf.fill((255, 255, 255, 1), special_flags=pygame.BLEND_RGBA_MULT)

    player_sprite.update()
    CameraX = player.vel.x
    move_map()

    screen.blit(bg, (0, 0))

    player.draw_particle_trail(player.rect.left - 1,
                               player.rect.bottom + 2,
                               WHITE)
    screen.blit(alpha_surf, (0, 0))
    draw_stats(screen, coin_count(coins))

    if player.isjump:
        angle -= 8.1712
        blitRotate(screen, player.image,
                   player.rect.center, (16, 16), angle)
    else:
        player_sprite.draw(screen)
    elements.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True

    pygame.display.flip()
    clock.tick(60)

pygame.quit()