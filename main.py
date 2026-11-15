import os
import sys
import json
import pygame
import fitz  # PyMuPDF

pygame.init()
pygame.joystick.init()

info = pygame.display.Info()
PHYS_W, PHYS_H = info.current_w, info.current_h
screen = pygame.display.set_mode((PHYS_W, PHYS_H), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for j in joysticks:
    j.init()

font = pygame.font.SysFont("dejavusans", 20)
small_font = pygame.font.SysFont("dejavusans", 15)

THEMES = [
    {
        "name": "Тёмная",
        "bg": (25, 25, 30),
        "text": (230, 230, 235),
        "dir": (255, 210, 90),
        "accent": (80, 160, 255),
        "exit": (255, 100, 100),
        "hint": (150, 150, 150),
        "reader_bg": (15, 15, 15),
        "invert_pdf": False,
        "tint": None,
    },
    {
        "name": "Светлая",
        "bg": (240, 242, 245),
        "text": (30, 32, 36),
        "dir": (180, 110, 10),
        "accent": (20, 100, 210),
        "exit": (200, 45, 45),
        "hint": (100, 105, 115),
        "reader_bg": (230, 230, 230),
        "invert_pdf": False,
        "tint": None,
    },
    {
        "name": "Ночь (инверсия)",
        "bg": (10, 10, 12),
        "text": (200, 205, 210),
        "dir": (220, 175, 70),
        "accent": (100, 180, 255),
        "exit": (230, 80, 80),
        "hint": (120, 125, 130),
        "reader_bg": (0, 0, 0),
        "invert_pdf": True,
        "tint": None,
    },
    {
        "name": "Сепия",
        "bg": (46, 38, 30),
        "text": (238, 226, 206),
        "dir": (235, 185, 105),
        "accent": (215, 145, 70),
        "exit": (235, 95, 85),
        "hint": (175, 160, 140),
        "reader_bg": (38, 32, 26),
        "invert_pdf": False,
        "tint": (250, 235, 205),
    },
]

BTN_A = 2
BTN_B = 3
BTN_X = 4
BTN_Y = 5
BTN_L1 = 6
BTN_R1 = 7
BTN_L2 = 8
BTN_R2 = 9
BTN_SELECT = 10
BTN_START = 11
BTN_MENU = 12

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_DIR, "alexpdf_state.json")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("pages", {})
                data.setdefault("last_dir", None)
                data.setdefault("theme", 0)
                data.setdefault("continuous", False)
                data.setdefault("rotation", 0)
                return data
        except Exception:
            pass
    return {"pages": {}, "last_dir": None, "theme": 0, "continuous": False, "rotation": 0}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def quit_app():
    pygame.display.quit()
    pygame.quit()
    os._exit(0)


def check_exit_combo():
    for j in joysticks:
        if j.get_numbuttons() > BTN_MENU:
            if j.get_button(BTN_MENU) and j.get_button(BTN_START):
                return True
    return False


def get_logical_size(rotation):
    if rotation % 180 == 90:
        return PHYS_H, PHYS_W
    return PHYS_W, PHYS_H


def present_canvas(canvas, rotation):
    if rotation == 0:
        screen.blit(canvas, (0, 0))
    else:
        rotated = pygame.transform.rotate(canvas, rotation)
        screen.blit(rotated, (0, 0))
    pygame.display.flip()


def map_hat_for_rotation(hat_x, hat_y, rotation):
    if rotation == 90:
        return hat_y, -hat_x
    elif rotation == 180:
        return -hat_x, -hat_y
    elif rotation == 270:
        return -hat_y, hat_x
    return hat_x, hat_y


def draw_help_overlay(canvas, theme):
    scr_w, scr_h = canvas.get_size()
    overlay = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    canvas.blit(overlay, (0, 0))

    margin = 24
    box_rect = pygame.Rect(margin, margin, scr_w - margin * 2, scr_h - margin * 2)
    pygame.draw.rect(canvas, theme["bg"], box_rect, border_radius=10)
    pygame.draw.rect(canvas, theme["accent"], box_rect, width=2, border_radius=10)

    title = font.render("Справка по управлению AlexPDF", True, theme["accent"])
    canvas.blit(title, (margin + 16, margin + 12))

    help_lines = [
        ("Крестовина", "Выбор файла / прокрутка страницы"),
        ("SELECT / A", "Открыть папку или PDF / Зум при чтении"),
        ("A / B", "Следующая / предыдущая страница (±1)"),
        ("X / Y", "Быстрая перемотка (±10 страниц)"),
        ("L1", "Режим: Постранично / Непрерывно"),
        ("R1", "Показать или скрыть эту справку"),
        ("L2", "Сменить тему оформления"),
        ("R2", "Повернуть экран на 90°"),
        ("MENU", "Вернуться к списку файлов"),
        ("MENU + START", "Выйти из приложения"),
    ]

    y = margin + 48
    line_step = max(22, (box_rect.height - 85) // len(help_lines))
    for btn_name, desc in help_lines:
        if y + 20 > box_rect.bottom - 28:
            break
        b_surf = small_font.render(f"[{btn_name}]", True, theme["dir"])
        d_surf = small_font.render(desc, True, theme["text"])
        canvas.blit(b_surf, (margin + 16, y))
        canvas.blit(d_surf, (margin + 150, y))
        y += line_step

    close_hint = small_font.render("Нажмите [R1] или [B] чтобы закрыть справку", True, theme["hint"])
    canvas.blit(close_hint, (margin + 16, box_rect.bottom - 26))


def get_dir_entries(directory, saved_pages):
    entries = []

    if directory == "ROOT_STORAGE":
        if os.path.exists("/mnt/mmc"):
            entries.append(("dir", "[SD1] Внутренняя карта (/mnt/mmc)", "/mnt/mmc"))
        if os.path.exists("/mnt/sdcard"):
            entries.append(("dir", "[SD2] Вторая карта (/mnt/sdcard)", "/mnt/sdcard"))
        entries.append(("exit", "[ ВЫХОД ИЗ ПРИЛОЖЕНИЯ ]", None))
        return entries

    parent = os.path.dirname(directory.rstrip("/"))
    if directory in ("/mnt/mmc", "/mnt/sdcard") or not parent or parent == "/mnt":
        entries.append(("up", "[ .. ] Выбор карты памяти (SD1 / SD2)", "ROOT_STORAGE"))
    else:
        entries.append(("up", "[ .. ] Назад", parent))

    if os.path.exists(directory):
        try:
            items = os.listdir(directory)
            dirs = []
            files = []
            for name in items:
                if name.startswith("."):
                    continue
                full_path = os.path.join(directory, name)
                if os.path.isdir(full_path):
                    dirs.append(("dir", f"[DIR] {name}", full_path))
                elif name.lower().endswith(".pdf"):
                    saved_p = saved_pages.get(full_path)
                    suffix = f" [стр. {saved_p + 1}]" if saved_p and saved_p > 0 else ""
                    files.append(("file", name + suffix, full_path))

            dirs.sort(key=lambda x: x[1].lower())
            files.sort(key=lambda x: x[1].lower())
            entries.extend(dirs)
            entries.extend(files)
        except PermissionError:
            pass

    entries.append(("exit", "[ ВЫХОД ИЗ ПРИЛОЖЕНИЯ ]", None))
    return entries


def file_browser(start_dir, state):
    saved_pages = state.get("pages", {})
    current_dir = start_dir if (start_dir == "ROOT_STORAGE" or os.path.exists(start_dir)) else "ROOT_STORAGE"
    entries = get_dir_entries(current_dir, saved_pages)
    selected = 0
    show_help = False
    clock = pygame.time.Clock()

    def next_theme():
        state["theme"] = (state.get("theme", 0) + 1) % len(THEMES)
        save_state(state)

    def next_rotation():
        state["rotation"] = (state.get("rotation", 0) + 90) % 360
        save_state(state)

    while True:
        if check_exit_combo():
            quit_app()

        theme = THEMES[state.get("theme", 0) % len(THEMES)]
        rotation = state.get("rotation", 0) % 360
        scr_w, scr_h = get_logical_size(rotation)
        canvas = pygame.Surface((scr_w, scr_h))

        canvas.fill(theme["bg"])
        header_path = "Выбор накопителя" if current_dir == "ROOT_STORAGE" else current_dir
        title = font.render(f"AlexPDF | {header_path}", True, theme["accent"])
        canvas.blit(title, (20, 15))

        max_rows = max(5, (scr_h - 90) // 28)
        start_idx = max(0, selected - (max_rows - 4))
        for idx, (etype, label, _) in enumerate(entries[start_idx:start_idx + max_rows]):
            real_idx = start_idx + idx
            if real_idx == selected:
                color = theme["accent"]
                prefix = "> "
            else:
                prefix = "  "
                if etype == "exit":
                    color = theme["exit"]
                elif etype in ("dir", "up"):
                    color = theme["dir"]
                else:
                    color = theme["text"]

            max_chars = max(25, (scr_w - 60) // 11)
            txt = font.render(prefix + label[:max_chars], True, color)
            canvas.blit(txt, (20, 55 + idx * 28))

        hint = small_font.render(
            f"[SELECT/A] Открыть [B] Назад [R1] Помощь [L2] Тема [R2] {rotation}°",
            True, theme["hint"]
        )
        canvas.blit(hint, (20, scr_h - 25))

        if show_help:
            draw_help_overlay(canvas, theme)

        present_canvas(canvas, rotation)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_app()

            elif event.type == pygame.KEYDOWN:
                if show_help:
                    if event.key in (pygame.K_h, pygame.K_ESCAPE, pygame.K_RETURN):
                        show_help = False
                    continue
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(entries)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(entries)
                elif event.key == pygame.K_h:
                    show_help = True
                elif event.key == pygame.K_t:
                    next_theme()
                elif event.key == pygame.K_r:
                    next_rotation()
                elif event.key == pygame.K_RETURN:
                    etype, _, target = entries[selected]
                    if etype == "exit":
                        quit_app()
                    elif etype in ("dir", "up"):
                        current_dir = target
                        state["last_dir"] = current_dir
                        save_state(state)
                        entries = get_dir_entries(current_dir, saved_pages)
                        selected = 0
                    elif etype == "file":
                        return target, current_dir
                elif event.key == pygame.K_ESCAPE:
                    quit_app()

            elif event.type == pygame.JOYBUTTONDOWN:
                menu_held = any(j.get_numbuttons() > BTN_MENU and j.get_button(BTN_MENU) for j in joysticks)
                if menu_held:
                    continue

                if event.button == BTN_R1:
                    show_help = not show_help
                    continue

                if show_help:
                    if event.button in (BTN_B, BTN_A, BTN_SELECT):
                        show_help = False
                    continue

                if event.button == BTN_L2:
                    next_theme()
                elif event.button == BTN_R2:
                    next_rotation()
                elif event.button == BTN_B:
                    for etype, _, target in entries:
                        if etype == "up":
                            current_dir = target
                            state["last_dir"] = current_dir
                            save_state(state)
                            entries = get_dir_entries(current_dir, saved_pages)
                            selected = 0
                            break

                elif event.button in (BTN_SELECT, BTN_A):
                    etype, _, target = entries[selected]
                    if etype == "exit":
                        quit_app()
                    elif etype in ("dir", "up"):
                        current_dir = target
                        state["last_dir"] = current_dir
                        save_state(state)
                        entries = get_dir_entries(current_dir, saved_pages)
                        selected = 0
                    elif etype == "file":
                        return target, current_dir

            elif event.type == pygame.JOYHATMOTION and not show_help:
                raw_x, raw_y = event.value
                _, hat_y = map_hat_for_rotation(raw_x, raw_y, rotation)
                if hat_y == -1:
                    selected = (selected + 1) % len(entries)
                elif hat_y == 1:
                    selected = (selected - 1) % len(entries)

            elif event.type == pygame.JOYAXISMOTION and not show_help:
                if event.axis == 1:
                    if event.value > 0.7:
                        selected = (selected + 1) % len(entries)
                    elif event.value < -0.7:
                        selected = (selected - 1) % len(entries)

        clock.tick(20)


def render_page(doc, page_num, zoom, theme, target_w):
    page = doc.load_page(page_num)
    base_scale = target_w / page.rect.width
    mat = fitz.Matrix(base_scale * zoom, base_scale * zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    if theme.get("invert_pdf"):
        pix.invert_irect(pix.irect)

    surf = pygame.image.frombuffer(pix.samples, (pix.width, pix.height), "RGB").convert()

    if theme.get("tint"):
        tint_surf = pygame.Surface(surf.get_size())
        tint_surf.fill(theme["tint"])
        surf.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_MULT)

    return surf


def read_pdf(filepath, state):
    doc = fitz.open(filepath)
    total_pages = len(doc)
    saved_pages = state.setdefault("pages", {})
    page_num = min(saved_pages.get(filepath, 0), max(0, total_pages - 1))
    zoom = 1.0
    offset_x, offset_y = 0, 0
    page_cache = {}
    PAGE_GAP = 10
    show_help = False
    clock = pygame.time.Clock()

    def clear_cache():
        page_cache.clear()

    def get_cached_page(p, theme_idx, target_w):
        key = (p, zoom, theme_idx, target_w)
        if key not in page_cache:
            if len(page_cache) > 5:
                page_cache.clear()
            page_cache[key] = render_page(doc, p, zoom, THEMES[theme_idx], target_w)
        return page_cache[key]

    def update_saved_page(p):
        saved_pages[filepath] = p
        save_state(state)

    def next_theme_in_reader():
        state["theme"] = (state.get("theme", 0) + 1) % len(THEMES)
        save_state(state)
        clear_cache()

    def next_rotation_in_reader():
        state["rotation"] = (state.get("rotation", 0) + 90) % 360
        save_state(state)
        clear_cache()

    while True:
        if check_exit_combo():
            update_saved_page(page_num)
            doc.close()
            quit_app()

        theme_idx = state.get("theme", 0) % len(THEMES)
        theme = THEMES[theme_idx]
        continuous = state.get("continuous", False)
        rotation = state.get("rotation", 0) % 360
        scr_w, scr_h = get_logical_size(rotation)
        canvas = pygame.Surface((scr_w, scr_h))

        page_surf = get_cached_page(page_num, theme_idx, scr_w)
        page_w, page_h = page_surf.get_width(), page_surf.get_height()

        if not show_help and joysticks and joysticks[0].get_numhats() > 0:
            raw_x, raw_y = joysticks[0].get_hat(0)
            hat_x, hat_y = map_hat_for_rotation(raw_x, raw_y, rotation)
            step = 22
            if continuous:
                if hat_y == -1:
                    offset_y -= step
                    while offset_y <= -(page_h + PAGE_GAP) and page_num < total_pages - 1:
                        offset_y += (page_h + PAGE_GAP)
                        page_num += 1
                        update_saved_page(page_num)
                        page_surf = get_cached_page(page_num, theme_idx, scr_w)
                        page_h = page_surf.get_height()
                    if page_num == total_pages - 1:
                        min_y = min(0, scr_h - page_h)
                        if offset_y < min_y:
                            offset_y = min_y
                elif hat_y == 1:
                    offset_y += step
                    while offset_y > 0 and page_num > 0:
                        page_num -= 1
                        update_saved_page(page_num)
                        page_surf = get_cached_page(page_num, theme_idx, scr_w)
                        page_h = page_surf.get_height()
                        offset_y -= (page_h + PAGE_GAP)
                    if page_num == 0 and offset_y > 0:
                        offset_y = 0
            else:
                if hat_y == 1:
                    offset_y = min(0, offset_y + step)
                elif hat_y == -1:
                    offset_y = max(min(0, scr_h - page_h), offset_y - step)

            if hat_x == -1:
                offset_x = min(0, offset_x + step)
            elif hat_x == 1:
                offset_x = max(min(0, scr_w - page_w), offset_x - step)

        offset_x = max(min(0, scr_w - page_w), min(0, offset_x))
        if not continuous:
            offset_y = max(min(0, scr_h - page_h), min(0, offset_y))

        canvas.fill(theme["reader_bg"])
        canvas.blit(page_surf, (offset_x, offset_y))

        if continuous:
            curr_y = offset_y + page_h + PAGE_GAP
            next_p = page_num + 1
            while curr_y < scr_h and next_p < total_pages:
                next_surf = get_cached_page(next_p, theme_idx, scr_w)
                canvas.blit(next_surf, (offset_x, curr_y))
                curr_y += next_surf.get_height() + PAGE_GAP
                next_p += 1

        mode_label = "Непрер." if continuous else "Постр."
        status = small_font.render(
            f"Стр.{page_num + 1}/{total_pages} | {int(zoom*100)}% | {mode_label} [L1] | Помощь [R1]",
            True, (255, 255, 255), (0, 0, 0)
        )
        canvas.blit(status, (10, scr_h - 22))

        if show_help:
            draw_help_overlay(canvas, theme)

        present_canvas(canvas, rotation)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                update_saved_page(page_num)
                doc.close()
                quit_app()

            elif event.type == pygame.JOYBUTTONDOWN:
                menu_held = any(j.get_numbuttons() > BTN_MENU and j.get_button(BTN_MENU) for j in joysticks)

                if event.button == BTN_R1:
                    show_help = not show_help
                    continue

                if show_help:
                    if event.button in (BTN_B, BTN_A, BTN_SELECT):
                        show_help = False
                    continue

                if event.button == BTN_L1:
                    state["continuous"] = not state.get("continuous", False)
                    save_state(state)
                    if not state["continuous"]:
                        offset_y = max(min(0, scr_h - page_h), min(0, offset_y))
                elif event.button == BTN_A and page_num < total_pages - 1:
                    page_num += 1
                    offset_y = 0
                    update_saved_page(page_num)
                elif event.button == BTN_B and page_num > 0:
                    page_num -= 1
                    offset_y = 0
                    update_saved_page(page_num)
                elif event.button == BTN_X and page_num < total_pages - 1:
                    page_num = min(total_pages - 1, page_num + 10)
                    offset_y = 0
                    update_saved_page(page_num)
                elif event.button == BTN_Y and page_num > 0:
                    page_num = max(0, page_num - 10)
                    offset_y = 0
                    update_saved_page(page_num)
                elif event.button == BTN_L2:
                    next_theme_in_reader()
                elif event.button == BTN_R2:
                    next_rotation_in_reader()
                    offset_x, offset_y = 0, 0
                elif event.button == BTN_SELECT and not menu_held:
                    zoom = 1.0 if zoom >= 2.0 else zoom + 0.5
                    clear_cache()
                elif event.button == BTN_MENU:
                    start_held = any(j.get_numbuttons() > BTN_START and j.get_button(BTN_START) for j in joysticks)
                    if not start_held:
                        update_saved_page(page_num)
                        doc.close()
                        return

        clock.tick(30)


def main():
    state = load_state()
    default_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/mmc/ROMS/PDF"
    current_dir = state.get("last_dir") or default_dir

    while True:
        selected_pdf, current_dir = file_browser(current_dir, state)
        if not selected_pdf:
            quit_app()
        read_pdf(selected_pdf, state)


if __name__ == "__main__":
    main()
