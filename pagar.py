import pygame
import random
from typing import List, Tuple, Dict, Any

# Scale Pagar (Digunakan saat memuat aset)
SCALE_X = 4
SCALE_Y = 1.0

class Pagar:
    """Kelas untuk mengelola aset pagar tunggal."""
    def __init__(self, image_path: str):
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            w = self.image.get_width()
            h = self.image.get_height()
            if SCALE_X != 1.0 or SCALE_Y != 1.0:
                self.image = pygame.transform.scale(
                    self.image,
                    (int(w * SCALE_X), int(h * SCALE_Y))
                )
        except pygame.error:
            # Fallback jika gambar tidak ditemukan
            print(f"ERROR: Gagal memuat aset pagar di {image_path}")
            self.image = pygame.Surface((100 * SCALE_X, 100 * SCALE_Y))
            self.image.fill((255, 0, 0)) # Kotak merah dummy
        
        self.rect = self.image.get_rect()

    def get_image(self) -> pygame.Surface:
        return self.image

    @staticmethod
    def get_collision_rect(img: pygame.Surface, draw_rect: pygame.Rect, hb_config: Dict[pygame.Surface, Dict[str, Tuple[int, int]]]) -> pygame.Rect:
        """Menghitung rect hitbox yang diperkecil dan di-offset dari draw_rect."""
        cfg = hb_config.get(img, {"shrink": (0, 0), "offset": (0, 0)})
        cr = draw_rect.inflate(-cfg["shrink"][0], -cfg["shrink"][1])
        cr.move_ip(cfg["offset"][0], cfg["offset"][1])
        return cr

    @staticmethod
    def build_hitbox_config(pagar_img: pygame.Surface, pagar2_img: pygame.Surface) -> Dict[pygame.Surface, Dict[str, Tuple[int, int]]]:
        """Menentukan konfigurasi hitbox untuk setiap tipe pagar."""
        hb: Dict[pygame.Surface, Dict[str, Tuple[int, int]]] = {}
        if pagar_img is not None:
            # Konfigurasi untuk Pagar 1 (pagar.png)
            shrink_x = int(pagar_img.get_width() * 0.6)
            hb[pagar_img] = {"shrink": (shrink_x, 12), "offset": (-90, -8)}
        if pagar2_img is not None:
            # Konfigurasi untuk Pagar 2 (pagar_2.png)
            shrink_x = int(pagar2_img.get_width() * 0.75)
            hb[pagar2_img] = {"shrink": (shrink_x, 16), "offset": (-10, -10)}
        return hb

class ObstacleSet:
    """Representasi satu himpunan pagar yang bergerak (bisa 1 atau 2 sprite)."""
    def __init__(self, x: float, imgs: List[pygame.Surface], single: bool):
        self.x = x
        self.imgs = imgs
        self.single = single
        # Lock: True jika pagar sudah dilewati dengan aksi yang benar (untuk draw di depan)
        self.locks: List[bool] = [False] if single else [False, False] 
        # Hit_prev: Mencegah hit/bounce berulang pada satu frame
        self.hit_prev: List[bool] = [False] if single else [False, False]

class ObstacleManager:
    """Kelola spawn, update, dan draw semua pagar."""
    def __init__(
        self,
        screen_width: int,
        variants: List[pygame.Surface],
        pagar2_img: pygame.Surface,
        spawn_interval_ms: int,
        speed: float,
        offsets: List[Tuple[int, int]],
        bounce_px: int,
        hb_config: Dict[pygame.Surface, Dict[str, Tuple[int, int]]]
    ):
        self.screen_width = screen_width
        self.variants = variants
        self.pagar2_img = pagar2_img
        self.pagar_img = [img for img in variants if img is not pagar2_img][0] if pagar2_img in variants else None

        self.spawn_interval_ms = spawn_interval_ms
        self.speed = speed
        self.offsets = offsets
        self.bounce_px = bounce_px
        self.hb_config = hb_config
        self.sprite_spawn_timer = 0
        self.sets: List[ObstacleSet] = []

    def shift_world(self, dx: float):
        """Geser semua pagar (dipanggil saat kamera di-bounce)."""
        for s in self.sets:
            s.x += dx

    def spawn_if_ready(self):
        """Memunculkan set pagar baru berdasarkan timer."""
        if self.sprite_spawn_timer > self.spawn_interval_ms:
            # Randomly pilih 2 pagar
            imgs_for_set = [random.choice(self.variants) for _ in range(2)]
            
            # Jika salah satunya adalah pagar 2 (ungu), jadikan set tunggal
            if self.pagar2_img is not None and (imgs_for_set[0] is self.pagar2_img or imgs_for_set[1] is self.pagar2_img):
                imgs_for_set = [self.pagar2_img]
                single = True
            else:
                single = False
            
            self.sets.append(ObstacleSet(self.screen_width + 120, imgs_for_set, single))
            self.sprite_spawn_timer = 0

    def update_and_prepare_draw(
        self,
        dt: int,
        player_rect: pygame.Rect,
        z_down: bool, # Nunduk (Nada Rendah)
        x_down: bool, # Ramping (Nada Tinggi)
        camera_follow_cb,
        debug_hitbox: bool,
        screen: pygame.Surface,
    ) -> Tuple[bool, bool, List[Tuple[pygame.Surface, pygame.Rect]], List[Tuple[pygame.Surface, pygame.Rect]], List[Tuple[Tuple[int,int,int], pygame.Rect]]]:
        """Update posisi, cek collision, dan siapkan daftar gambar untuk drawing."""
        self.sprite_spawn_timer += dt
        self.spawn_if_ready()

        collided_second_any = False
        collided_first_any = False
        back_draw: List[Tuple[pygame.Surface, pygame.Rect]] = []
        front_draw: List[Tuple[pygame.Surface, pygame.Rect]] = []
        debug_boxes: List[Tuple[Tuple[int,int,int], pygame.Rect]] = []
        
        # Floor_top_y diambil dari player_rect.midbottom[1] yang diset di main.py
        floor_top_y = player_rect.midbottom[1] 

        for s in self.sets[:]:
            s.x -= self.speed
            base_x = s.x
            
            # Logika untuk set tunggal (Pagar 2 / Ungu)
            if s.single:
                img = s.imgs[0]
                
                # Gunakan offset tengah untuk set tunggal
                mid_dx = (self.offsets[0][0] + self.offsets[1][0]) / 2.0
                mid_dy = (self.offsets[0][1] + self.offsets[1][1]) / 2.0
                r = img.get_rect()
                r.midbottom = (base_x + mid_dx, floor_top_y + mid_dy + 20)
                
                c = Pagar.get_collision_rect(img, r, self.hb_config)
                collides = player_rect.colliderect(c)
                
                # Pagar 2 (ungu) membutuhkan aksi RAMPING (x_down/Nada Tinggi)
                required_ok = x_down 
                
                if collides:
                    if required_ok:
                        collided_second_any = True
                        s.locks[0] = True
                    elif not s.hit_prev[0]:
                        camera_follow_cb(self.bounce_px) # Kena! Panggil bounce/kurangi nyawa
                        self.sprite_spawn_timer -= 900
                        
                # Tentukan draw layer: depan jika lolos/lock
                (front_draw if (s.locks[0] or (collides and required_ok)) else back_draw).append((img, r))
                
                if debug_hitbox:
                    pygame.draw.rect(screen, (255, 0, 255), c, 2)
                s.hit_prev[0] = collides
            
            # Logika untuk set ganda (Pagar 1 / Kuning)
            else:
                for i,(dx,dy) in enumerate(self.offsets):
                    img = s.imgs[i] 
                    r = img.get_rect()
                    r.midbottom = (base_x + dx, floor_top_y + dy)
                    c = Pagar.get_collision_rect(img, r, self.hb_config)
                    collides = player_rect.colliderect(c)
                    
                    if i == 0:
                        # Pagar Kuning pertama (offset 0)
                        if collides:
                            collided_first_any = True # Hanya perlu deteksi tabrakan
                        back_draw.append((img,r))
                        if debug_hitbox:
                            debug_boxes.append(((255,200,0), c))
                        s.hit_prev[0] = collides
                    else:
                        # Pagar Kuning kedua (offset 1)
                        # Pagar 1 (kuning) membutuhkan aksi NUNDUK (z_down/Nada Rendah)
                        required_ok = z_down 
                        
                        if collides:
                            if required_ok:
                                collided_second_any = True
                                s.locks[1] = True
                            elif not s.hit_prev[1]:
                                camera_follow_cb(self.bounce_px) # Kena! Panggil bounce/kurangi nyawa
                                self.sprite_spawn_timer -= 900
                                
                        draw_front = s.locks[1] or (collides and required_ok)
                        (front_draw if draw_front else back_draw).append((img,r))
                        
                        if debug_hitbox:
                            pygame.draw.rect(screen, (255, 0, 255), c, 2)
                        s.hit_prev[1] = collides

            # hapus jika di luar layar kiri
            if self.sets and base_x + max(dx for dx,_ in self.offsets) + s.imgs[0].get_width() < 0:
                self.sets.remove(s)

        return collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes