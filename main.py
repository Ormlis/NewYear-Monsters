import sys
from random import randint

import pygame
import os

WIDTH = 500
HEIGHT = 500
SIZE = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(SIZE)

FPS = 60
clock = pygame.time.Clock()
pygame.font.init()


def terminate():
    pygame.quit()
    sys.exit()


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = mapFile.readlines()

    max_width = max(map(len, level_map)) - 1

    return list(map(lambda x: ''.join(map(lambda y: "K" if y == ' ' else y, x))
                    .rstrip().ljust(max_width, 'K'),
                    level_map))


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def cut_sheet(sheet, rows, pix_x1=0, pix_y1=0, pix_x2=-1, pix_y2=-1):
    if pix_x2 == -1:
        pix_x2 = sheet.get_width()
    if pix_y2 == -1:
        pix_y2 = sheet.get_height()
    rect = pygame.Rect(0, 0, (pix_x2 - pix_x1) // max(rows),
                       (pix_y2 - pix_y1) // len(rows))
    frames = [[]]
    for j in range(len(rows)):
        frames[0].append([])
        for i in range(rows[j]):
            frame_location = (pix_x1 + rect.w * i, pix_y1 + rect.h * j)
            frames[0][j].append(sheet.subsurface(pygame.Rect(
                frame_location, rect.size)))
    return rect, frames


def text_screen(text):
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        #blck_surf = pygame.Surface(intro_rect.size)
        #blck_surf.fill((0, 0, 0))
        text_coord += 10
        #screen.blit(blck_surf, (10, text_coord))
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, rows, x, y, *groups, pix_x1=0, pix_y1=0, pix_x2=-1, pix_y2=-1):
        super().__init__(all_sprites, *groups)
        self.rotated = 0
        self.rect, self.frames = cut_sheet(sheet, rows, pix_x1, pix_y1, pix_x2, pix_y2)
        self.cur_frame_row = 0
        self.cur_frame = 0
        self.image = self.frames[self.rotated][self.cur_frame_row][self.cur_frame]
        self.rect = self.rect.move(x, y)

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames[self.rotated][self.cur_frame_row])
        self.image = self.frames[self.rotated][self.cur_frame_row][self.cur_frame]


class Tree(AnimatedSprite):
    def __init__(self, sheet, rows, x, y, *groups):
        super().__init__(sheet, rows, x, y, *groups)
        self.health = 30

    def get_health(self):
        return self.health

    def damage(self, dmg):
        self.health -= dmg


class Tile(pygame.sprite.Sprite):
    images = cut_sheet(pygame.transform.scale(load_image('tiles3.png'), (64 * 9, 64 * 6)),
                       [9] * 6)[1][0]
    images2 = list(
        map(lambda images_list: list(
            map(lambda image: pygame.transform.scale(image, (64, 64)), images_list)),
            cut_sheet(load_image('Tileset.png'),
                      [3] * 3, pix_x2=16 * 3, pix_y2=16 * 3)[1][0]))
    # transform all images to 64 x 64

    images = (images[0] + images[1] + images[2] + images[3] + images[4] + images[5] + images2[0] +
              images2[1] + images2[2])

    def __init__(self, tile_type, pos_x, pos_y, *groups):
        super().__init__(all_sprites, tiles_group, *groups)
        self.image = self.images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class FixedItem(pygame.sprite.Sprite):
    images = cut_sheet(load_image('Tileset.png'), [3, 3], 0, 16 * 7, 16 * 3, 16 * 9)[1][0]
    images = images[0] + images[1]
    images = list(map(lambda image: pygame.transform.scale(image, (48, 48)), images))
    images.append(load_image('mandarin.png'))

    def __init__(self, item_type, pos_x, pos_y, *groups, add_x=0, add_y=0, collide=True):
        if collide:
            super().__init__(all_sprites, items_group, boxes_group, *groups)
        else:
            super().__init__(all_sprites, items_group, *groups)
        self.image = self.images[item_type]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x + add_x,
                                               tile_height * pos_y + add_y)


class Player(AnimatedSprite):
    def __init__(self, sheet, rows, x, y):
        super().__init__(sheet, rows, x, y, player_group)
        self.v = 10
        self.iterations = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.frames = [self.frames[0][:8], self.frames[0][8:]]
        self.attacked = False

    def move(self):
        keys = pygame.key.get_pressed()
        if self.attacked or keys[pygame.K_f]:
            self.attack()
        change_x = change_y = 0
        if keys[pygame.K_UP] ^ keys[pygame.K_DOWN]:
            change_y = -self.v if keys[pygame.K_UP] else self.v
        self.rect.y += change_y
        if pygame.sprite.spritecollideany(self, boxes_group, pygame.sprite.collide_mask):
            self.rect.y -= change_y
            change_y = 0
        if keys[pygame.K_LEFT] ^ keys[pygame.K_RIGHT]:
            change_x += -self.v if keys[pygame.K_LEFT] else self.v
        self.rect.x += change_x
        if pygame.sprite.spritecollideany(self, boxes_group, pygame.sprite.collide_mask):
            self.rect.x -= change_x
            change_x = 0
        if change_x < 0:
            self.cur_frame_row = 1 if not self.attacked else self.cur_frame_row
            self.rotated = 1
        elif change_x > 0 or change_y:
            self.cur_frame_row = 1 if not self.attacked else self.cur_frame_row
            self.rotated = 0
        else:
            self.cur_frame_row = 0 if not self.attacked else self.cur_frame_row
        self.iterations = (self.iterations + 4) % 20
        if self.iterations < 4:
            self.update()

    def attack(self):
        if not self.attacked:
            self.cur_frame = 0
            self.cur_frame_row = 2
        self.attacked = (self.attacked + 1) % 40
        pygame.sprite.spritecollide(self, enemies_group, True)


class NPC(AnimatedSprite):
    def __init__(self, sheet, x, y, *groups, animated=False, rows=None, add_x=0, add_y=0):
        if animated:
            super().__init__(sheet, rows, x, y, *groups, NPC_group)
        else:
            super().__init__(sheet, [1], x, y, *groups, NPC_group)
        self.v = 15
        self.iterations = 0
        self.mask = pygame.mask.from_surface(self.image)


class Spawner(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, *groups, rotate=0):
        super().__init__(all_sprites, *groups)
        self.image = pygame.Surface((0, 0))
        self.rect = self.image.get_rect().move(x * tile_width, y * tile_height)
        self.enemy_type = enemy_type
        self.rotate = rotate

    def spawn_enemy(self):
        Enemy(self.enemy_type, self.rect.x, self.rect.y, rotate=self.rotate)


class SpawnerGroup(pygame.sprite.Group):
    def __init__(self, *sprites):
        super().__init__(*sprites)

    def apply(self, enemy_type):
        for spw in self:
            spw.enemy_type = enemy_type

    def spawn_enemies(self):
        for spw in self:
            spw.spawn_enemy()


class Enemy(AnimatedSprite):
    images = [[pygame.transform.scale(load_image('Enemy 06-1.png'), (48 * 3, 48 * 4)), [3] * 4],
              [pygame.transform.scale(load_image('Enemy 05-1.png'), (48 * 3, 48 * 4)), [3] * 4]]
    damages = [1, 2]
    speed_x = [0, -1, 1, 0]
    speed_y = [1, 0, 0, -1]

    def __init__(self, enemy_type, x, y, *groups, rotate=0):
        super().__init__(self.images[enemy_type][0], self.images[enemy_type][1], x, y,
                         enemies_group, *groups)
        self.iterations = 0
        self.damage = self.damages[enemy_type]
        self.vx = self.speed_x[rotate]
        self.vy = self.speed_y[rotate]
        self.rotated = rotate
        self.mask = pygame.mask.from_surface(self.image)
        self.frames = [[self.frames[0][0]], [self.frames[0][1]], [self.frames[0][2]],
                       [self.frames[0][3]]]

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if pygame.sprite.spritecollideany(self, animated_items_group, pygame.sprite.collide_mask):
            print(1)
            self.rect.x -= self.vx
            self.rect.y -= self.vy
            tree.damage(self.damage)
            self.kill()
        super().update()


def generate_level(level):
    new_player, new_tree, new_grandmother, x, y = None, None, None, None, None
    x_player = y_player = None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x].isdigit():
                if int(level[y][x]) == 5:
                    FixedItem(4, x - 1, y, add_x=48)
                else:
                    FixedItem(int(level[y][x]) - 1, x, y)
                Tile(6 * 9 + 4, x, y)
            elif level[y][x] == '@':
                x_player = x
                y_player = y
                Tile(16, x, y)
            elif level[y][x] == '=':
                Tile(16, x, y)
                new_tree = Tree(christmas_tree_image, [2], (x - 1) * tile_width,
                                (y - 1) * tile_height, animated_items_group, boxes_group)
            elif level[y][x] == '+':
                Tile(40, x, y)
                Spawner(x, y, 0, spawners_group, rotate=2)
            elif level[y][x] == '-':
                Tile(40, x, y)
                Spawner(x, y, 0, spawners_group, rotate=1)
            elif level[y][x] == "#":
                Tile(6 * 9 + 4, x, y)
                new_grandmother = NPC(grandmother_image, x * tile_width, y * tile_height,
                                      boxes_group)
            elif level[y][x] in ('K', "", "}"):
                Tile(ord(level[y][x]) - ord('A'), x, y, boxes_group)
            else:
                Tile(ord(level[y][x]) - ord('A'), x, y)
    new_player = Player(player_image, [13, 8, 10, 10, 10, 6, 4, 7] * 2, x_player * tile_width,
                        y_player * tile_height)
    return new_player, new_grandmother, new_tree, x, y


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


class Interface(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(interface_group)
        self.image = pygame.Surface((50, 25))
        self.rect = self.image.get_rect()
        self.rect.move(200, 10)

    def apply(self, time):
        self.image.fill((255, 255, 255))
        font = pygame.font.Font(None, 30)
        string_rendered = font.render(str(time // 60) + ":" + str(time % 60), 1,
                                      pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        self.image.blit(string_rendered, intro_rect)


text_screen(["Предыстория...",
             '',
             "Ура! Новогодние праздники начались!",
             "Вы как прилежный внук, конечно же,",
             "решили навестить вашу бабушку!",
             ])
#             "Однако, бабушке нужна ваша помощь,",
#             "Новый год находится в опасности,",
#             "Его хотят испортить злые монстры!",
#             "Прогоните их всех, пожалуйста!"])

player_image = pygame.transform.scale(load_image('player.png'), (64 * 13, 64 * 16))
christmas_tree_image = load_image('christmas_tree_w_snow.png')
grandmother_image = pygame.transform.scale(load_image('grandmother.png').
                                           subsurface(pygame.Rect((0, 0), (32, 32))), (48, 48))

all_sprites = pygame.sprite.Group()
NPC_group = pygame.sprite.Group()
animated_items_group = pygame.sprite.Group()
items_group = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
boxes_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
other_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
interface_group = pygame.sprite.Group()
spawners_group = SpawnerGroup()

tile_width = tile_height = 64
player, grandmother, tree, level_x, level_y = generate_level(load_level('map.txt'))
screen2 = pygame.Surface((tile_width * level_x, tile_height * level_y))


def run(seconds, func):
    start_tile = Tile(10, 0, 0, other_group)

    camera = Camera()

    all_sprites.update()
    tiles_group.draw(screen2)
    items_group.draw(screen2)
    iterations = 0
    time = 0

    interface = Interface()
    interface_group.update()
    interface.apply(0)
    while time < seconds * 45:
        time += 1
        interface.apply(time // 45)
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                spawners_group.spawn_enemies()
        player.move()
        camera.update(player)

        iterations = (iterations + 1) % 5
        if iterations == 0:
            enemies_group.update()
            animated_items_group.update()
            other_group.update()
        for sprite in all_sprites:
            camera.apply(sprite)

        screen.blit(screen2, (start_tile.rect.x, start_tile.rect.y))
        animated_items_group.draw(screen)
        NPC_group.draw(screen)
        other_group.draw(screen)
        player_group.draw(screen)
        enemies_group.draw(screen)
        interface_group.draw(screen)

        if not func(time):
            screen.fill((0, 0, 0))
            return 0

        clock.tick(FPS)
        pygame.display.flip()
    return 1


class QuestCookies:
    def __init__(self, count, time):
        self.count = count
        self.count_cookies = 0
        self.group = pygame.sprite.Group()
        self.started = False
        self.start_time = time

    def check(self, time):
        if self.started:
            return 1
        if time - self.start_time > 100:
            return 2
        if (player.rect.x - grandmother.rect.x) ** 2 + (
                player.rect.y - grandmother.rect.y) ** 2 < 5000:
            self.start(time)
            return 1
        return 0

    def start(self, time):
        text_screen(["Бабушка просит вас найти",
                     "её потерянные мандарины!",
                     "Пожалуйста помогите ей!",
                     f'Их ровно {self.count} штук.'])
        self.start_time = time
        self.started = True
        for i in range(self.count):
            x = randint(-level_x, level_x)
            y = randint(-level_y, level_y)
            cookie = FixedItem(6, x, y, self.group, other_group, collide=False)
            while (pygame.sprite.spritecollideany(cookie, boxes_group, False) or
                   not len(pygame.sprite.spritecollide(cookie, tiles_group, False))):
                cookie.rect.x = randint(-level_x * tile_width, level_x * tile_width)
                cookie.rect.y = randint(-level_y * tile_height, level_y * tile_height)

    def __call__(self, time):
        if time - self.start_time > 60 * 45:
            return 2
        self.count_cookies += \
            len(pygame.sprite.spritecollide(player, self.group, True, pygame.sprite.collide_mask))
        return 1 if self.count == self.count_cookies else 0

    def end(self):
        text_screen(['Молодчинка!', 'Ты нашел все мандаринки!'])


class QuestNight:
    def __init__(self, num, time):
        self.enemy_type = num
        spawners_group.apply(num)
        self.start_time = time
        self.started = False
        tree.health = 30

    def check(self, time):
        if self.started:
            return 1
        if time - self.start_time > 100:
            return 2
        if (player.rect.x - tree.rect.x) ** 2 + (
                player.rect.y - tree.rect.y) ** 2 < 10000:
            self.start(time)
            return 1
        return 0

    def start(self, time):
        self.started = True
        self.start_time = time

    def __call__(self, time):
        black_surf = pygame.Surface(SIZE)
        black_surf.fill((0, 0, 0))
        black_surf.set_alpha(70)
        screen.blit(black_surf, (0, 0))
        if tree.get_health() <= 0:
            return 2
        if (time - self.start_time) % (35 * 45) == 0:
            spawners_group.spawn_enemies()
        if time - self.start_time == 300 * 45:
            return 1
        return 0

    def end(self):
        text_screen(['Поздравляем ночь закончена!'])


class Game:
    quests = [QuestCookies, QuestNight]

    def __init__(self):
        self.current_quest = None

    def __call__(self, time):
        if time < 5 * 45:
            return True
        if time == 5 * 45:
            text_screen(['Бабушке срочно нужна ваша',
                         'помощь, скорее к ней!'])
            self.current_quest = self.quests[0](15, time)
        if time == 15 * 45:
            text_screen(["Срочно беги к ёлке!",
                         'Кажется, её хотят сломать!'])
            self.current_quest = self.quests[1](1, time)
        if self.current_quest is not None:
            chk = self.current_quest.check(time)
            if chk == 0:
                return True
            elif chk == 2:
                return False
            res = self.current_quest(time)
            if res == 1:
                self.current_quest.end()
                self.current_quest = None
            return res != 2
        return True


while run(300 * 4, Game()) == 0:
    text_screen(['К сожалению, вы проиграли',
                 'Чтобы начать с начала',
                 'Нажмите любую клавишу'])
    for spr in all_sprites:
        spr.kill()

    player, grandmother, tree, level_x, level_y = generate_level(load_level('map.txt'))
    screen2 = pygame.Surface((tile_width * level_x, tile_height * level_y))

pygame.quit()
