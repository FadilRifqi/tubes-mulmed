import pygame

class Sapi(pygame.sprite.Sprite):
    def __init__(self, normal_path, low_path, high_path, x_pos, target_size=(320, 320)):
        super().__init__()

        self.target_w, self.target_h = target_size
        self.frame_count = 6 
        self.animation_speed = 0.2 

        # Load ketiga strip animasi
        self.animations = {
            'normal': self.load_strip(normal_path),
            'nunduk': self.load_strip(low_path),
            'ramping': self.load_strip(high_path)
        }

        self.state = 'normal'
        self.frame_index = 0
        self.image = self.animations[self.state][0]

        # Hitbox (Rect)
        # Hitbox dibuat sangat kecil dan akan disesuaikan di update()
        self.rect = self.image.get_rect()
        self.rect.x = x_pos

        # Simpan ukuran visual dasar
        self.base_w = self.target_w
        self.base_h = self.target_h
        
        # Offset visual untuk mengatur gambar sapi di atas lantai
        self.visual_offset_y = 170 

    def load_strip(self, path):
        """Memuat gambar strip horizontal dan memotongnya menjadi 6 frame."""
        frames = []
        try:
            sheet = pygame.image.load(path).convert_alpha()
            sheet_w = sheet.get_width()
            
            # Hitung lebar per frame (total lebar dibagi 6)
            frame_width = sheet_w // self.frame_count
            
            for i in range(self.frame_count):
                rect = pygame.Rect(i * frame_width, 0, frame_width, sheet.get_height())
                frame_surf = sheet.subsurface(rect)

                # Resize ke target size
                frame_surf = pygame.transform.scale(frame_surf, (self.target_w, self.target_h))
                frames.append(frame_surf)

        except (FileNotFoundError, pygame.error) as e:
            # Fallback (Kotak Merah)
            for _ in range(self.frame_count):
                surf = pygame.Surface((self.target_w, self.target_h))
                surf.fill((255, 0, 0)) 
                frames.append(surf)

        return frames

    def update(self, dt: int, is_nunduk: bool, is_ramping: bool):
        # 1. Tentukan State dan Reset Animasi
        previous_state = self.state
        if is_nunduk:
            self.state = 'nunduk'
        elif is_ramping:
            self.state = 'ramping'
        else:
            self.state = 'normal'

        if self.state != previous_state:
            self.frame_index = 0

        # 2. Jalankan Animasi
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.animations[self.state]):
            self.frame_index = 0

        self.image = self.animations[self.state][int(self.frame_index)]

        # 3. Update Hitbox (Rect) Secara Dinamis
        # Simpan posisi tengah bawah sebagai jangkar agar rect tumbuh ke atas/samping
        current_center_x = self.rect.centerx
        current_bottom = self.rect.bottom

        # Hitbox dibuat relatif terhadap ukuran visual (disesuaikan dengan posisi 3D di lantai)
        if self.state == 'nunduk':
            new_h = int(self.base_h * 0.3)
            new_w = int(self.base_w * 0.25)
        elif self.state == 'ramping':
            new_h = int(self.base_h * 0.5)
            new_w = int(self.base_w * 0.1)
        else: # Normal
            new_h = int(self.base_h * 0.5)
            new_w = int(self.base_w * 0.2)

        # Terapkan ukuran baru
        self.rect.width = new_w
        self.rect.height = new_h

        # Kembalikan posisi ke titik jangkar (bawah tengah)
        self.rect.centerx = current_center_x
        self.rect.bottom = current_bottom


    def draw(self, screen: pygame.Surface):
        """Menggambar visual sapi (sprite) di layar."""
        # Gambar sprite visual di tengah rect hitbox
        draw_x = self.rect.centerx - (self.image.get_width() // 2)
        draw_y = (self.rect.bottom - self.image.get_height()) + self.visual_offset_y

        screen.blit(self.image, (draw_x, draw_y))

    def set_floor_pos(self, floor_y: int):
        """Menyetel posisi vertikal sapi berdasarkan lantai."""
        self.rect.bottom = floor_y