import pygame
import sys
import os
import numpy as np
import cv2
from audio import Audio

# Import class Sapi yang baru
from sapi import Sapi
from pagar import Pagar, ObstacleManager
import environment

audio = Audio()
audio.start()

# --- ASSET PATH DIUPDATE ---
# Pastikan 3 file ini ada di folder assets Anda
walk_path = os.path.join(os.getcwd(), 'assets', 'walk.png')
walk_low_path = os.path.join(os.getcwd(), 'assets', 'walk_low.png')
walk_high_path = os.path.join(os.getcwd(), 'assets', 'walk_high.png')

pagar_1_image_path = os.path.join(os.getcwd(), 'assets', 'pagar.png')
pagar_2_image_path = os.path.join(os.getcwd(), 'assets', 'pagar_2.png')

# pygame init
pygame.init()

# set ukuran layar
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sapi Go")
font = pygame.font.SysFont("consolas", 28)
clock = pygame.time.Clock()

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

# Inisialisasi object Sapi dengan 3 file
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

def camera_follow_on_bounce(dx: float):
    global offset_x
    offset_x += dx
    manager.shift_world(dx)

FRAME_INTERVAL_MS = 128
time_since_last_frame = 0
background_surf = None

running = True
try:
    while running:
        dt = clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False

        # --- AUDIO PITCH LOGIC ---
        freq = audio.get_pitch()
        if 66 <= freq < 500:
            ramping = False
            nunduk = True
        elif freq >= 500:
            nunduk = False
            ramping = True
        else:
            ramping = False
            nunduk = False

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

        # Draw Lantai
        offset_x += speed_x
        environment.draw_lantai(screen, offset_x)
        environment.draw_lantai_edges(screen, offset_x)

        # --- UPDATE PLAYER (SAPI) ---
        floor_top_y = environment.get_floor_top_y()
        player_cow.set_floor_pos(floor_top_y)
        player_cow.update(dt, nunduk, ramping)

        # --- UPDATE OBSTACLES ---
        collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes = manager.update_and_prepare_draw(
            dt=dt,
            player_rect=player_cow.rect,
            z_down=nunduk,
            x_down=ramping,
            camera_follow_cb=camera_follow_on_bounce,
            debug_hitbox=DEBUG_HITBOX,
            screen=screen,
        )

        # Draw layer belakang pagar
        for img, r in back_draw:
            screen.blit(img, r)

        # --- DRAW PLAYER ---
        player_cow.draw(screen)

        # Debug Hitbox Sapi
        if DEBUG_HITBOX:
             pygame.draw.rect(screen, (0, 255, 0), player_cow.rect, 2)

        # Draw layer depan pagar
        for img, r in front_draw:
            screen.blit(img, r)

        pygame.display.flip()

except KeyboardInterrupt:
    pass
finally:
    audio.stop()
    if cam.isOpened():
        cam.release()
    pygame.quit()
    sys.exit()
