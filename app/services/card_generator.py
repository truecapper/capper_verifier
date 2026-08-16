import io
from PIL import Image, ImageDraw, ImageFont

def create_capper_card(
    capper_name: str,
    username: str,
    day_stats: dict,
    week_stats: dict,
    month_stats: dict,
    all_stats: dict
) -> io.BytesIO:
    # 1. Canvas setup (1080x1080 Dark Premium Theme)
    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(image)

    # 2. Fonts setup (Fallback to default if custom ttf isn't present)
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_subtitle = ImageFont.truetype("DejaVuSans.ttf", 26)
        font_card_val = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_card_lbl = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_card_val = ImageFont.load_default()
        font_card_lbl = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # 3. Top Header / Brand
    draw.rounded_rectangle([(60, 60), (1020, 200)], radius=24, fill="#1E293B", outline="#334155", width=2)
    
    # Avatar placeholder / Icon
    draw.rounded_rectangle([(90, 85), (175, 175)], radius=20, fill="#2563EB")
    draw.text((118, 105), capper_name[:1].upper(), fill="#FFFFFF", font=font_title)
    
    # Name & Username
    draw.text((200, 95), capper_name, fill="#FFFFFF", font=font_title)
    draw.text((200, 150), f"@{username} • Verified Live Capper", fill="#94A3B8", font=font_subtitle)

    # 4. Big Stat Banners: ALL-TIME (Центральный блок)
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

    # 5. Period Grid (Сегодня, 7 Дней, 30 Дней)
    periods = [
        ("СЕГОДНЯ", day_stats, 60),
        ("7 ДНЕЙ", week_stats, 390),
        ("30 ДНЕЙ", month_stats, 720)
    ]

    for label, stats, x_pos in periods:
        draw.rounded_rectangle([(x_pos, 450), (x_pos + 300, 880)], radius=20, fill="#1E293B", outline="#334155", width=2)
        
        # Period Header
        draw.text((x_pos + 30, 480), label, fill="#F59E0B", font=font_badge)
        
        # ROI
        p_roi_col = "#34D399" if stats["roi"] >= 0 else "#F87171"
        draw.text((x_pos + 30, 540), "ROI:", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 570), f"{stats['roi']:+,.1f}%", fill=p_roi_col, font=font_card_val)
        
        # Профит
        p_prof_col = "#34D399" if stats["profit"] >= 0 else "#F87171"
        draw.text((x_pos + 30, 640), "Профит:", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 670), f"{stats['profit']:+,.0f}", fill=p_prof_col, font=font_card_val)

        # Ставки
        draw.text((x_pos + 30, 740), "Ставки (В/П):", fill="#94A3B8", font=font_card_lbl)
        draw.text((x_pos + 30, 770), f"{stats['wins']} / {stats['losses']}", fill="#FFFFFF", font=font_card_val)
        
        # Винрейт
        draw.text((x_pos + 30, 825), f"Винрейт: {stats['winrate']}%", fill="#94A3B8", font=font_card_lbl)

    # 6. Bottom Security / Trust Footer
    draw.rounded_rectangle([(60, 910), (1020, 1020)], radius=20, fill="#0B132B", outline="#1E293B", width=1)
    draw.text((90, 940), "🔒 TRUECAPPER PROTOCOL VERIFIED", fill="#10B981", font=font_badge)
    draw.text((90, 975), "Неизменяемый реестр live-прогнозов • t.me/capper_verifier_bot", fill="#64748B", font=font_subtitle)

    # 7. Export to buffer
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="PNG", optimize=True)
    output_buffer.seek(0)
    return output_buffer