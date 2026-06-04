import pygame
import random
import math

# --- Setup ---
pygame.init()
WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BIRTH LOTTERY")
clock = pygame.time.Clock()

# --- Palette ---
COLOR_BG     = (242, 238, 230)   # Helles Sand-Beige
COLOR_SLOT   = (225, 220, 210)   # Einlassungen/Zonen
COLOR_WOOD   = (150, 110, 70)    # Kiste (gegriffen)
COLOR_ACCENT = (190, 170, 150)   # Kiste (los)
COLOR_TEXT   = (80, 75, 70)

# 7-Segment / LED
LED_PANEL = (26, 20, 19)
LED_ON    = (235, 45, 35)
LED_OFF   = (62, 26, 24)

# Roter Knopf
BTN_RED   = (208, 48, 42)
BTN_RED_HI= (236, 72, 62)
BTN_DARK  = (138, 26, 22)
BTN_RING  = (92, 20, 17)

# Lottoschein
PAPER  = (250, 248, 243)
INK    = (58, 53, 50)
PAPER_SHADOW = (205, 200, 190)

# --- Fonts ---
f_btn    = pygame.font.SysFont("Courier New", 30, bold=True)
f_head   = pygame.font.SysFont("Courier New", 24, bold=True)
f_hint   = pygame.font.SysFont("Courier New", 16, bold=True)
f_sub    = pygame.font.SysFont("Courier New", 14, bold=True)
f_euro   = pygame.font.SysFont("Courier New", 58, bold=True)

# Schein-Fonts
ft_title = pygame.font.SysFont("Courier New", 19, bold=True)
ft_big   = pygame.font.SysFont("Courier New", 22, bold=True)
ft_bold  = pygame.font.SysFont("Courier New", 15, bold=True)
ft_norm  = pygame.font.SysFont("Courier New", 15, bold=False)
ft_small = pygame.font.SysFont("Courier New", 12, bold=True)

# =========================================================
#  7-SEGMENT ANZEIGE
# =========================================================
SEG_MAP = {
    '0': "abcdef", '1': "bc",   '2': "abdeg", '3': "abcdg", '4': "bcfg",
    '5': "acdfg",  '6': "acdefg", '7': "abc", '8': "abcdefg", '9': "abcdfg",
}

def _hseg(x1, x2, cy, t):
    h = t / 2
    return [(int(x1), int(cy)), (int(x1+h), int(cy-h)), (int(x2-h), int(cy-h)),
            (int(x2), int(cy)), (int(x2-h), int(cy+h)), (int(x1+h), int(cy+h))]

def _vseg(cx, y1, y2, t):
    h = t / 2
    return [(int(cx), int(y1)), (int(cx+h), int(y1+h)), (int(cx+h), int(y2-h)),
            (int(cx), int(y2)), (int(cx-h), int(y2-h)), (int(cx-h), int(y1+h))]

def draw_digit(surf, ch, ox, oy, w, h, t):
    xl, xr = ox + t, ox + w - t
    yt, ym, yb = oy + t, oy + h / 2, oy + h - t
    segs = {
        'a': _hseg(xl, xr, yt, t), 'g': _hseg(xl, xr, ym, t), 'd': _hseg(xl, xr, yb, t),
        'f': _vseg(xl, yt, ym, t), 'b': _vseg(xr, yt, ym, t),
        'e': _vseg(xl, ym, yb, t), 'c': _vseg(xr, ym, yb, t),
    }
    on = SEG_MAP.get(ch, "")
    for name, poly in segs.items():
        pygame.draw.polygon(surf, LED_ON if name in on else LED_OFF, poly)

def draw_score(surf, value):
    """Score als rote 7-Segment-Zahl auf dunklem LED-Panel mit € dahinter."""
    s = f"{value:02d}"
    dw, dh, t, gap = 30, 52, 7, 9
    num_w = len(s) * dw + (len(s) - 1) * gap
    euro_surf = f_euro.render("€", True, LED_ON)
    euro_w = euro_surf.get_width()
    inner_w = num_w + 16 + euro_w
    pad_x, pad_y = 26, 14
    panel_w = inner_w + 2 * pad_x
    panel_h = dh + 2 * pad_y
    px = WIDTH // 2 - panel_w // 2
    py = 46
    # Panel
    pygame.draw.rect(surf, LED_PANEL, (px, py, panel_w, panel_h), border_radius=10)
    pygame.draw.rect(surf, (12, 9, 9), (px, py, panel_w, panel_h), width=2, border_radius=10)
    # Ziffern
    cx = px + pad_x
    cy = py + pad_y
    for ch in s:
        draw_digit(surf, ch, cx, cy, dw, dh, t)
        cx += dw + gap
    # Euro-Zeichen
    surf.blit(euro_surf, (cx - gap + 16, cy + dh // 2 - euro_surf.get_height() // 2))

# =========================================================
#  LOTTOSCHEIN (einmal vorrendern)
# =========================================================
TW = 300  # Scheinbreite

TICKET_LINES = [
    ("BIRTH LOTTERY",         ft_title, INK,        6),
    ("",                      None,     None,       2),
    ("sep",                   None,     None,       4),
    ("LOS-NR. 1.387.402.991", ft_small, INK,        2),
    ("ZIEHUNG 04.06.2026",    ft_small, INK,        2),
    ("sep",                   None,     None,       6),
    ("** GLÜCKWUNSCH! **",    ft_bold,  INK,        4),
    ("Sie wurden zugewiesen:", ft_norm, INK,        8),
    ("> GLOBALER NORDEN <",   ft_big,   (40,140,60), 8),
    ("Zuteilung : BÜROJOB",   ft_norm,  INK,        2),
    ("Status    : ANGESTELLT", ft_norm, INK,        4),
    ("sep",                   None,     None,       4),
    ("Kein Umtausch möglich.", ft_small, INK,       2),
    ("Behalten Sie den Schein.", ft_small, INK,     6),
]

def build_ticket():
    # Hoehe berechnen
    pad_top, pad_bot = 22, 26
    y = pad_top
    for text, font, _, after in TICKET_LINES:
        lh = 8 if text == "sep" else (font.get_height() if font else 8)
        y += lh + after
    th = y + pad_bot
    surf = pygame.Surface((TW, th), pygame.SRCALPHA)
    # Papier
    pygame.draw.rect(surf, PAPER, (0, 0, TW, th))
    # Seitliche Perforation (Loecher in BG-Farbe)
    for hy in range(14, th - 8, 18):
        pygame.draw.circle(surf, COLOR_BG, (0, hy), 4)
        pygame.draw.circle(surf, COLOR_BG, (TW, hy), 4)
    # Text
    y = pad_top
    for text, font, color, after in TICKET_LINES:
        if text == "sep":
            for dx in range(14, TW - 14, 10):
                pygame.draw.line(surf, (175, 170, 162), (dx, y + 4), (dx + 5, y + 4), 2)
            y += 8 + after
            continue
        if text == "":
            y += 8 + after
            continue
        line = font.render(text, True, color)
        surf.blit(line, (TW // 2 - line.get_width() // 2, y))
        y += font.get_height() + after
    # Gezackte Unterkante (abgerissen)
    zig = 9
    for zx in range(0, TW, zig):
        pygame.draw.polygon(surf, COLOR_BG,
                            [(zx, th - 8), (zx + zig // 2, th), (zx + zig, th - 8),
                             (zx + zig, th), (zx, th)])
    return surf, th

TICKET_SURF, TH = build_ticket()
SLOT_Y = 26  # Oberkante Druckerschlitz

# =========================================================
#  SPIEL-VARIABLEN
# =========================================================
STATE_START, STATE_TICKET, STATE_GAME = "start", "ticket", "game"
state = STATE_START

# Button-Animation
btn_center = (WIDTH // 2, HEIGHT // 2 + 10)
btn_radius = 64
btn_clicked = False
btn_click_time = 0

# Ticket-Animation
ticket_start = 0
PRINT_MS = 2200  # Dauer Druckvorgang

# Minigame (wie im Prototyp)
box_x = 150.0
box_y = HEIGHT - 100
has_grip = False
money = 0
is_respawning = False
particles = []

def create_particles(x, y, color, amount=10):
    for _ in range(amount):
        particles.append({
            "pos": [x, y],
            "vel": [random.uniform(-2, 2), random.uniform(-2, 2)],
            "life": 255,
            "color": color,
        })

def reset_game():
    global box_x, has_grip, money, is_respawning, particles
    box_x = 150.0
    has_grip = False
    money = 0
    is_respawning = False
    particles = []

# =========================================================
#  MAIN LOOP
# =========================================================
running = True
while running:
    now = pygame.time.get_ticks()
    mx, my = pygame.mouse.get_pos()
    screen.fill(COLOR_BG)

    # ---------- EVENTS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == STATE_START and not btn_clicked:
                d = math.hypot(mx - btn_center[0], my - btn_center[1])
                if d <= btn_radius:
                    btn_clicked = True
                    btn_click_time = now
            elif state == STATE_TICKET:
                # Erst weiter, wenn der Schein fertig gedruckt ist
                if (now - ticket_start) >= PRINT_MS:
                    reset_game()
                    state = STATE_GAME

    # =========================================================
    #  STATE: START (roter Knopf)
    # =========================================================
    if state == STATE_START:
        title = f_head.render("BIRTH LOTTERY", True, COLOR_TEXT)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

        hover = math.hypot(mx - btn_center[0], my - btn_center[1]) <= btn_radius

        # Druck-Animation berechnen
        depress = 0.0
        if btn_clicked:
            tprog = (now - btn_click_time) / 320.0
            depress = min(1.0, tprog)
            if tprog >= 1.0:
                btn_clicked = False
                ticket_start = now
                state = STATE_TICKET

        # Pulsierender Glow (zieht den Blick an)
        pulse = (math.sin(now * 0.005) + 1) / 2
        glow_r = btn_radius + 14 + int(pulse * 8)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (230, 60, 50, 55 + int(pulse * 40)),
                           (glow_r, glow_r), glow_r)
        screen.blit(glow, (btn_center[0] - glow_r, btn_center[1] - glow_r))

        # Sockel / Ring
        pygame.draw.circle(screen, BTN_RING, btn_center, btn_radius + 8)
        pygame.draw.circle(screen, BTN_DARK, btn_center, btn_radius + 3)

        # Knopf (hebt sich, sinkt bei Druck ein)
        lift = int((1 - depress) * 6)
        top_center = (btn_center[0], btn_center[1] - lift)
        face = BTN_RED_HI if (hover and not btn_clicked) else BTN_RED
        pygame.draw.circle(screen, BTN_DARK, btn_center, btn_radius)        # Schattenseite
        pygame.draw.circle(screen, face, top_center, btn_radius)            # Oberseite
        # Glanzlicht
        hl = pygame.Surface((btn_radius * 2, btn_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(hl, (255, 255, 255, 70),
                           (btn_radius, int(btn_radius * 0.7)), int(btn_radius * 0.55))
        screen.blit(hl, (top_center[0] - btn_radius, top_center[1] - btn_radius))

        label = f_btn.render("START", True, (255, 235, 230))
        screen.blit(label, (top_center[0] - label.get_width() // 2,
                            top_center[1] - label.get_height() // 2))

        if (now // 600) % 2 == 0 and not btn_clicked:
            hint = f_hint.render("» Knopf drücken «", True, COLOR_ACCENT)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 60))

    # =========================================================
    #  STATE: TICKET (Lottoschein wird gedruckt)
    # =========================================================
    elif state == STATE_TICKET:
        elapsed = now - ticket_start
        prog = min(1.0, elapsed / PRINT_MS)
        # Gestufter Vorschub -> mechanisches Druckgefühl
        revealed = (int(prog * TH) // 16) * 16
        revealed = max(0, min(TH, revealed))

        tx = WIDTH // 2 - TW // 2
        if prog < 1.0:
            tx += int(2 * math.sin(now * 0.04))  # leichtes Wackeln

        # Schatten
        if revealed > 0:
            sh = pygame.Surface((TW, revealed), pygame.SRCALPHA)
            sh.fill((*PAPER_SHADOW, 90))
            screen.blit(sh, (tx + 4, SLOT_Y + 6))
            screen.blit(TICKET_SURF, (tx, SLOT_Y), area=pygame.Rect(0, 0, TW, revealed))

        # Druckerschlitz (liegt über der Oberkante)
        sx = WIDTH // 2 - (TW // 2 + 30)
        pygame.draw.rect(screen, (70, 66, 62), (sx, SLOT_Y - 18, TW + 60, 20), border_radius=6)
        pygame.draw.rect(screen, (20, 18, 16), (sx + 14, SLOT_Y - 4, TW + 32, 6), border_radius=3)

        if prog >= 1.0 and (now // 500) % 2 == 0:
            go = f_hint.render("» klicken zum Starten «", True, COLOR_TEXT)
            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT - 28))

    # =========================================================
    #  STATE: GAME (Minigame – Kern wie im Prototyp)
    # =========================================================
    elif state == STATE_GAME:
        # --- Logik: Interaktion ---
        box_rect = pygame.Rect(box_x - 40, box_y - 40, 80, 80)
        dist = abs(mx - box_x)

        if box_rect.collidepoint(mx, my) and not is_respawning:
            has_grip = True

        if has_grip:
            if dist > 140:
                has_grip = False
            else:
                speed = (mx - box_x) * 0.08
                box_x += speed
                if abs(speed) > 0.5:
                    create_particles(box_x, box_y + 40, (180, 170, 150), 1)

        # --- Logik: Zielankunft ---
        if box_x > 850 and not is_respawning:
            money += random.randint(25, 95)
            create_particles(box_x, box_y, COLOR_WOOD, 20)
            is_respawning = True
            has_grip = False
            box_x = 150
        if is_respawning:
            is_respawning = False
            create_particles(box_x, box_y, COLOR_ACCENT, 10)

        # --- Zeichnen ---
        pygame.draw.rect(screen, COLOR_SLOT, (110, HEIGHT - 110, 80, 5), border_radius=5)
        pygame.draw.rect(screen, COLOR_SLOT, (810, HEIGHT - 110, 80, 5), border_radius=5)

        for p in particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 7
            if p["life"] <= 0:
                particles.remove(p)
            else:
                s = pygame.Surface((5, 5), pygame.SRCALPHA)
                pygame.draw.rect(s, (*p["color"], max(0, p["life"])), s.get_rect())
                screen.blit(s, p["pos"])

        if not is_respawning:
            color = COLOR_WOOD if has_grip else COLOR_ACCENT
            b_rect = pygame.Rect(box_x - 40, box_y - 40, 80, 80)
            shadow = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 20), shadow.get_rect(), border_radius=4)
            screen.blit(shadow, (box_x - 35, box_y - 35))
            pygame.draw.rect(screen, color, b_rect, border_radius=2)
            pygame.draw.line(screen, COLOR_BG, (box_x - 30, box_y - 30), (box_x + 30, box_y + 30), 2)
            pygame.draw.line(screen, COLOR_BG, (box_x + 30, box_y - 30), (box_x - 30, box_y + 30), 2)

        # Score als rote 7-Segment-Anzeige
        draw_score(screen, money)
        sub = f_sub.render("EARNED REVENUE", True, COLOR_ACCENT)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 124))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()