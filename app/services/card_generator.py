import io
import os
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def get_font(size: int, bold: bool = False):
    """Загружает геометрический чистый шрифт без сбоев."""
    candidates = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def get_emoji_font(size: int):
    """Загружает файл шрифта для эмодзи (паутина, огонь, кубки)."""
    for p in ["emoji.ttf", "NotoColorEmoji.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return None

def create_capper_card(
    capper_name: str,
    username: str,
    day_stats: dict,
    week_stats: dict,
    month_stats: dict,
    all_stats: dict
) -> io.BytesIO:
    # 1. Размеры и ультра-модный темный фон (Кибер-Графит 2026)
    width, height = 720, 860
    image = Image.new("RGBA", (width, height), (11, 15, 25, 255))
    draw = ImageDraw.Draw(image)

    # 2. Шрифты
    font_title = get_font(20, bold=True)
    font_regular = get_font(15, bold=False)
    font_bold = get_font(16, bold=True)
    font_stat_val = get_font(28, bold=True)
    font_card_val = get_font(18, bold=True)
    font_badge = get_font(13, bold=True)
    font_emoji = get_emoji_font(20)

    # 3. Цветовая палитра 2026
    CYAN = (0, 242, 254, 255)         # Неоновый циан
    GREEN = (52, 211, 153, 255)       # Мягкий изумрудный
    RED = (248, 113, 113, 255)        # Мягкий красный (при минусе)
    TEXT_WHITE = (255, 255, 255, 255)
    TEXT_MUTED = (148, 163, 184, 255) # Приглушенный сланец
    BG_CARD = (22, 30, 49, 255)       # Стеклоплашка
    BORDER_CARD = (40, 53, 80, 255)   # Неоновая обводка

    # --- БЛОК 1: ШАПКА / АВАТАР ---
    # Аватар
    draw.ellipse([30, 30, 90, 90], fill=(30, 41, 59, 255), outline=CYAN, width=2)
    avatar_char = username[0].upper() if username else (capper_name[0].upper() if capper_name else "C")
    draw.text((50, 48), avatar_char, font=font_title, fill=TEXT_WHITE)

    # Имя с паутиной
    display_user = f"🕸️ @{username} 🕸️" if username else f"🕸️ {capper_name} 🕸️"
    with Pilmoji(image) as pilmoji:
        if font_emoji:
            pilmoji.text((110, 38), display_user, font=font_title, fill=TEXT_WHITE, emoji_font=font_emoji)
        else:
            pilmoji.text((110, 38), display_user, font=font_title, fill=TEXT_WHITE)

    draw.text((110, 70), "⚡ Verified Live Capper", font=font_regular, fill=CYAN)

    # --- БЛОК 2: ALL-TIME ОБЩАЯ СТАТИСТИКА ---
    draw.rounded_rectangle([30, 120, 690, 260], radius=16, fill=BG_CARD, outline=BORDER_CARD, width=1)
    draw.text((50, 138), "📊 ОБЩАЯ СТАТИСТИКА (ALL-TIME)", font=font_badge, fill=CYAN)

    # ROI
    roi_col = GREEN if all_stats["roi"] >= 0 else RED
    draw.text((50, 175), f"{all_stats['roi']:+,.1f}%", font=font_stat_val, fill=roi_col)
    draw.text((50, 215), "ROI Верификатора", font=font_regular, fill=TEXT_MUTED)

    # Винрейт
    draw.text((275, 175), f"{all_stats['winrate']}%", font=font_stat_val, fill=TEXT_WHITE)
    draw.text((275, 215), f"Винрейт ({all_stats['wins']}В / {all_stats['losses']}П)", font=font_regular, fill=TEXT_MUTED)

    # Профит
    prof_col = GREEN if all_stats["profit"] >= 0 else RED
    draw.text((505, 175), f"{all_stats['profit']:+,.0f}", font=font_stat_val, fill=prof_col)
    draw.text((505, 215), "Профит (коины)", font=font_regular, fill=TEXT_MUTED)

    # --- БЛОК 3: ПЕРИОДЫ (Сегодня / 7 Дней / 30 Дней) ---
    periods = [
        ("🗓 СЕГОДНЯ", day_stats, 30),
        ("⚡ 7 ДНЕЙ", week_stats, 255),
        ("📈 30 ДНЕЙ", month_stats, 480)
    ]

    for title, stats, x in periods:
        draw.rounded_rectangle([x, 285, x + 210, 560], radius=14, fill=BG_CARD, outline=BORDER_CARD, width=1)

        draw.text((x + 20, 305), title, font=font_bold, fill=CYAN)

        # ROI
        p_roi_col = GREEN if stats["roi"] >= 0 else RED
        draw.text((x + 20, 350), "ROI:", font=font_regular, fill=TEXT_MUTED)
        draw.text((x + 95, 350), f"{stats['roi']:+,.1f}%", font=font_card_val, fill=p_roi_col)

        # Профит
        p_prof_col = GREEN if stats["profit"] >= 0 else RED
        draw.text((x + 20, 395), "Профит:", font=font_regular, fill=TEXT_MUTED)
        draw.text((x + 95, 395), f"{stats['profit']:+,.0f}", font=font_card_val, fill=p_prof_col)

        # Ставки
        draw.text((x + 20, 440), "Ставки:", font=font_regular, fill=TEXT_MUTED)
        draw.text((x + 95, 440), f"{stats['wins']} / {stats['losses']}", font=font_card_val, fill=TEXT_WHITE)

        # Винрейт
        draw.text((x + 20, 485), "Винрейт:", font=font_regular, fill=TEXT_MUTED)
        draw.text((x + 95, 485), f"{stats['winrate']}%", font=font_card_val, fill=TEXT_WHITE)

    # --- БЛОК 4: ПОДВАЛ / ВЕРИФИКАЦИЯ ---
    draw.line([(30, 770), (690, 770)], fill=(38, 45, 61, 255), width=1)
    draw.text((30, 785), "🛡️ TRUECAPPER PROTOCOL VERIFIED", font=font_bold, fill=GREEN)
    draw.text((30, 810), "Неизменяемый реестр live-прогнозов • t.me/capper_verifier_bot", font=font_regular, fill=TEXT_MUTED)

    # 5. Экспорт в буфер памяти
    output_buffer = io.BytesIO()
    image.convert("RGB").save(output_buffer, format="PNG", optimize=True)
    output_buffer.seek(0)
    return output_buffer