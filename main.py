import pygame
import sys
import random
import os



pygame.init()

# Ukuran layar
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sapi Go")

clock = pygame.time.Clock()

# Warna
BG = (200, 220, 255)
GREEN = (20, 120, 40)
BLACK = (0, 0, 0)
BROWN = (100, 60, 20)

# Fungsi bantu warna
def clamp_color(value):
    return max(0, min(255, value))
def darker(color, amount):
    return tuple(clamp_color(c - amount) for c in color)

# Lantai
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
speed_x = -10  # -1 px/frame ke kiri

# ...existing code...

BLACK = (0, 0, 0)
BROWN = (100, 60, 20)

try:
    pagar_img = pygame.image.load(os.path.join("assets", "pagar.png")).convert_alpha()

    # Skala hanya di sumbu X
    SCALE_X = 4  # perbesar lebar 1.5x
    SCALE_Y = 1.0  # tinggi tetap sama

    if SCALE_X != 1.0 or SCALE_Y != 1.0:
        w, h = pagar_img.get_width(), pagar_img.get_height()
        new_size = (int(w * SCALE_X), int(h * SCALE_Y))
        pagar_img = pygame.transform.smoothscale(pagar_img, new_size)

    pagar_rect = pagar_img.get_rect()

except Exception as e:
    pagar_img = None
    pagar_rect = None
    print(f"Gagal load assets/pagar.png: {e}")

try:
    pagar2_img = pygame.image.load(os.path.join("assets", "pagar_2.png")).convert_alpha()
    if SCALE_X != 1.0 or SCALE_Y != 1.0:
        w2, h2 = pagar2_img.get_width(), pagar2_img.get_height()
        pagar2_img = pygame.transform.smoothscale(pagar2_img, (int(w2 * SCALE_X), int(h2 * SCALE_Y)))
    pagar2_rect = pagar2_img.get_rect()
except Exception as e:
    pagar2_img = None
    pagar2_rect = None
    print(f"Gagal load assets/pagar_2.png: {e}")

PAGAR_VARIANTS = [img for img in (pagar_img, pagar2_img) if img is not None]

def _build_hitbox_config():
    hb = {}
    if pagar_img is not None:
        # Example: shrink 40% of width and 12 px height; lift hitbox up 8 px
        shrink_x = int(pagar_img.get_width() * 0.6)
        hb[pagar_img] = {"shrink": (shrink_x, 12), "offset": (-90, -8)}
    if pagar2_img is not None:
        # Example: slightly different tuning for pagar_2
        shrink_x = int(pagar2_img.get_width() * 0.75)
        hb[pagar2_img] = {"shrink": (shrink_x, 16), "offset": (-20, -10)}
    return hb

HB_FOR_IMG = _build_hitbox_config()

def get_collision_rect(img, draw_rect):
    cfg = HB_FOR_IMG.get(img, {"shrink": (0, 0), "offset": (0, 0)})
    # shrink tuple is (x, y) total shrink, applied symmetrically
    cr = draw_rect.inflate(-cfg["shrink"][0], -cfg["shrink"][1])
    cr.move_ip(cfg["offset"][0], cfg["offset"][1])
    return cr

# Tambah: daftar sprite pagar yang terus muncul
pagar_sprite_list = []          # setiap item: {"x": float} -> base x utk satu set pagar
SPRITE_SPAWN_GAP = 180          # jarak antar pagar (px)
SPRITE_SPEED = 3                # kecepatan gerak set pagar (px/frame)
SPRITE_SET_OFFSETS = [(20, 20), (170, 40)]  # satu set = 2 sprite: (dx, dy) relatif terhadap base x

# Player dan debug hitbox
PLAYER_W, PLAYER_H = 26, 58
PLAYER_X = 130                 # posisi X player (ujung kiri lantai kira-kira)
DEBUG_HITBOX = True    

# Bounce tuning
BOUNCE_PX = 200

# -------------------------------------
# MAIN LOOP
# -------------------------------------
pagar_list = []
spawn_timer = 0
sprite_spawn_timer = 0


player_rect = pygame.Rect(0, 0, PLAYER_W, PLAYER_H)

def camera_follow_on_bounce(dx):
    global offset_x, pagar_sprite_list
    # geser lantai (pakai offset_x) dan semua pagar
    offset_x += dx
    for s in pagar_sprite_list:
        s["x"] += dx

running = True
while running:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    # Tambah: status tombol Z (disable collision saat ditekan)
    keys = pygame.key.get_pressed()
    z_down = keys[pygame.K_z]
    x_down = keys[pygame.K_x]

    # Update offset x tiap frame (-1 px/frame)
    offset_x += speed_x

    # Hitung titik lantai yang sudah digeser di sumbu X
    ft_l = (floor_top_left[0] + offset_x, floor_top_left[1])
    ft_r = (floor_top_right[0] , floor_top_right[1])
    fb_r = (floor_bottom_right[0] , floor_bottom_right[1])
    fb_l = (floor_bottom_left[0] + offset_x, floor_bottom_left[1])

    bt_l = (bottom_tl[0] + offset_x, bottom_tl[1])
    bt_r = (bottom_tr[0] , bottom_tr[1])
    bb_r = (bottom_br[0] , bottom_br[1])
    bb_l = (bottom_bl[0] + offset_x, bottom_bl[1])

    screen.fill(BG)

    # --- LANTAI --- 
    pygame.draw.polygon(screen, GREEN, [ft_l, ft_r, fb_r, fb_l])
    dark_green = darker(GREEN, 40)
    pygame.draw.polygon(screen, dark_green, [fb_l, fb_r, bb_r, bb_l])  # depan
    pygame.draw.polygon(screen, darker(GREEN, 60), [fb_r, ft_r, bt_r, bb_r])  # kanan

    # Garis tepi
    pygame.draw.polygon(screen, BLACK, [ft_l, ft_r, fb_r, fb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_l, fb_r, bb_r, bb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_r, ft_r, bt_r, bb_r], 2)


    if PAGAR_VARIANTS:
        floor_top_y = floor_top_left[1] + 40  # y garis atas lantai

        player_rect.midbottom = (PLAYER_X, floor_top_y)

        # spawn set pagar (2 sprite per set), masing-masing pilih varian acak
        sprite_spawn_timer += dt
        if sprite_spawn_timer > 2500:  # tiap ~0.9 detik
            imgs_for_set = [random.choice(PAGAR_VARIANTS) for _ in range(2)]
            # jika salah satu atau kedua yang terpilih adalah pagar2_img -> tampilkan hanya pagar2 saja (single)
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
                "hit_prev": [False] if is_single else [False, False],  # untuk bounce sekali per kontak
                "nudge": [0] if is_single else [0, 0],                  # dorongan per-sprite (px)
            })
            sprite_spawn_timer = 0

        collided_second_any = False
        collided_first_any = False

        # Kumpulkan draw-call jadi dua grup:
        # - back_draw: digambar sebelum player
        # - front_draw: digambar setelah player (agar player "di belakang" sprite tsb)
        back_draw = []
        front_draw = []
        debug_boxes = []  # (color, rect)

        # update + draw tiap set + cek tabrakan
        for s in pagar_sprite_list[:]:
            s["x"] -= SPRITE_SPEED
            base_x = s["x"]

            if s.get("single"):
                # gambar 1 sprite di tengah antara dua offset
                mid_dx = (SPRITE_SET_OFFSETS[0][0] + SPRITE_SET_OFFSETS[1][0]) / 2.0
                mid_dy = (SPRITE_SET_OFFSETS[0][1] + SPRITE_SET_OFFSETS[1][1]) / 2.0
                img = s["imgs"][0]
                r = img.get_rect()
                r.midbottom = (base_x + mid_dx, floor_top_y + mid_dy + 20)

                # collision rect (hitbox ungu)
                c = get_collision_rect(img, r)
                collides = player_rect.colliderect(c)

                # tombol yang diwajibkan berdasarkan jenis gambar
                required_ok = (img is pagar2_img and x_down) or (img is pagar_img and z_down)

                if collides:
                    if required_ok:
                        collided_second_any = True
                        s["locks"][0] = True  # kunci: setelah lolos, selalu di depan
                    elif not s["hit_prev"][0]:
                        # bounce sekali pada saat mulai kontak
                        camera_follow_on_bounce(BOUNCE_PX)

                # gambar depan hanya jika allowed (atau sudah terkunci)
                ((front_draw if (s["locks"][0] or (collides and required_ok)) else back_draw)
                 ).append((img, r))

                if DEBUG_HITBOX:
                    debug_boxes.append(((255, 0, 255), c))

                s["hit_prev"][0] = collides

            else:
                # dua sprite per set
                for i, (dx, dy) in enumerate(SPRITE_SET_OFFSETS):
                    img = s.get("imgs", PAGAR_VARIANTS)[i if "imgs" in s else 0]
                    r = img.get_rect()
                    r.midbottom = (base_x + dx, floor_top_y + dy)
                    required_ok = (img is pagar2_img and x_down) or (img is pagar_img and z_down)

                    c = get_collision_rect(img, r)
                    collides = player_rect.colliderect(c)

                    if i == 0:
                        if collides:
                            collided_first_any = True

                        back_draw.append((img, r))
                        if DEBUG_HITBOX:
                            debug_boxes.append(((255, 200, 0), c))
                        s["hit_prev"][0] = collides

                    else:
                        # pagar kedua (ungu) => wajib X
                        if collides:
                            if required_ok:
                                collided_second_any = True
                                s["locks"][1] = True  # kunci agar selalu di depan
                            elif not s["hit_prev"][1]:
                                camera_follow_on_bounce(BOUNCE_PX)

                        draw_front = s["locks"][1] or (collides and required_ok)
                        (front_draw if draw_front else back_draw).append((img, r))
                        if DEBUG_HITBOX:
                            debug_boxes.append(((255, 0, 255), c))
                        s["hit_prev"][1] = collides

        # DRAW ORDER:
        # 1) Semua pagar "di belakang" player
        for img, r in back_draw:
            screen.blit(img, r)

        # 2) Player (warna sesuai collision)
        player_color = (200, 50, 50) if collided_second_any else (240, 180, 0) if collided_first_any else (50, 120, 220)
        pygame.draw.rect(screen, player_color, player_rect)
        if DEBUG_HITBOX:
            outline_color = (255, 0, 0) if collided_second_any else (255, 200, 0) if collided_first_any else (0, 200, 0)
            pygame.draw.rect(screen, outline_color, player_rect, 2)

        # 3) Pagar yang harus menutupi player (ungu yang sedang tabrakan)
        for img, r in front_draw:
            screen.blit(img, r)

        # 4) Debug hitbox di paling atas
        if DEBUG_HITBOX:
            for color, rect in debug_boxes:
                pygame.draw.rect(screen, color, rect, 1)


    pygame.display.flip()   