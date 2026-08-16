from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from app.database import AsyncSessionLocal
from app.bot.handlers.bet_tracker import get_or_create_user
from app.services.stats_engine import calculate_capper_metrics
from app.services.card_generator import create_capper_card

router = Router()

@router.message(Command("stats"))
@router.callback_query(F.data == "refresh_stats")
async def cmd_capper_stats(event: types.Message | types.CallbackQuery):
    message = event if isinstance(event, types.Message) else event.message
    telegram_user = event.from_user
    
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(telegram_user, session)
        
        # Получаем данные за все периоды
        day_stats = await calculate_capper_metrics(user.id, session, period_days=1)
        week_stats = await calculate_capper_metrics(user.id, session, period_days=7)
        month_stats = await calculate_capper_metrics(user.id, session, period_days=30)
        all_stats = await calculate_capper_metrics(user.id, session, period_days=None)
        
        # Генерируем PNG прямо в памяти
        image_bytes = create_capper_card(
            capper_name=user.full_name,
            username=user.username or f"id_{user.telegram_id}",
            day_stats=day_stats,
            week_stats=week_stats,
            month_stats=month_stats,
            all_stats=all_stats
        )
        
        photo_file = BufferedInputFile(image_bytes.read(), filename=f"stats_{user.telegram_id}.png")
        
        caption_text = (
            f"📊 <b>Официальная карточка каппера</b>\n\n"
            f"👤 <b>Каппер:</b> {user.full_name} (@{user.username or 'capper'})\n"
            f"💰 <b>Текущий банк:</b> <code>{user.coin_balance:,.0f} coins</code>\n"
            f"👑 <b>All-Time ROI:</b> <b>{all_stats['roi']:+,.1f}%</b>\n\n"
            f"<i>Сохрани или перешли картинку в свой канал для подтверждения честной статистики!</i>"
        )
        
        bot_info = await message.bot.get_me()
        share_url = f"https://t.me/share/url?url=https://t.me/{bot_info.username}?start=capper_{user.telegram_id}&text=Моя+верифицированная+статистика+live-ставок!"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Поделиться профилем", url=share_url)],
            [InlineKeyboardButton(text="🔄 Обновить баланс (+100k)", callback_data="buy_refill")]
        ])
        
        if isinstance(event, types.CallbackQuery):
            await event.answer()
            
        await message.answer_photo(photo=photo_file, caption=caption_text, reply_markup=kb, parse_mode="HTML")