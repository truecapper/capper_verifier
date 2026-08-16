import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "DejaVuSans-Bold.ttf"

def get_loaded_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Загружает TTF шрифт с полной поддержкой кириллицы и спецсимволов."""
    try:
        if os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, size)
        # Системные шрифты Linux/Debian на Render
        for sys_font in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]:
            if os.path.exists(sys_font):
                return ImageFont.truetype(sys_font, size)
    except Exception:
        pass
    return ImageFont.load_default()

def format_clean_chat_name(full_name: str) -> str:
    """
    Формирует оригинальное экранное имя каппера из чата.
    Фильтрует непечатаемые управляющие байты, сохраняя буквы, знаки и читаемый текст.
    """
    # Сохраняем все кириллические, латинские буквы, цифры и знаки препинания
    clean = "".join(c for c in full_name if ord(c) < 0x10000 and (c.isalnum() or c in " _-—–.,!?'\"()[]{}#@*~/\\+")).strip()
    return clean if clean else full_name.strip()

def create_capper_card(
    capper_name: str,
    username: str,
    day_stats: dict,
    week_stats: dict,
    month_stats: dict,
    all_stats: dict
) -> io.BytesIO:
    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(image)

    # 1. Шрифты
    font_title = get_loaded_font(46, bold=True)
    font_subtitle = get_loaded_font(24, bold=False)
    font_card_val = get_loaded_font(36, bold=True)
    font_card_lbl = get_loaded_font(20, bold=False)
    font_badge = get_loaded_font(22, bold=True)

    # 2. Имя каппера из чата
    display_chat_name = format_clean_chat_name(capper_name)
    if not display_chat_name:
        display_chat_name = username or "Каппер"

    # Буква для плашки аватара
    first_char = "C"
    for ch in display_chat_name:
        if ch.isalnum():
            first_char = ch.upper()
            break

    # 3. Шапка профиля
    draw.rounded_rectangle([(60, 60), (1020, 200)], radius=24, fill="#1E293B", outline="#334155", width=2)
    
    # Аватар-бейдж
    draw.rounded_rectangle([(90, 85), (175, 175)], radius=20, fill="#2563EB")
    draw.text((118, 102), first_char, fill="#FFFFFF", font=font_title)
    
    # Отображаемое имя каппера (как в чате)
    draw.text((200, 95), display_chat_name, fill="#FFFFFF", font=font_title)
    
    # Дополнительная плашка (юзернейм и статус)
    user_handle = f"@{username} • " if username else ""
    draw.text((200, 150), f"{user_handle}Verified Live Capper", fill="#38BDF8", font=font_subtitle)

    # 4. Центральный блок: ALL-TIME
    draw.rounded_rectangle([(60, 230), (1020, 420)], radius=24, fill="#131D31", outline="#3B82F6", width=2)
    draw.text((90, 255), "ОБЩАЯ СТАТИСТИКА (ALL-TIME)", fill="#60A5FA", font=font_badge)
    
    roi_color = "#34D399" if all_stats["roi"] >= 0 else "#F87171"
    draw.text((90, 310), f"{all_stats['roi']:+,.1f}%", fill=roi_color, font=font_title)
    draw.text((90, 370), "ROI Верификатора", fill="#94A3B8", font=font_card_lbl)

    draw.text((450, 310), f"{all_stats['winrate']}%", fill="#FFFFFF", font=font_title)
    draw.text((450, 370), f"Винрейт ({all_stats['wins']}В / {all_stats['losses']}П)", fill="#94A3B8", font=font_card_lbl)

    profit_color = "#34D399" if all_stats["profit"] >= 0 else "#F87171"
    draw.text((780, 310), f"{all_stats['profit']:+,.0f}", fill=profit_color, font=font_title)
    draw.text((780, 370), "Профит (коины)", fill="#94A3B8", font=font_card_lbl)

    # 5. Периоды: Сегодня, 7 Дней, 30 Дней
    periods = [
        ("СЕГОДНЯ", day_stats, 60),
        ("7 ДНЕЙ", week_stats, 390),
        ("30 ДНЕЙ", month_stats, 720)
    ]

    for label, stats, x_pos in periods:
        draw.rounded_rectangle([(x_pos, 450), (x_pos + 300, 880)], radius=20, fill="#1E293B", outline="#334155", width=2)
        
        draw.text((x_pos + 30, 480), label, fill="#F59E0B", font=font_badge)
        
        p_roi_col = "#34D399" if stats["roi"] >= 0 else "#F87171"
        draw.text((x_pos + 30, 540), "ROI:", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 570), f"{stats['roi']:+,.1f}%", fill=p_roi_col, font=font_card_val)
        
        p_prof_col = "#34D399" if stats["profit"] >= 0 else "#F87171"
        draw.text((x_pos + 30, 640), "Профит:", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 670), f"{stats['profit']:+,.0f}", fill=p_prof_col, font=font_card_val)

        draw.text((x_pos + 30, 740), "Ставки (В/П):", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 770), f"{stats['wins']} / {stats['losses']}", fill="#FFFFFF", font=font_card_val)
        
        draw.text((x_pos + 30, 825), f"Винрейт: {stats['winrate']}%", fill="#94A3B8", font=font_card_lbl)

    # 6. Подвал верификатора
    draw.rounded_rectangle([(60, 910), (1020, 1020)], radius=20, fill="#0B132B", outline="#1E293B", width=1)
    draw.text((90, 940), "TRUECAPPER PROTOCOL VERIFIED", fill="#10B981", font=font_badge)
    draw.text((90, 975), "Неизменяемый реестр live-прогнозов • t.me/capper_verifier_bot", fill="#64748B", font=font_subtitle)

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="PNG", optimize=True)
    output_buffer.seek(0)
    return output_buffer