import sys
import pygame
import os

WIDTH = 500
HEIGHT = 500
SIZE = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(SIZE)
time = 0

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
    # fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
    # screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
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


class Tile(pygame.sprite.Sprite):
    images = cut_sheet(pygame.transform.scale(load_image('tiles3.png'), (64 * 9, 64 * 6)),
                       [9] * 6)[1][0]
    images2 = list(
        map(lambda images_list: list(
            map(lambda image: pygame.transform.scale(image, (64, 64)), images_list)),
            cut_sheet(load_image('Tileset.png'),
                      [3] * 3, pix_x2=16 * 3, pix_y2=16 * 3)[1][0]))
    # transform all images to 64 * 64

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

    def __init__(self, item_type, pos_x, pos_y, *groups, add_x=0, add_y=0):
        super().__init__(all_sprites, items_group, boxes_group, *groups)
        self.image = self.images[item_type]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x + add_x,
                                               tile_height * pos_y + add_y)


class Player(AnimatedSprite):
    def __init__(self, sheet, rows, x, y):
        super().__init__(sheet, rows, x, y, player_group)
        self.v = 15
        self.iterations = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.frames = [self.frames[0][:8], self.frames[0][8:]]

    def move(self):
        keys = pygame.key.get_pressed()
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
            self.cur_frame_row = 1 if self.cur_frame_row == 0 else self.cur_frame_row
            self.rotated = 1
        elif change_x > 0 or change_y:
            self.cur_frame_row = 1 if self.cur_frame_row == 0 else self.cur_frame_row
            self.rotated = 0
        else:
            self.cur_frame_row = 0
        self.iterations = (self.iterations + 4) % 20
        if self.iterations < 4:
            self.update()


class NPC(AnimatedSprite):
    def __init__(self, sheet, x, y, *groups, animated=False, rows=None, add_x=0, add_y=0):
        if animated:
            super().__init__(sheet, rows, x, y, *groups, NPC_group)
        else:
            super().__init__(sheet, [1], x, y, *groups, NPC_group)
        self.v = 15
        self.iterations = 0
        self.mask = pygame.mask.from_surface(self.image)


class Enemy(AnimatedSprite):
    images = [[load_image('Enemy 06-1.png'), [3] * 4]]

    def __init__(self, enemy_type, x, y, *groups):
        super().__init__(self.images[enemy_type][0], self.images[enemy_type][1], x, y, *groups)


def generate_level(level):
    new_player, x, y = None, None, None
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
                AnimatedSprite(christmas_tree_image, [2], (x - 1) * tile_width,
                               (y - 1) * tile_height, animated_items_group, boxes_group)
            elif level[y][x] == "#":
                Tile(6 * 9 + 4, x, y)
                NPC(grandmother_image, x * tile_width, y * tile_height, boxes_group)
                print(x, y)
            elif level[y][x] in ('K', "", "}"):
                Tile(ord(level[y][x]) - ord('A'), x, y, boxes_group)
            else:
                Tile(ord(level[y][x]) - ord('A'), x, y)
    new_player = Player(player_image, [13, 8, 10, 10, 10, 6, 4, 7] * 2, x_player * tile_width,
                        y_player * tile_height)
    return new_player, x, y


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
             "Однако, бабушке нужна ваша помощь,",
             "Новый год находится в опасности,",
             "Его хотят испортить злые монстры!",
             "Прогоните их всех, пожалуйста!"])

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
interface_group = pygame.sprite.Group()
tile_width = tile_height = 64
player, level_x, level_y = generate_level(load_level('map.txt'))
screen2 = pygame.Surface((tile_width * level_x, tile_height * level_y))


def day():
    time = 0
    start_tile = Tile(10, 0, 0, other_group)
    camera = Camera()
    all_sprites.update()
    tiles_group.update()
    items_group.update()
    tiles_group.draw(screen2)
    items_group.draw(screen2)
    iterations = 0
    interface = Interface()
    interface_group.update()
    interface.apply(0)
    while time < 600 * 45:
        time += 1
        interface.apply(time // 45)
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        player.move()
        camera.update(player)

        iterations = (iterations + 1) % 5
        if iterations == 0:
            animated_items_group.update()
            animated_items_group.draw(screen)
        for sprite in all_sprites:
            camera.apply(sprite)

        other_group.draw(screen)
        screen.blit(screen2, (start_tile.rect.x, start_tile.rect.y))
        animated_items_group.draw(screen)
        NPC_group.draw(screen)
        player_group.draw(screen)
        interface_group.draw(screen)

        clock.tick(FPS)
        pygame.display.flip()


day()
pygame.quit()
