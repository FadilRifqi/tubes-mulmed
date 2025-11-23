import pygame

# Color helper functions
def clamp_color(value):
    return max(0, min(255, value))

def darker(color, amount):
    return tuple(clamp_color(c - amount) for c in color)

# Color Definitions
BG = (200, 220, 255)
GREEN = (20, 120, 40)
BLACK = (0, 0, 0)
BROWN = (100, 60, 20)

# Floor Corners 
floor_top_left = (100, 300)
floor_top_right = (900, 300)
floor_bottom_right = (900, 430)
floor_bottom_left = (0, 430)
depth = 25
bottom_tl = (floor_top_left[0], floor_top_left[1] + depth)
bottom_tr = (floor_top_right[0], floor_top_right[1] + depth)
bottom_br = (floor_bottom_right[0], floor_bottom_right[1] + depth)
bottom_bl = (floor_bottom_left[0], floor_bottom_left[1] + depth)

# --- FUNGSI EXISTING (Lantai) ---

def get_floor_points(offset_x: float):
    ft_l = (floor_top_left[0] + offset_x, floor_top_left[1])
    ft_r = (floor_top_right[0], floor_top_right[1])
    fb_r = (floor_bottom_right[0], floor_bottom_right[1])
    fb_l = (floor_bottom_left[0] + offset_x, floor_bottom_left[1])

    bt_l = (bottom_tl[0] + offset_x, bottom_tl[1])
    bt_r = (bottom_tr[0], bottom_tr[1])
    bb_r = (bottom_br[0], bottom_br[1])
    bb_l = (bottom_bl[0] + offset_x, bottom_bl[1])

    return ft_l, ft_r, fb_r, fb_l, bt_l, bt_r, bb_r, bb_l

def draw_lantai(screen: pygame.Surface, offset_x: float):
    ft_l, ft_r, fb_r, fb_l, bt_l, bt_r, bb_r, bb_l = get_floor_points(offset_x)
    pygame.draw.polygon(screen, GREEN, [ft_l, ft_r, fb_r, fb_l])
    dark_green = darker(GREEN, 40)
    pygame.draw.polygon(screen, dark_green, [fb_l, fb_r, bb_r, bb_l])
    pygame.draw.polygon(screen, darker(GREEN, 60), [fb_r, ft_r, bt_r, bb_r])

def draw_lantai_edges(screen: pygame.Surface, offset_x: float):
    ft_l, ft_r, fb_r, fb_l, bt_l, bt_r, bb_r, bb_l = get_floor_points(offset_x)
    pygame.draw.polygon(screen, BLACK, [ft_l, ft_r, fb_r, fb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_l, fb_r, bb_r, bb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_r, ft_r, bt_r, bb_r], 2)

def get_floor_top_y():
    return floor_top_left[1] + 40

# --- FUNGSI BARU UNTUK DRAWING UI DAN SCREEN STATES ---

def draw_health_bar(screen: pygame.Surface, current: int, max_health: int, heart_full: pygame.Surface, heart_empty: pygame.Surface):
    """Menggambar bar nyawa (hati) di kiri atas layar. Hanya menggambar hati penuh."""
    
    if heart_full is None:
        # Fallback teks jika aset hati tidak ada
        hp_text = pygame.font.SysFont("consolas", 28).render(f"HP: {current}/{max_health}", True, (255, 0, 0))
        screen.blit(hp_text, (10, 10))
        return

    x_start = 10
    y_pos = 10
    
    # Gambar hati penuh sebanyak nyawa saat ini
    for i in range(current):
        screen.blit(heart_full, (x_start + i * heart_full.get_width(), y_pos))

def draw_score(screen: pygame.Surface, font: pygame.font.Font, score: int):
    """Menggambar skor di kanan atas."""
    score_text = font.render(f"SCORE: {score}", True, (255, 255, 255))
    screen.blit(score_text, (screen.get_width() - score_text.get_width() - 10, 10))

def draw_menu_screen(screen: pygame.Surface, font_menu: pygame.font.Font):
    """Menggambar layar menu awal."""
    screen.fill(BG)
    text = font_menu.render("SAPI GO!", True, BLACK)
    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 3))

    instr_text = pygame.font.SysFont("consolas", 24).render("Press SPACE to Start. (Nada Tinggi = Ramping, Nada Rendah = Nunduk)", True, BLACK)
    screen.blit(instr_text, (screen.get_width() // 2 - instr_text.get_width() // 2, screen.get_height() // 3 + 100))

def draw_game_over_screen(screen: pygame.Surface, font_menu: pygame.font.Font, font_score: pygame.font.Font, final_score: int):
    """Menggambar layar Game Over."""
    
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    go_text = font_menu.render("GAME OVER", True, (255, 50, 50))
    screen.blit(go_text, (screen.get_width() // 2 - go_text.get_width() // 2, screen.get_height() // 3))
    
    score_text = font_score.render(f"Final Score: {final_score}", True, (255, 255, 255))
    screen.blit(score_text, (screen.get_width() // 2 - score_text.get_width() // 2, screen.get_height() // 3 + 100))
    
    restart_text = pygame.font.SysFont("consolas", 24).render("Press SPACE to Try Again", True, (200, 200, 200))
    screen.blit(restart_text, (screen.get_width() // 2 - restart_text.get_width() // 2, screen.get_height() // 3 + 160))