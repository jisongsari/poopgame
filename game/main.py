import asyncio          # ← pygbag용 추가
import pygame
import random
import sys
import math
from abc import ABC, abstractmethod

pygame.init()

WIDTH, HEIGHT = 640, 960

# ─────────────────────────────────────────
# 화면 설정 (pygbag/브라우저 비율 유지)
# ─────────────────────────────────────────
# SCALED: 창 크기에 맞춰 내부 해상도(640x960)를 자동 확대해 줌
# 가로가 남으면 좌우에 검은 여백(레터박스)이 자동으로 생김
# 브라우저에서도 동일하게 동작함
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.SCALED
)
pygame.display.set_caption("똥피하기")
clock = pygame.time.Clock()

# 시스템 폰트 대신 기본 폰트 사용 (브라우저에는 AppleSDGothicNeo가 없음)
font     = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)

BG_COLOR = (200, 40,  40)
WHITE    = (255, 255, 255)
BLACK    = (30,  30,  30)
BLUE     = (70,  130, 255)
RED      = (220, 80,  80)
GOLD     = (255, 210, 0)
GREEN    = (80,  200, 120)
GRAY     = (180, 180, 180)
PURPLE   = (150, 80,  200)
YELLOW   = (255, 230, 0)
YELLOW_D = (200, 170, 0)

# ─────────────────────────────────────────
# 이미지 로드
# ─────────────────────────────────────────
PLAYER_IMG = pygame.transform.scale(
    pygame.image.load("stickman.png").convert_alpha(), (40, 120))
ENEMY_IMG  = pygame.transform.scale(
    pygame.image.load("poop.png").convert_alpha(),  (20, 20))

# ─────────────────────────────────────────
# 하트 폴리곤 좌표 생성
# ─────────────────────────────────────────
def heart_points(cx, cy, size):
    points = []
    for i in range(360):
        rad = math.radians(i)
        x = size * 16 * (math.sin(rad) ** 3)
        y = -size * (13 * math.cos(rad)
                     - 5  * math.cos(2 * rad)
                     - 2  * math.cos(3 * rad)
                     -       math.cos(4 * rad))
        points.append((cx + x, cy + y))
    return points

# ─────────────────────────────────────────
# 추상 기반
# ─────────────────────────────────────────
class GameObject(ABC):
    def __init__(self):
        self._alive = True

    @property
    def is_alive(self):
        return self._alive

    def destroy(self):
        self._alive = False

    @property
    def can_collide_with_player(self):
        return False

    @property
    def can_collide_with_bullet(self):
        return False

    @property
    def is_bullet(self):
        return False

    @property
    @abstractmethod
    def rect(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

    def on_player_collision(self, player):
        pass

    def on_bullet_collision(self, bullet, player):
        pass

# ─────────────────────────────────────────
# Player
# ─────────────────────────────────────────
class Player(GameObject):
    MAX_HEARTS = 5

    def __init__(self):
        super().__init__()
        self.__x      = WIDTH // 2 - 20
        self.__y      = HEIGHT - 120
        self.__size   = 40
        self.__speed  = 10
        self.__hearts = self.MAX_HEARTS
        self.__elapsed_frames = 0
        self.__img    = PLAYER_IMG

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, value):
        if isinstance(value, (int, float)):
            self.__x = max(0, min(WIDTH - self.__size, value))

    @property
    def y(self):
        return self.__y

    @property
    def hearts(self):
        return self.__hearts

    @property
    def max_hearts(self):
        return self.MAX_HEARTS

    @property
    def elapsed_seconds(self):
        return self.__elapsed_frames // 60

    @property
    def is_dead(self):
        return not self.is_alive

    @property
    def rect(self):
        return pygame.Rect(int(self.__x), int(self.__y),
                           self.__size,   self.__size)

    def take_damage(self, amount=1):
        if self.is_alive:
            self.__hearts = max(0, self.__hearts - amount)
            if self.__hearts <= 0:
                self.destroy()

    def heal(self, amount=1):
        if self.is_alive:
            self.__hearts = min(self.MAX_HEARTS, self.__hearts + amount)

    def update(self):
        if not self.is_alive:
            return
        self.__elapsed_frames += 1
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self.__speed
        if keys[pygame.K_RIGHT]:
            self.x += self.__speed

    def draw(self, surface):
        if self.is_dead:
            pygame.draw.rect(surface, GRAY, self.rect)
        else:
            surface.blit(self.__img, (int(self.__x), int(self.__y)))

# ─────────────────────────────────────────
# Enemy (똥)
# ─────────────────────────────────────────
class Enemy(GameObject):
    def __init__(self):
        super().__init__()
        self.__radius = 10
        self.__x      = 0.0
        self.__y      = 0.0
        self.__speed  = 3.0
        self.__img    = ENEMY_IMG
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def rect(self):
        r = self.__radius
        return pygame.Rect(int(self.__x - r), int(self.__y - r), r * 2, r * 2)

    def reset(self):
        self.__x     = float(random.randint(self.__radius, WIDTH - self.__radius))
        self.__speed = float(random.choice([3, 4, 5, 6]))
        self.__y     = -10.0

    def update(self):
        self.__y     += self.__speed
        self.__speed += 0.1
        if self.__y > HEIGHT + self.__radius:
            self.reset()

    def draw(self, surface):
        r = self.__radius
        surface.blit(self.__img, (int(self.__x - r), int(self.__y - r)))

    def on_player_collision(self, player):
        player.take_damage(1)
        self.reset()

# ─────────────────────────────────────────
# Heart 아이템 (낙하)
# ─────────────────────────────────────────
class Heart(GameObject):
    def __init__(self):
        super().__init__()
        self.__radius = 12
        self.__size   = 1.1
        self.__x      = 0.0
        self.__y      = 0.0
        self.__speed  = 0.0
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def rect(self):
        r = self.__radius
        return pygame.Rect(int(self.__x - r), int(self.__y - r), r * 2, r * 2)

    def reset(self):
        self.__x     = float(random.randint(self.__radius, WIDTH - self.__radius))
        self.__speed = float(random.choice([3, 4, 5, 6]))
        self.__y     = -10.0

    def update(self):
        self.__y     += self.__speed
        self.__speed += 0.1
        if self.__y > HEIGHT + self.__radius:
            self.destroy()

    def draw(self, surface):
        pts = heart_points(int(self.__x), int(self.__y), self.__size)
        pygame.draw.polygon(surface, YELLOW,   pts)
        pygame.draw.polygon(surface, YELLOW_D, pts, 2)

    def on_player_collision(self, player):
        player.heal(1)
        self.destroy()

# ─────────────────────────────────────────
# FlashEffect
# ─────────────────────────────────────────
class FlashEffect:
    def __init__(self):
        self.__active     = False
        self.__mode       = 'dark'
        self.__timer      = 0
        self.__duration   = 0
        self.__peak_alpha = 0
        self.__overlay    = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def trigger(self, mode='dark', duration=20, peak_alpha=120):
        self.__active     = True
        self.__mode       = mode
        self.__timer      = 0
        self.__duration   = duration
        self.__peak_alpha = peak_alpha

    def update(self):
        if self.__active:
            self.__timer += 1
            if self.__timer >= self.__duration:
                self.__active = False

    @property
    def is_active(self):
        return self.__active

    def draw(self, surface):
        if not self.__active:
            return
        t     = self.__timer / self.__duration
        alpha = int(self.__peak_alpha * (1 - abs(t * 2 - 1)))
        color = (0, 0, 0, alpha) if self.__mode == 'dark' else (255, 255, 255, alpha)
        self.__overlay.fill(color)
        surface.blit(self.__overlay, (0, 0))

# ─────────────────────────────────────────
# 스포너
# ─────────────────────────────────────────
class EnemySpawner:
    def __init__(self, interval, max_count):
        self.__interval  = interval
        self.__max_count = max_count
        self.__timer     = 0

    def update(self, objects):
        current = sum(1 for o in objects if isinstance(o, Enemy))
        if current >= self.__max_count:
            return
        self.__timer += 1
        if self.__timer >= self.__interval:
            self.__timer = 0
            objects.append(Enemy())

class HeartSpawner:
    def __init__(self, interval=300):
        self.__interval = interval
        self.__timer    = 0

    def update(self, objects):
        self.__timer += 1
        if self.__timer >= self.__interval:
            self.__timer    = 0
            self.__interval += 60
            objects.append(Heart())

    def reset(self):
        self.__timer = 0

# ─────────────────────────────────────────
# UI 하트 Surface 생성
# ─────────────────────────────────────────
def make_heart_surf(filled: bool) -> pygame.Surface:
    size  = 40
    scale = 1.5
    cx, cy = size // 2, size // 2 + 3
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pts = heart_points(cx, cy, scale)
    if filled:
        pygame.draw.polygon(s, YELLOW,   pts)
        pygame.draw.polygon(s, YELLOW_D, pts, 2)
    else:
        pygame.draw.polygon(s, (255, 255, 255, 80), pts)
        pygame.draw.polygon(s, WHITE, pts, 2)
    return s

_heart_filled = None
_heart_empty  = None

def get_heart_surfs():
    global _heart_filled, _heart_empty
    if _heart_filled is None:
        _heart_filled = make_heart_surf(True)
        _heart_empty  = make_heart_surf(False)
    return _heart_filled, _heart_empty

# ─────────────────────────────────────────
# draw_ui / draw_game_over
# ─────────────────────────────────────────
def draw_ui(surface, player):
    filled_s, empty_s = get_heart_surfs()
    hw = filled_s.get_width()

    for i in range(player.max_hearts):
        hx = 20 + i * (hw + 4)
        hy = 14
        surf = filled_s if i < player.hearts else empty_s
        surface.blit(surf, (hx, hy))

    sec  = player.elapsed_seconds
    mins = sec // 60
    secs = sec  % 60
    surface.blit(font.render(f"Time: {mins:02d}:{secs:02d}", True, WHITE), (20, 65))
    surface.blit(font.render("R: Restart   ESC: Quit",       True, WHITE), (20, 92))

def draw_game_over(surface, player):
    sec  = player.elapsed_seconds
    mins = sec // 60
    secs = sec  % 60

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surface.blit(overlay, (0, 0))

    msg1 = big_font.render("GAME OVER",                    True, WHITE)
    msg2 = font.render(f"Survived: {mins:02d}:{secs:02d}", True, WHITE)
    msg3 = font.render("R: Restart   ESC: Quit",           True, WHITE)

    surface.blit(msg1, (WIDTH // 2 - msg1.get_width() // 2, HEIGHT // 2 - 60))
    surface.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, HEIGHT // 2))
    surface.blit(msg3, (WIDTH // 2 - msg3.get_width() // 2, HEIGHT // 2 + 40))

# ─────────────────────────────────────────
# 초기화
# ─────────────────────────────────────────
def create_objects():
    player  = Player()
    objects = [player]
    return player, objects

# ─────────────────────────────────────────
# 메인 루프 (pygbag용으로 async 변환)
# ─────────────────────────────────────────
async def main():
    enemy_spawner = EnemySpawner(interval=60, max_count=100)
    heart_spawner = HeartSpawner(interval=300)
    flash         = FlashEffect()
    player, objects = create_objects()

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if player.is_dead and event.key == pygame.K_r:
                    player, objects = create_objects()
                    enemy_spawner   = EnemySpawner(interval=60, max_count=100)
                    heart_spawner   = HeartSpawner(interval=300)
                    flash           = FlashEffect()

        if not player.is_dead:
            for obj in objects:
                obj.update()

            enemy_spawner.update(objects)
            heart_spawner.update(objects)
            flash.update()

            player_targets = [
                obj for obj in objects
                if obj is not player and obj.can_collide_with_player
            ]
            for obj in player_targets:
                if obj.is_alive and player.rect.colliderect(obj.rect):
                    before_hearts = player.hearts
                    obj.on_player_collision(player)
                    after_hearts  = player.hearts
                    if isinstance(obj, Enemy) and after_hearts < before_hearts:
                        flash.trigger(mode='dark',   duration=20, peak_alpha=130)
                    elif isinstance(obj, Heart) and after_hearts > before_hearts:
                        flash.trigger(mode='bright', duration=20, peak_alpha=110)

            objects = [obj for obj in objects if obj.is_alive or obj is player]

        else:
            flash.update()

        screen.fill(BG_COLOR)
        for obj in objects:
            obj.draw(screen)
        flash.draw(screen)
        draw_ui(surface=screen, player=player)
        if player.is_dead:
            draw_game_over(screen, player)

        pygame.display.flip()

        # pygbag 필수: 브라우저에 제어권 넘기기
        await asyncio.sleep(0)

    pygame.quit()

# 진입점
asyncio.run(main())