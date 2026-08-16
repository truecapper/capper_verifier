from aiogram import Router, types
from aiogram.filters import Command
from app.database import AsyncSessionLocal
from app.bot.handlers.bet_tracker import get_or_create_user
from app.services.stats_engine import calculate_capper_metrics

router = Router()

@router.message(Command("stats"))
async def cmd_capper_stats(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(message.from_user, session)
        
        day_stats = await calculate_capper_metrics(user.id, session, period_days=1)
        week_stats = await calculate_capper_metrics(user.id, session, period_days=7)
        month_stats = await calculate_capper_metrics(user.id, session, period_days=30)
        year_stats = await calculate_capper_metrics(user.id, session, period_days=365)
        all_stats = await calculate_capper_metrics(user.id, session, period_days=None)
        
        card_text = (
            f"🏆 <b>КАРТОЧКА ВЕРИФИЦИРОВАННОГО КАППЕРА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Каппер:</b> {user.full_name} (@{user.username or 'capper'})\n"
            f"💰 <b>Банк:</b> <code>{user.coin_balance:,.0f} coins</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>СЕГОДНЯ:</b>\n"
            f"• Ставок: {day_stats['total']} | В/П: {day_stats['wins']}/{day_stats['losses']}\n"
            f"• Профит: <b>{day_stats['profit']:+,.0f}</b> | ROI: <b>{day_stats['roi']}%</b>\n\n"
            f"🗓 <b>ЗА 7 ДНЕЙ:</b>\n"
            f"• Ставок: {week_stats['total']} | Winrate: <b>{week_stats['winrate']}%</b>\n"
            f"• Профит: <b>{week_stats['profit']:+,.0f}</b> | ROI: <b>{week_stats['roi']}%</b>\n\n"
            f"📈 <b>ЗА 30 ДНЕЙ:</b>\n"
            f"• Ставок: {month_stats['total']} | Winrate: <b>{month_stats['winrate']}%</b>\n"
            f"• Профит: <b>{month_stats['profit']:+,.0f}</b> | ROI: <b>{month_stats['roi']}%</b>\n\n"
            f"👑 <b>ЗА ВСЁ ВРЕМЯ (All-Time):</b>\n"
            f"• Всего ставок: <b>{all_stats['total']}</b>\n"
            f"• Общий ROI: <b>{all_stats['roi']}%</b>\n"
            f"• Чистый профит: <b>{all_stats['profit']:+,.0f} коинов</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 <i>Верифицировано автоматическим протоколом. Ставки неизменяемы.</i>"
        )
        
        bot_info = await message.bot.get_me()
        share_url = f"https://t.me/share/url?url=https://t.me/{bot_info.username}?start=capper_{user.telegram_id}&text=Моя+статистика+в+Live-Верификаторе+ставок!"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📢 Поделиться карточкой", url=share_url)],
            [types.InlineKeyboardButton(text="🔄 Обновить банк (+100k)", callback_data="buy_refill")]
        ])
        
        await message.answer(card_text, reply_markup=kb, parse_mode="HTML")