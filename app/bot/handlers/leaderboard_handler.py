import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database import AsyncSessionLocal
from app.services.leaderboard import get_top_cappers

router = Router()
logger = logging.getLogger(__name__)

def build_leaderboard_text(top_list: list, period_title: str) -> str:
    if not top_list:
        return (
            f"🏆 <b>ЗАЛ СЛАВЫ TRUECAPPER: {period_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>В базе пока нет зарегистрированных капперов или ставок.</i>\n\n"
            f"Отправь <code>/лайв</code> чтобы открыть рейтинг!"
        )
        
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines = [
        f"🏆 <b>РЕЙТИНГ КАППЕРОВ ({period_title})</b>",
        f"━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    for idx, capper in enumerate(top_list):
        medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
        handle = f"@{capper['username']}" if capper['username'] else capper['name']
        roi_sign = "+" if capper['roi'] > 0 else ""
        prof_sign = "+" if capper['profit'] > 0 else ""
        
        lines.append(
            f"{medal} <b>{handle}</b>\n"
            f"   📈 ROI: <b>{roi_sign}{capper['roi']}%</b> | Профит: <b>{prof_sign}{capper['profit']:,.0f}</b>\n"
            f"   🎯 Ставки: <b>{capper['wins']}В / {capper['losses']}П</b> ({capper['winrate']}% winrate)"
        )
        
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔒 <i>Рейтинг формируется автоматически без возможности ручных правок.</i>")
    return "\n".join(lines)

def get_leaderboard_keyboard(active_period: str = "all") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сегодня" + (" ✅" if active_period == "day" else ""), callback_data="top_day"),
            InlineKeyboardButton(text="7 Дней" + (" ✅" if active_period == "week" else ""), callback_data="top_week")
        ],
        [
            InlineKeyboardButton(text="30 Дней" + (" ✅" if active_period == "month" else ""), callback_data="top_month"),
            InlineKeyboardButton(text="Всё время" + (" ✅" if active_period == "all" else ""), callback_data="top_all")
        ],
        [
            InlineKeyboardButton(text="📊 Моя карточка", callback_data="refresh_stats")
        ]
    ])

@router.message(Command("top"))
async def cmd_leaderboard(message: types.Message):
    try:
        async with AsyncSessionLocal() as session:
            top_list = await get_top_cappers(session, period_days=None, min_bets=0, limit=10)
            text = build_leaderboard_text(top_list, "ВСЁ ВРЕМЯ")
            await message.answer(text, reply_markup=get_leaderboard_keyboard("all"), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /top command: {e}")
        await message.answer(f"❌ Ошибка вывода рейтинга: {str(e)}")

@router.callback_query(F.data.startswith("top_"))
async def callback_switch_period(callback: types.CallbackQuery):
    period = callback.data.replace("top_", "")
    
    period_map = {
        "day": (1, "СЕГОДНЯ"),
        "week": (7, "7 ДНЕЙ"),
        "month": (30, "30 ДНЕЙ"),
        "all": (None, "ВСЁ ВРЕМЯ")
    }
    
    days, title = period_map.get(period, (None, "ВСЁ ВРЕМЯ"))
    
    try:
        async with AsyncSessionLocal() as session:
            top_list = await get_top_cappers(session, period_days=days, min_bets=0, limit=10)
            text = build_leaderboard_text(top_list, title)
            await callback.message.edit_text(text, reply_markup=get_leaderboard_keyboard(period), parse_mode="HTML")
            await callback.answer()
    except Exception as e:
        logger.error(f"Error in top callback: {e}")
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)