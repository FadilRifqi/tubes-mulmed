import pygame
import random
import os

# Definisikan kelas Pagar dan ObstacleManager yang dibutuhkan main.py
class Pagar:
    """Kelas untuk mengelola aset dan konfigurasi pagar tunggal."""
    def __init__(self, image_path: str):
        self.image_path = image_path
        SCALE_X, SCALE_Y = 4, 1.0
        try:
            self._img = pygame.image.load(image_path).convert_alpha()
            w, h = self._img.get_width(), self._img.get_height()
            self._img = pygame.transform.smoothscale(self._img, (int(w*SCALE_X), int(h*SCALE_Y)))
        except:
            self._img = None

    def get_image(self) -> pygame.Surface:
        return self._img

    @staticmethod
    def _get_collision_rect(img, draw_rect, hb_config: dict):
        cfg = hb_config.get(img, {"shrink": (0, 0), "offset": (0, 0)})
        cr = draw_rect.inflate(-cfg["shrink"][0], -cfg["shrink"][1])
        cr.move_ip(cfg["offset"][0], cfg["offset"][1])
        return cr

    @staticmethod
    def build_hitbox_config(pagar_img, pagar2_img) -> dict:
        # Konfigurasi hitbox yang digunakan main.py
        hb = {}
        if pagar_img:
            hb[pagar_img] = {"shrink": (int(pagar_img.get_width()*0.6), 12), "offset": (-90, -8)}
        if pagar2_img:
            hb[pagar2_img] = {"shrink": (int(pagar2_img.get_width()*0.75), 16), "offset": (-20, -10)}
        return hb

class ObstacleManager:
    """Mengelola spawning, pergerakan, dan collision semua rintangan."""
    def __init__(self, screen_width, variants, pagar2_img, spawn_interval_ms, speed, offsets, bounce_px, hb_config):
        self.screen_width = screen_width
        self.variants = variants
        self.pagar2_img = pagar2_img
        # Asumsi self.pagar_img adalah pagar.png
        self.pagar_img = [img for img in variants if img is not pagar2_img][0] if pagar2_img in variants else None
        self.spawn_interval = spawn_interval_ms
        self.sprite_spawn_timer = 0
        self.sprite_list = [] # Daftar semua rintangan aktif
        self.speed = speed
        self.offsets = offsets
        self.bounce_px = bounce_px
        self.hb_config = hb_config

    def shift_world(self, dx: float):
        """Menggeser posisi semua pagar (dipanggil saat bounce/kamera bergerak)."""
        for s in self.sprite_list:
            s["x"] += dx

    def update_and_prepare_draw(self, dt, player_rect, z_down, x_down, camera_follow_cb, debug_hitbox):
        self.sprite_spawn_timer += dt
        
        # 1. SPAWN LOGIC
        if self.sprite_spawn_timer > self.spawn_interval:
            imgs_for_set = [random.choice(self.variants) for _ in range(2)]
            if self.pagar2_img and (imgs_for_set[0] is self.pagar2_img or imgs_for_set[1] is self.pagar2_img):
                imgs_for_set = [self.pagar2_img]
                is_single = True
            else:
                is_single = False
                
            num_imgs = len(imgs_for_set)
            self.sprite_list.append({
                "x": self.screen_width + 120,
                "imgs": imgs_for_set,
                "single": is_single,
                "locks": [False] * num_imgs,
                "hit_prev": [False] * num_imgs,
            })
            self.sprite_spawn_timer = 0
            
        collided_first_any = False
        collided_second_any = False
        back_draw = []
        front_draw = []
        debug_boxes = []
        
        # 2. UPDATE, COLLISION CHECK, DAN DRAW PREPARATION
        for s in self.sprite_list[:]:
            s["x"] -= self.speed
            base_x = s["x"]

            if base_x < -200:
                self.sprite_list.remove(s)
                continue
            
            # Tentukan offset gambar
            offsets = self.offsets
            if s["single"]:
                mid_dx = (self.offsets[0][0] + self.offsets[1][0]) / 2.0
                mid_dy = (self.offsets[0][1] + self.offsets[1][1]) / 2.0
                offsets = [(mid_dx, mid_dy + 20)]

            for i in range(len(s["imgs"])):
                dx, dy = offsets[i]
                img = s["imgs"][i]
                r = img.get_rect()
                r.midbottom = (base_x + dx, player_rect.midbottom[1] + dy) 
                
                c = Pagar._get_collision_rect(img, r, self.hb_config)
                collides = player_rect.colliderect(c)
                
                # Pagar 1 (pagar.png) -> Z/Nunduk
                # Pagar 2 (pagar_2.png) -> X/Ramping
                required_ok = (img is self.pagar2_img and x_down) or (img is self.pagar_img and z_down)

                if collides:
                    if required_ok:
                        # Lolos!
                        if img is self.pagar2_img:
                            collided_second_any = True
                        else:
                            collided_first_any = True
                        s["locks"][i] = True
                    elif not s["hit_prev"][i]:
                        # Tabrakan! Lakukan bounce dan KURANGI NYAWA via callback
                        camera_follow_cb(self.bounce_px) # <-- Mengurangi Nyawa di main.py
                        self.sprite_spawn_timer -= 900 
                
                # Tentukan draw layer
                draw_front = s["locks"][i] or (collides and required_ok)
                (front_draw if draw_front else back_draw).append((img, r))
                
                if debug_hitbox:
                    color = (255, 0, 255) if img is self.pagar2_img else (255, 200, 0)
                    debug_boxes.append((color, c))
                
                s["hit_prev"][i] = collides

        return collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes