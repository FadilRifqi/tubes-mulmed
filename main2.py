import pygame
import sys
import random
import os
import sounddevice as sd
import numpy as np
import cv2 

pygame.init()

# Ukuran layar
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sapi Go")

clock = pygame.time.Clock()

# ======= SETUP WEBCAM (DITAMBAHKAN) =======
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Gagal membuka webcam. Pastikan kamera terhubung.")
    # Jika gagal membuka kamera, kita akan kembali menggunakan latar belakang warna default
# ==========================================

# ======= AUDIO SETUP (DARI KODE ASLI) =======
SR = 44100
BLOCKSIZE = 1024
audio_buffer = np.zeros(BLOCKSIZE)

def audio_callback(indata, frames, time, status):
    global audio_buffer
    audio_buffer = indata[:, 0].copy()

stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=SR, blocksize=BLOCKSIZE)
stream.start()

def detect_pitch(signal):
    signal = signal - np.mean(signal)
    corr = np.correlate(signal, signal, mode='full')
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    start = np.nonzero(d > 0)[0]
    if len(start) == 0:
        return None
    peak = np.argmax(corr[start[0]:]) + start[0]
    if peak == 0:
        return None
    pitch = SR / peak
    return pitch

# Warna
BG = (200, 220, 255) # Warna default jika webcam gagal
GREEN = (20, 120, 40)
BLACK = (0, 0, 0)
BROWN = (100, 60, 20)

# Fungsi bantu warna
def clamp_color(value):
    return max(0, min(255, value))
def darker(color, amount):
    return tuple(clamp_color(c - amount) for c in color)

# Lantai
# Koordinat lantai tetap, tetapi tidak lagi menggambar latar belakang warna BG
floor_top_left = (100, 300)
floor_top_right = (900, 300)
floor_bottom_right = (900, 430)
floor_bottom_left = (0, 430)
depth = 25
bottom_tl = (floor_top_left[0], floor_top_left[1] + depth)
bottom_tr = (floor_top_right[0], floor_top_right[1] + depth)
bottom_br = (floor_bottom_right[0], floor_bottom_right[1] + depth)
bottom_bl = (floor_bottom_left[0], floor_bottom_left[1] + depth)

# Tambahkan offset sumbu X (gerak -1 px per frame)
offset_x = 0
speed_x = -10

# Load Assets Pagar (disingkat)
pagar_img = None
pagar2_img = None
SCALE_X = 4
SCALE_Y = 1.0

try:
    # Asumsi Anda punya folder assets/ dan file pagar.png/pagar_2.png
    # Jika tidak ada file ini, kode akan menggunakan None
    pagar_img_raw = pygame.image.load(os.path.join("assets", "pagar.png")).convert_alpha()
    w, h = pagar_img_raw.get_width(), pagar_img_raw.get_height()
    pagar_img = pygame.transform.smoothscale(pagar_img_raw, (int(w * SCALE_X), int(h * SCALE_Y)))
except Exception as e:
    print(f"Gagal load assets/pagar.png: {e}")

try:
    pagar2_img_raw = pygame.image.load(os.path.join("assets", "pagar_2.png")).convert_alpha()
    w2, h2 = pagar2_img_raw.get_width(), pagar2_img_raw.get_height()
    pagar2_img = pygame.transform.smoothscale(pagar2_img_raw, (int(w2 * SCALE_X), int(h2 * SCALE_Y)))
except Exception as e:
    print(f"Gagal load assets/pagar_2.png: {e}")

PAGAR_VARIANTS = [img for img in (pagar_img, pagar2_img) if img is not None]

def _build_hitbox_config():
    hb = {}
    if pagar_img is not None:
        shrink_x = int(pagar_img.get_width() * 0.6)
        hb[pagar_img] = {"shrink": (shrink_x, 12), "offset": (-90, -8)}
    if pagar2_img is not None:
        shrink_x = int(pagar2_img.get_width() * 0.75)
        hb[pagar2_img] = {"shrink": (shrink_x, 16), "offset": (-20, -10)}
    return hb

HB_FOR_IMG = _build_hitbox_config()

def get_collision_rect(img, draw_rect):
    cfg = HB_FOR_IMG.get(img, {"shrink": (0, 0), "offset": (0, 0)})
    cr = draw_rect.inflate(-cfg["shrink"][0], -cfg["shrink"][1])
    cr.move_ip(cfg["offset"][0], cfg["offset"][1])
    return cr

SPRITE_SPEED = 3
SPRITE_SET_OFFSETS = [(20, 20), (170, 40)]
PLAYER_W, PLAYER_H = 26, 58
PLAYER_X = 130
DEBUG_HITBOX = True
BOUNCE_PX = 200

pagar_sprite_list = []
sprite_spawn_timer = 0
player_rect = pygame.Rect(0, 0, PLAYER_W, PLAYER_H)

def camera_follow_on_bounce(dx):
    global offset_x, pagar_sprite_list
    offset_x += dx
    for s in pagar_sprite_list:
        s["x"] += dx

# ================= MAIN LOOP =================

running = True
while running:
    dt = clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    # --- 1. Ambil & Gambar Video Webcam sebagai Latar Belakang ---
    ret, frame = cam.read()
    if ret:
        # Konversi warna BGR (OpenCV) ke RGB (Pygame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize ke ukuran layar game
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        # Buat surface dari numpy array
        surf = pygame.surfarray.make_surface(np.rot90(frame))
        # Gambar sebagai latar belakang
        screen.blit(surf, (0, 0))
    else:
        # Jika webcam gagal, gambar latar belakang default
        screen.fill(BG)
    # -----------------------------------------------------------

    # ====== LOGIKA KONTROL SUARA ======
    signal = audio_buffer.copy()
    pitch = detect_pitch(signal)

    z_down = False # Nada Tinggi
    x_down = False # Nada Rendah

    if pitch:
        if pitch > 250:
            z_down = True
        elif 80 < pitch < 160:
            x_down = True

    # ====== LOGIKA GERAK DAN GAMBAR GAME ======

    offset_x += speed_x

    # Menggambar Lantai di atas latar belakang webcam/warna
    ft_l = (floor_top_left[0] + offset_x, floor_top_left[1])
    ft_r = (floor_top_right[0] , floor_top_right[1])
    fb_r = (floor_bottom_right[0] , floor_bottom_right[1])
    fb_l = (floor_bottom_left[0] + offset_x, floor_bottom_left[1])
    bt_l = (bottom_tl[0] + offset_x, bottom_tl[1])
    bt_r = (bottom_tr[0] , bottom_tr[1])
    bb_r = (bottom_br[0] , bottom_br[1])
    bb_l = (bottom_bl[0] + offset_x, bottom_bl[1])

    # Menggambar 3D Lantai
    pygame.draw.polygon(screen, GREEN, [ft_l, ft_r, fb_r, fb_l])
    dark_green = darker(GREEN, 40)
    pygame.draw.polygon(screen, dark_green, [fb_l, fb_r, bb_r, bb_l])
    pygame.draw.polygon(screen, darker(GREEN, 60), [fb_r, ft_r, bt_r, bb_r])
    pygame.draw.polygon(screen, BLACK, [ft_l, ft_r, fb_r, fb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_l, fb_r, bb_r, bb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_r, ft_r, bt_r, bb_r], 2)


    # Logika Pagar dan Pemain
    if PAGAR_VARIANTS:
        floor_top_y = floor_top_left[1] + 40
        player_rect.midbottom = (PLAYER_X, floor_top_y)
        sprite_spawn_timer += dt

        # Logika Spawn Pagar
        if sprite_spawn_timer > 4000:
            # Pilihan pagar dan penentuan apakah single (pagar2) atau double
            imgs_for_set = [random.choice(PAGAR_VARIANTS) for _ in range(2)]
            if pagar2_img is not None and (imgs_for_set[0] is pagar2_img or imgs_for_set[1] is pagar2_img):
                imgs_for_set = [pagar2_img]
                is_single = True
            else:
                is_single = False

            pagar_sprite_list.append({
                "x": WIDTH + 120,
                "imgs": imgs_for_set,
                "single": is_single,
                "locks": [False] if is_single else [False, False],
                "hit_prev": [False] if is_single else [False, False],
                "nudge": [0] if is_single else [0, 0],
            })
            sprite_spawn_timer = 0

        collided_second_any = False
        collided_first_any = False

        back_draw = []
        front_draw = []
        debug_boxes = []

        # Update posisi dan cek tabrakan
        for s in pagar_sprite_list[:]:
            s["x"] -= SPRITE_SPEED
            base_x = s["x"]

            if s.get("single"):
                mid_dx = (SPRITE_SET_OFFSETS[0][0] + SPRITE_SET_OFFSETS[1][0]) / 2.0
                mid_dy = (SPRITE_SET_OFFSETS[0][1] + SPRITE_SET_OFFSETS[1][1]) / 2.0
                img = s["imgs"][0]
                r = img.get_rect()
                r.midbottom = (base_x + mid_dx, floor_top_y + mid_dy + 20)

                c = get_collision_rect(img, r)
                collides = player_rect.colliderect(c)

                # Cek input suara: x_down untuk pagar2_img (rendah), z_down untuk pagar_img (tinggi)
                required_ok = (img is pagar2_img and x_down) or (img is pagar_img and z_down)

                if collides:
                    if required_ok:
                        collided_second_any = True
                        s["locks"][0] = True
                    elif not s["hit_prev"][0]:
                        # Bounce (hukuman)
                        camera_follow_on_bounce(BOUNCE_PX)
                        sprite_spawn_timer -= 900

                ((front_draw if (s["locks"][0] or (collides and required_ok)) else back_draw)
                 ).append((img, r))

                if DEBUG_HITBOX:
                    debug_boxes.append(((255, 0, 255), c))

                s["hit_prev"][0] = collides

            else: # Dua pagar
                for i, (dx, dy) in enumerate(SPRITE_SET_OFFSETS):
                    img = s.get("imgs", PAGAR_VARIANTS)[i if "imgs" in s else 0]
                    r = img.get_rect()
                    r.midbottom = (base_x + dx, floor_top_y + dy)
                    required_ok = (img is pagar2_img and x_down) or (img is pagar_img and z_down)
                    c = get_collision_rect(img, r)
                    collides = player_rect.colliderect(c)

                    if i == 0: # Pagar pertama
                        if collides:
                            collided_first_any = True # Tabrakan dengan pagar pertama (selalu di belakang pemain)
                        back_draw.append((img, r))
                        if DEBUG_HITBOX:
                            debug_boxes.append(((255, 200, 0), c))
                        s["hit_prev"][0] = collides

                    else: # Pagar kedua
                        if collides:
                            if required_ok:
                                collided_second_any = True
                                s["locks"][1] = True
                            elif not s["hit_prev"][1]:
                                # Bounce (hukuman)
                                camera_follow_on_bounce(BOUNCE_PX)
                                sprite_spawn_timer -= 900

                        draw_front = s["locks"][1] or (collides and required_ok)
                        (front_draw if draw_front else back_draw).append((img, r))
                        if DEBUG_HITBOX:
                            debug_boxes.append(((255, 0, 255), c))
                        s["hit_prev"][1] = collides

        # Menggambar Pagar (belakang pemain)
        for img, r in back_draw:
            screen.blit(img, r)

        # Menggambar Pemain
        player_color = (200, 50, 50) if collided_second_any else (240, 180, 0) if collided_first_any else (50, 120, 220)
        pygame.draw.rect(screen, player_color, player_rect)
        if DEBUG_HITBOX:
            outline_color = (255, 0, 0) if collided_second_any else (255, 200, 0) if collided_first_any else (0, 200, 0)
            pygame.draw.rect(screen, outline_color, player_rect, 2)

        # Menggambar Pagar (depan pemain)
        for img, r in front_draw:
            screen.blit(img, r)

        # Menggambar Hitbox Debug
        if DEBUG_HITBOX:
            for color, rect in debug_boxes:
                pygame.draw.rect(screen, color, rect, 1)

    # --- 3. Update Tampilan ---
    pygame.display.flip()

# --- 4. Cleanup ---
cam.release()
stream.stop()
stream.close()
pygame.quit()
sys.exit() # Pastikan keluar dari sistem