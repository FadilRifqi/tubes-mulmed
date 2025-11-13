import pygame
import sys
import os
import numpy as np
import cv2
from audio import Audio


audio = Audio()
audio.start()

# asset path
pagar_1_image_path = os.path.join(os.getcwd(), 'assets', 'pagar.png')
pagar_2_image_path = os.path.join(os.getcwd(), 'assets', 'pagar_2.png')
# TODO: ganti player dengan gambar sapi
sapi_path = os.path.join(os.getcwd(), 'assets', 'sapi.png')

# pygame init
pygame.init()

# set ukuran layar
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sapi Go")
font = pygame.font.SysFont("consolas", 28)
clock = pygame.time.Clock()

from pagar import Pagar, ObstacleManager
import environment

# buat object
pagar_1 = Pagar(pagar_1_image_path)
pagar_2 = Pagar(pagar_2_image_path)

# Setup video capture untuk latar belakang game
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Gagal membuka webcam. Pastikan kamera terhubung.")

# offset dan speed kamera
offset_x = 0.0
speed_x = -10

# definisi gambar dan rect
pagar_img = pagar_1.get_image()
pagar_rect = pagar_img.get_rect()

pagar2_img = pagar_2.get_image()
pagar2_rect = pagar2_img.get_rect()

# varian pagar
PAGAR_VARIANTS = [img for img in (pagar_img, pagar2_img) if img is not None]

# hitbox pagar
HB_FOR_IMG = Pagar.build_hitbox_config(pagar_img, pagar2_img)


# Kecepatan dan offset sprite pagar
SPRITE_SPEED = 3
SPRITE_SET_OFFSETS = [(20, 20), (170, 40)]

# Player dan debug hitbox
PLAYER_W, PLAYER_H = 26, 58
PLAYER_X = 130
DEBUG_HITBOX = True

# Bounce tuning
BOUNCE_PX = 200

# TODO: Ganti player dengan gambar sapi
player_rect = pygame.Rect(0, 0, PLAYER_W, PLAYER_H)

# object untuk mengelola pagar
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
    # Geser dunia (lantai + semua pagar) ke kanan saat player dibounce ke kiri
    offset_x += dx
    manager.shift_world(dx)

# Set resolusi kamera agar lebih optimal
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Set fps background
FRAME_INTERVAL_MS = 72
time_since_last_frame = 0
background_surf = None

running = True
try:
    while running:
        dt = clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False

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

        # Background
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

        offset_x += speed_x
        environment.draw_lantai(screen, offset_x)
        environment.draw_lantai_edges(screen, offset_x)

        # Update obstacles
        floor_top_y = environment.get_floor_top_y()
        player_rect.midbottom = (PLAYER_X, floor_top_y)

        collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes = manager.update_and_prepare_draw(
            dt=dt,
            player_rect=player_rect,
            z_down=nunduk,
            x_down=ramping,
            camera_follow_cb=camera_follow_on_bounce,
            debug_hitbox=DEBUG_HITBOX
        )

        for img, r in back_draw:
            screen.blit(img, r)

        if os.path.exists(sapi_path):
            player_img = pygame.image.load(sapi_path).convert_alpha()
            player_img = pygame.transform.smoothscale(player_img, (PLAYER_W, PLAYER_H))
            screen.blit(player_img, player_rect.topleft)
        else:
            pygame.draw.rect(screen, (50, 120, 220), player_rect)

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
