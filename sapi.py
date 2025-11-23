import pygame

class Sapi(pygame.sprite.Sprite):
    def __init__(self, normal_path, low_path, high_path, x_pos, target_size=(80, 60)):
        super().__init__()

        self.target_w, self.target_h = target_size
        self.frame_count = 6 # Sesuai permintaan: 6 frame per file

        # Load ketiga file animasi
        self.animations = {
            'normal': self.load_strip(normal_path),
            'nunduk': self.load_strip(low_path),
            'ramping': self.load_strip(high_path)
        }

        self.state = 'normal'
        self.frame_index = 0
        self.animation_speed = 0.2 # Kecepatan animasi

        # Set image awal
        self.image = self.animations[self.state][0]

        # Setup Hitbox (Rect)
        self.rect = self.image.get_rect()
        self.rect.x = x_pos

        # Simpan ukuran hitbox dasar untuk referensi perubahan bentuk
        self.base_w = self.target_w
        self.base_h = self.target_h

    def load_strip(self, path):
        """Memuat gambar strip horizontal dan memotongnya menjadi 6 frame."""
        frames = []
        try:
            sheet = pygame.image.load(path).convert_alpha()
            sheet_w = sheet.get_width()
            sheet_h = sheet.get_height()

            # Hitung lebar per frame (total lebar dibagi 6)
            frame_width = sheet_w // self.frame_count
            frame_height = sheet_h

            for i in range(self.frame_count):
                # Ambil potongan rect horizontal
                rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame_surf = sheet.subsurface(rect)

                # Resize ke target size
                frame_surf = pygame.transform.scale(frame_surf, (self.target_w, self.target_h))
                frames.append(frame_surf)

        except (FileNotFoundError, pygame.error) as e:
            print(f"WARNING: Gagal memuat {path}. Menggunakan kotak merah dummy.")
            # Buat dummy frames (kotak merah) jika file belum ada
            for _ in range(self.frame_count):
                surf = pygame.Surface((self.target_w, self.target_h))
                surf.fill((255, 0, 0)) # Merah
                frames.append(surf)

        return frames

    def update(self, dt, is_nunduk, is_ramping):
        # 1. Tentukan State
        previous_state = self.state
        if is_nunduk:
            self.state = 'nunduk'
        elif is_ramping:
            self.state = 'ramping'
        else:
            self.state = 'normal'

        # Reset frame index jika state berubah agar animasi tidak loncat aneh
        if self.state != previous_state:
            self.frame_index = 0

        # 2. Jalankan Animasi (Looping 0 sampai 5)
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.animations[self.state]):
            self.frame_index = 0

        self.image = self.animations[self.state][int(self.frame_index)]

        # 3. Update Hitbox (Rect) Secara Dinamis
        # Kita simpan posisi tengah bawah agar perubahan ukuran tumbuh ke atas/samping
        current_center_x = self.rect.centerx
        current_bottom = self.rect.bottom

        if self.state == 'nunduk':
            # Hitbox jadi pendek (misal 60% tinggi)
            new_h = int(self.base_h * 0.6)
            new_w = int(self.base_w * 0.2)
        elif self.state == 'ramping':
            # Hitbox jadi kurus (misal 40% lebar)
            new_h = int(self.base_h * 0.6)
            new_w = int(self.base_w * 0.2)
        else: # Normal
            new_h = int(self.base_h * 0.6)
            new_w = int(self.base_w * 0.2)

        # Terapkan ukuran baru
        self.rect.width = new_w
        self.rect.height = new_h

        # Kembalikan posisi ke titik jangkar (bawah tengah)
        self.rect.centerx = current_center_x
        self.rect.bottom = current_bottom

    def draw(self, screen):
        # Gambar sprite visual di tengah rect hitbox
        draw_x = self.rect.centerx - (self.image.get_width() // 2)

        visual_offset_y = 170

        draw_y = (self.rect.bottom - self.image.get_height()) + visual_offset_y

        screen.blit(self.image, (draw_x, draw_y))

    def set_floor_pos(self, floor_y):
        self.rect.bottom = floor_y
