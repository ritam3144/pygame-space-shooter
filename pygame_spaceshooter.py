import pygame
import random
import sys
import os
from dotenv import load_dotenv

# =========================
# Space Shooter Game
# Usage:
#   - Arrow keys to move
#   - Spacebar to shoot
#   - Avoid enemy bullets and enemies
#   - Every 5th enemy fires a circular burst
#   - Every 10 hits, enemies get faster
#   - On game over, press R to replay or Q to quit
# =========================

# --- Configuration ---
WIDTH, HEIGHT = 480, 600
PLAYER_SPEED = 5
BULLET_SPEED = -10
ENEMY_SPEED_START = 1
ENEMY_SPEED_INCREMENT = 1
HITS_FOR_SPEEDUP = 10
ENEMY_SPAWN_DELAY = 30
ENEMY_BULLET_SPEED = 6
ENEMY_BULLET_BURST = 12  # Number of bullets in a burst

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- Load environment variables ---
load_dotenv()

BACKGROUND_IMG_PATH = os.getenv("BACKGROUND_IMG_PATH", "background.png")
PLAYER_IMG_PATH = os.getenv("PLAYER_IMG_PATH", "spaceship.png")
BULLET_IMG_PATH = os.getenv("BULLET_IMG_PATH", "bullet.png")
ENEMY_IMG_PATHS = os.getenv("ENEMY_IMG_PATHS", "enemy1.png,enemy2.png,enemy3.png").split(',')

# --- Asset Loading ---
def load_image(filename, fallback_size, fallback_color):
    try:
        img = pygame.image.load(filename)
        return img
    except pygame.error:
        surf = pygame.Surface(fallback_size)
        surf.fill(fallback_color)
        return surf

def load_assets():
    assets = {}
    # Background
    try:
        bg = pygame.image.load(BACKGROUND_IMG_PATH).convert()
        assets['background'] = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except pygame.error:
        assets['background'] = None
    # Player
    assets['player'] = load_image(PLAYER_IMG_PATH, (50, 38), (0, 0, 255))
    # Bullet
    assets['bullet'] = load_image(BULLET_IMG_PATH, (5, 10), (255, 255, 0))
    # Enemies
    assets['enemies'] = [
        load_image(fname.strip(), (40, 30), (255, 0, 0)) for fname in ENEMY_IMG_PATHS
    ]
    return assets

# --- Drawing ---
def draw_text(surf, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

def draw_game(screen, assets, player_rect, bullets, enemies, enemy_bullets, score):
    bg = assets['background']
    if bg:
        screen.blit(bg, (0, 0))
    else:
        screen.fill(BLACK)
    screen.blit(assets['player'], player_rect)
    for bullet in bullets:
        screen.blit(assets['bullet'], bullet)
    for enemy_rect, img_idx in enemies:
        screen.blit(assets['enemies'][img_idx], enemy_rect)
    for eb in enemy_bullets:
        screen.blit(assets['bullet'], eb['rect'])
    draw_text(screen, f"Score: {score}", 30, WIDTH // 2, 10)
    pygame.display.flip()

def show_game_over_screen(screen, score):
    screen.fill(BLACK)
    draw_text(screen, "GAME OVER", 64, WIDTH // 2, HEIGHT // 3)
    draw_text(screen, f"Score: {score}", 36, WIDTH // 2, HEIGHT // 2)
    draw_text(screen, "Press R to Replay or Q to Quit", 28, WIDTH // 2, HEIGHT // 2 + 60)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

# --- Game Logic ---
def reset_game_state(assets):
    player_rect = assets['player'].get_rect()
    player_rect.centerx = WIDTH // 2
    player_rect.bottom = HEIGHT - 10
    bullets = []
    enemies = []
    enemy_bullets = []
    enemy_speed = ENEMY_SPEED_START
    score = 0
    enemy_spawn_count = 0
    enemy_timer = 0
    return {
        'player_rect': player_rect,
        'bullets': bullets,
        'enemies': enemies,
        'enemy_bullets': enemy_bullets,
        'enemy_speed': enemy_speed,
        'score': score,
        'enemy_spawn_count': enemy_spawn_count,
        'enemy_timer': enemy_timer
    }

def handle_player_input(keys, player_rect, bullets, bullet_img):
    if keys[pygame.K_LEFT] and player_rect.left > 0:
        player_rect.x -= PLAYER_SPEED
    if keys[pygame.K_RIGHT] and player_rect.right < WIDTH:
        player_rect.x += PLAYER_SPEED
    if keys[pygame.K_SPACE]:
        if len(bullets) < 5:
            bullet_rect = bullet_img.get_rect()
            bullet_rect.centerx = player_rect.centerx
            bullet_rect.bottom = player_rect.top
            bullets.append(bullet_rect)

def update_bullets(bullets):
    for bullet in bullets[:]:
        bullet.y += BULLET_SPEED
        if bullet.bottom < 0:
            bullets.remove(bullet)

def spawn_enemy(assets, enemies, enemy_spawn_count):
    img_idx = random.randint(0, len(assets['enemies']) - 1)
    enemy_rect = assets['enemies'][img_idx].get_rect()
    enemy_rect.x = random.randint(0, WIDTH - enemy_rect.width)
    enemy_rect.y = -enemy_rect.height
    enemies.append((enemy_rect, img_idx))
    enemy_spawn_count += 1
    return enemy_rect, img_idx, enemy_spawn_count

def fire_enemy_burst(enemy_rect, enemy_bullets, bullet_img):
    centerx = enemy_rect.centerx
    top = enemy_rect.bottom
    for i in range(ENEMY_BULLET_BURST):
        angle_deg = (360 / ENEMY_BULLET_BURST) * i
        dx = ENEMY_BULLET_SPEED * pygame.math.Vector2(1, 0).rotate(angle_deg).x
        dy = ENEMY_BULLET_SPEED * pygame.math.Vector2(1, 0).rotate(angle_deg).y
        enemy_bullet_rect = bullet_img.get_rect()
        enemy_bullet_rect.centerx = centerx
        enemy_bullet_rect.top = top
        enemy_bullets.append({'rect': enemy_bullet_rect, 'dx': dx, 'dy': dy})

def update_enemies(enemies, enemy_speed):
    for enemy in enemies[:]:
        enemy_rect, img_idx = enemy
        enemy_rect.y += enemy_speed
        if enemy_rect.top > HEIGHT:
            enemies.remove(enemy)

def update_enemy_bullets(enemy_bullets):
    for eb in enemy_bullets[:]:
        eb['rect'].x += int(eb['dx'])
        eb['rect'].y += int(eb['dy'])
        if (eb['rect'].top > HEIGHT or eb['rect'].bottom < 0 or
            eb['rect'].right < 0 or eb['rect'].left > WIDTH):
            enemy_bullets.remove(eb)

def handle_collisions(bullets, enemies, enemy_bullets, player_rect, score, enemy_speed):
    # Bullet-enemy collisions
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            enemy_rect, img_idx = enemy
            if bullet.colliderect(enemy_rect):
                bullets.remove(bullet)
                enemies.remove(enemy)
                score += 1
                if score % HITS_FOR_SPEEDUP == 0:
                    enemy_speed += ENEMY_SPEED_INCREMENT
                break
    # Enemy-player collisions
    for enemy in enemies:
        enemy_rect, img_idx = enemy
        if enemy_rect.colliderect(player_rect):
            return True, score, enemy_speed
    # Enemy bullet-player collisions
    for eb in enemy_bullets:
        if eb['rect'].colliderect(player_rect):
            return True, score, enemy_speed
    return False, score, enemy_speed

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Shooter")
    assets = load_assets()
    clock = pygame.time.Clock()

    while True:
        state = reset_game_state(assets)
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            handle_player_input(keys, state['player_rect'], state['bullets'], assets['bullet'])
            update_bullets(state['bullets'])

            # Enemy spawn logic
            state['enemy_timer'] += 1
            if state['enemy_timer'] >= ENEMY_SPAWN_DELAY:
                state['enemy_timer'] = 0
                enemy_rect, img_idx, state['enemy_spawn_count'] = spawn_enemy(
                    assets, state['enemies'], state['enemy_spawn_count']
                )
                # Every 5th enemy fires a circular burst
                if state['enemy_spawn_count'] % 5 == 0:
                    fire_enemy_burst(enemy_rect, state['enemy_bullets'], assets['bullet'])

            update_enemies(state['enemies'], state['enemy_speed'])
            update_enemy_bullets(state['enemy_bullets'])

            game_over, state['score'], state['enemy_speed'] = handle_collisions(
                state['bullets'], state['enemies'], state['enemy_bullets'],
                state['player_rect'], state['score'], state['enemy_speed']
            )

            draw_game(
                screen, assets, state['player_rect'], state['bullets'],
                state['enemies'], state['enemy_bullets'], state['score']
            )

            if game_over:
                running = False

        show_game_over_screen(screen, state['score'])

if __name__ == "__main__":
    main()