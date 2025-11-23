# TODO: buat agar pagar berbentuk objek agar lebih clean code
import pygame
import random
from typing import List, Tuple, Dict, Any

# Sesuaikan Image Scale
SCALE_X = 4
SCALE_Y = 1.0

class Pagar:
    def __init__(self, image_path: str):
        self.image = pygame.image.load(image_path).convert_alpha()
        w = self.image.get_width()
        h = self.image.get_height()
        if SCALE_X != 1.0 or SCALE_Y != 1.0:
            self.image = pygame.transform.scale(
                self.image,
                (int(w * SCALE_X), int(h * SCALE_Y))
            )
        self.rect = self.image.get_rect()

    def get_image(self) -> pygame.Surface:
        return self.image

    @staticmethod
    def get_collision_rect(img: pygame.Surface, draw_rect: pygame.Rect, hb_config: Dict[pygame.Surface, Dict[str, Tuple[int, int]]]) -> pygame.Rect:
        cfg = hb_config.get(img, {"shrink": (0, 0), "offset": (0, 0)})
        cr = draw_rect.inflate(-cfg["shrink"][0], -cfg["shrink"][1])
        cr.move_ip(cfg["offset"][0], cfg["offset"][1])
        return cr

    @staticmethod
    def build_hitbox_config(pagar_img: pygame.Surface, pagar2_img: pygame.Surface) -> Dict[pygame.Surface, Dict[str, Tuple[int, int]]]:
        hb: Dict[pygame.Surface, Dict[str, Tuple[int, int]]] = {}
        if pagar_img is not None:
            shrink_x = int(pagar_img.get_width() * 0.6)
            hb[pagar_img] = {"shrink": (shrink_x, 12), "offset": (-90, -8)}
        if pagar2_img is not None:
            shrink_x = int(pagar2_img.get_width() * 0.75)
            hb[pagar2_img] = {"shrink": (shrink_x, 16), "offset": (-10, -10)}
        return hb

class ObstacleSet:
    # Satu himpunan pagar (1 atau 2 sprite)
    def __init__(self, x: float, imgs: List[pygame.Surface], single: bool):
        self.x = x
        self.imgs = imgs
        self.single = single
        self.locks: List[bool] = [False] if single else [False, False]
        self.hit_prev: List[bool] = [False] if single else [False, False]
        self.nudge: List[int] = [0] if single else [0, 0]

class ObstacleManager:
    # Kelola spawn, update, dan draw pagar
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
        self.spawn_interval_ms = spawn_interval_ms
        self.speed = speed
        self.offsets = offsets
        self.bounce_px = bounce_px
        self.hb_config = hb_config
        self.sprite_spawn_timer = 0
        self.sets: List[ObstacleSet] = []

    def shift_world(self, dx: float):
        for s in self.sets:
            s.x += dx

    def spawn_if_ready(self):
        if self.sprite_spawn_timer > self.spawn_interval_ms:
            imgs_for_set = [random.choice(self.variants) for _ in range(2)]
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
        z_down: bool,
        x_down: bool,
        camera_follow_cb,
        debug_hitbox: bool,
        screen: pygame.Surface,
    ) -> Tuple[bool, bool, List[Tuple[pygame.Surface, pygame.Rect]], List[Tuple[pygame.Surface, pygame.Rect]], List[Tuple[Tuple[int,int,int], pygame.Rect]]]:
        self.sprite_spawn_timer += dt
        self.spawn_if_ready()

        collided_second_any = False
        collided_first_any = False
        back_draw: List[Tuple[pygame.Surface, pygame.Rect]] = []
        front_draw: List[Tuple[pygame.Surface, pygame.Rect]] = []
        debug_boxes: List[Tuple[Tuple[int,int,int], pygame.Rect]] = []
        floor_top_y = player_rect.midbottom[1]  # sudah di-set oleh caller sebelum panggilan ini

        for s in self.sets[:]:
            s.x -= self.speed
            base_x = s.x

            if s.single:
                mid_dx = (self.offsets[0][0] + self.offsets[1][0]) / 2.0
                mid_dy = (self.offsets[0][1] + self.offsets[1][1]) / 2.0
                img = s.imgs[0]
                r = img.get_rect()
                r.midbottom = (base_x + mid_dx, floor_top_y + mid_dy + 20)
                c = Pagar.get_collision_rect(img, r, self.hb_config)
                collides = player_rect.colliderect(c)
                required_ok = z_down
                if collides:
                    if required_ok:
                        collided_second_any = True
                        s.locks[0] = True
                    elif not s.hit_prev[0]:
                        camera_follow_cb(self.bounce_px)
                        self.sprite_spawn_timer -= 900
                (front_draw if (s.locks[0] or (collides and required_ok)) else back_draw).append((img, r))
                if debug_hitbox:
                    pygame.draw.rect(screen, (255, 0, 255), c, 2)
                s.hit_prev[0] = collides
            else:
                for i,(dx,dy) in enumerate(self.offsets):
                    img = s.imgs[i if i < len(s.imgs) else 0]
                    r = img.get_rect()
                    r.midbottom = (base_x + dx, floor_top_y + dy)
                    c = Pagar.get_collision_rect(img, r, self.hb_config)
                    collides = player_rect.colliderect(c)
                    if i == 0:
                        if collides:
                            collided_first_any = True
                        back_draw.append((img,r))
                        if debug_hitbox:
                            debug_boxes.append(((255,200,0), c))
                        s.hit_prev[0] = collides
                    else:
                        required_ok = x_down
                        if collides:
                            if required_ok:
                                collided_second_any = True
                                s.locks[1] = True
                            elif not s.hit_prev[1]:
                                camera_follow_cb(self.bounce_px)
                                self.sprite_spawn_timer -= 900
                        draw_front = s.locks[1] or (collides and required_ok)
                        (front_draw if draw_front else back_draw).append((img,r))
                        if debug_hitbox:
                            pygame.draw.rect(screen, (255, 0, 255), c, 2)
                        s.hit_prev[1] = collides

            # hapus jika di luar layar kiri
            max_dx = max(dx for dx,_ in self.offsets)
            any_img = s.imgs[0]
            if base_x + max_dx + any_img.get_width() < 0:
                self.sets.remove(s)

        return collided_first_any, collided_second_any, back_draw, front_draw, debug_boxes
