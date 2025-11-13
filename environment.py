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
    pygame.draw.polygon(screen, dark_green, [fb_l, fb_r, bb_r, bb_l])  # depan
    pygame.draw.polygon(screen, darker(GREEN, 60), [fb_r, ft_r, bt_r, bb_r])  # kanan

def draw_lantai_edges(screen: pygame.Surface, offset_x: float):
    ft_l, ft_r, fb_r, fb_l, bt_l, bt_r, bb_r, bb_l = get_floor_points(offset_x)
    pygame.draw.polygon(screen, BLACK, [ft_l, ft_r, fb_r, fb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_l, fb_r, bb_r, bb_l], 2)
    pygame.draw.polygon(screen, BLACK, [fb_r, ft_r, bt_r, bb_r], 2)

def get_floor_top_y():
    return floor_top_left[1] + 40

def camera_follow_on_bounce(dx, offset_x, pagar_sprite_list):
    offset_x += dx
    for s in pagar_sprite_list:
        s["x"] += dx