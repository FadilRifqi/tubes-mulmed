import pygame
import sys
import os
import cv2
from audio import Audio

from sapi import Sapi
from pagar import Pagar, ObstacleManager
import environment

# --- KONSTANTA GLOBAL STATE BARU ---
MAX_HEALTH = 3
current_health = MAX_HEALTH
score = 0.0
game_state = "MENU" # State awal: MENU, PLAYING, atau GAMEOVER

audio = Audio()
audio.start()

# --- ASSET PATH ---
walk_path = os.path.join(os.getcwd(), 'assets', 'walk.png')
walk_low_path = os.path.join(os.getcwd(), 'assets', 'walk_low.png')
walk_high_path = os.path.join(os.getcwd(), 'assets', 'walk_high.png')

pagar_1_image_path = os.path.join(os.getcwd(), 'assets', 'pagar.png')
pagar_2_image_path = os.path.join(os.getcwd(), 'assets', 'pagar_2.png')
heart_full_path = os.path.join(os.getcwd(), 'assets', 'nyawa.png') # Aset tunggal untuk nyawa

# pygame init
pygame.init()

# set ukuran layar
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sapi Go")
font_score = pygame.font.SysFont("consolas", 28)
font_menu = pygame.font.SysFont("impact", 72)
clock = pygame.time.Clock()

# --- LOAD ASSET UTILITY ---
def load_and_scale_asset(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            return pygame.transform.scale(img, size)
        return img
    except Exception:
        return None

HEART_SIZE = (40, 40)
HEART_IMG = load_and_scale_asset(heart_full_path, HEART_SIZE)
HEART_EMPTY_IMG = None # Tidak digunakan

# buat object pagar
pagar_1 = Pagar(pagar_1_image_path)
pagar_2 = Pagar(pagar_2_image_path)

# Setup video capture
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Gagal membuka webcam. Pastikan kamera terhubung.")

# Set resolusi kamera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# offset dan speed kamera
offset_x = 0.0
speed_x = -10

# definisi gambar dan rect pagar
pagar_img = pagar_1.get_image()
pagar2_img = pagar_2.get_image()
PAGAR_VARIANTS = [img for img in (pagar_img, pagar2_img) if img is not None]
HB_FOR_IMG = Pagar.build_hitbox_config(pagar_img, pagar2_img)

# Konfigurasi Obstacle
SPRITE_SPEED = 3
SPRITE_SET_OFFSETS = [(20, 20), (170, 40)]
BOUNCE_PX = 200

# --- SETUP PLAYER (SAPI) ---
SAPI_SIZE = (320, 320)
PLAYER_X = 130
DEBUG_HITBOX = False

player_cow = Sapi(
    normal_path=walk_path,
    low_path=walk_low_path,
    high_path=walk_high_path,
    x_pos=PLAYER_X,
    target_size=SAPI_SIZE
)

# Manager Obstacle
manager = ObstacleManager(
    screen_width=WIDTH,
    variants=PAGAR_VARIANTS,
    pagar2_img=pagar2_img,
    spawn_interval_ms=4000,
    speed=SPRITE_SPEED,
    offsets=SPRITE_SET_OFFSETS,
    bounce_px=BOUNCE_PX,
    hb_config=HB_FOR_IMG
)

# --- FUNGSI GLOBAL STATE ---
def reset_game():
    """Mengatur ulang semua variabel game untuk memulai permainan baru."""
    global offset_x, current_health, score, game_state
    offset_x = 0.0
    current_health = MAX_HEALTH
    score = 0.0
    manager.sets.clear() # Hapus semua set pagar aktif
    manager.sprite_spawn_timer = 0 # Reset timer spawn
    game_state = "PLAYING"
    print("Game Dimulai!")

def check_game_over():
    """Memeriksa apakah nyawa habis dan mengubah state menjadi GAMEOVER."""
    global game_state
    if current_health <= 0 and game_state == "PLAYING":
        game_state = "GAMEOVER"
        print(f"GAME OVER! Skor Akhir: {int(score)}")

def camera_follow_on_bounce(dx: float):
    """Dipanggil saat pemain menabrak pagar. Menggeser dunia dan mengurangi nyawa."""
    global offset_x, current_health
    
    if game_state == "PLAYING":
        current_health -= 1
        check_game_over()
        
    offset_x += dx
    manager.shift_world(dx)


FRAME_INTERVAL_MS = 128
time_since_last_frame = 0
background_surf = None

running = True
try:
    while running:
        dt = clock.tick(60)
        
        # --- EVENT HANDLING ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                if game_state == "MENU" or game_state == "GAMEOVER":
                    reset_game()

        # --- BACKGROUND ---
        time_since_last_frame += dt
        if time_since_last_frame >= FRAME_INTERVAL_MS:
            ret, frame = cam.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                background_surf = pygame.image.frombuffer(frame.tobytes(), (WIDTH, HEIGHT), "RGB")
            time_since_last_frame = 0

        if background_surf is not None:
            screen.blit(background_surf, (0, 0))
        else:
            screen.fill(environment.BG)
            
        # --- LOGIKA GAME INTI (Hanya saat PLAYING) ---
        if game_state == "PLAYING":
            # 1. Update Skor
            score += dt / 100 

            # 2. Input Suara
            freq = audio.get_pitch()
            # 66 <= f < 500 = Nunduk (Z-down)
            # f >= 500 = Ramping (X-down)
            if freq <= 100:
                ramping = False
                nunduk = True
            elif freq >= 500:
                nunduk = False
                ramping = True
            else:
                ramping = False
                nunduk = False
            print(f"Freq: {freq:.2f} Hz | Nunduk: {nunduk} | Ramping: {ramping}")
            # 3. Update Dunia dan Rintangan
            offset_x += speed_x
            
            floor_top_y = environment.get_floor_top_y()
            player_cow.set_floor_pos(floor_top_y)
            player_cow.update(dt, nunduk, ramping)
            
            collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes = manager.update_and_prepare_draw(
                dt=dt,
                player_rect=player_cow.rect,
                z_down=nunduk, # Nunduk
                x_down=ramping, # Ramping
                camera_follow_cb=camera_follow_on_bounce,
                debug_hitbox=DEBUG_HITBOX,
                screen=screen,
            )
        
        # --- DRAWING DUNIA & PLAYER (Hanya saat PLAYING/GAMEOVER) ---
        if game_state != "MENU":
            environment.draw_lantai(screen, offset_x)
            
            # Draw Pagar (hanya jika PLAYING)
            if game_state == "PLAYING":
                for img, r in back_draw:
                    screen.blit(img, r)
            
            # Draw Player (Sapi)
            player_cow.draw(screen)
            if DEBUG_HITBOX:
                 pygame.draw.rect(screen, (0, 255, 0), player_cow.rect, 2)
            
            # Draw Pagar di depan (hanya jika PLAYING)
            if game_state == "PLAYING":
                for img, r in front_draw:
                    screen.blit(img, r)

            environment.draw_lantai_edges(screen, offset_x)
            
            # Draw UI (Nyawa & Skor)
            environment.draw_score(screen, font_score, int(score))
            environment.draw_health_bar(screen, current_health, MAX_HEALTH, HEART_IMG, HEART_EMPTY_IMG) 
        
        # --- SCREEN STATE DRAWING (Overlay) ---
        if game_state == "MENU":
            environment.draw_menu_screen(screen, font_menu)
        
        elif game_state == "GAMEOVER":
            environment.draw_game_over_screen(screen, font_menu, font_score, int(score))

        pygame.display.flip()

except KeyboardInterrupt:
    pass
finally:
    audio.stop()
    if cam.isOpened():
        cam.release()
    pygame.quit()
    sys.exit()