import re
from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, Bet, BetStatus
from app.config import settings

router = Router()

async def get_or_create_user(telegram_user: types.User, session) -> User:
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            full_name=telegram_user.full_name,
            coin_balance=settings.STARTING_BALANCE
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(message.from_user, session)
        await message.answer(
            f"⚡ <b>Верификатор Live-ставок готов к работе!</b>\n\n"
            f"👤 <b>Каппер:</b> {user.full_name}\n"
            f"💰 <b>Твой баланс:</b> {user.coin_balance:,.0f} коинов\n\n"
            f"📌 <b>Формат быстрой ставки:</b>\n"
            f"<code>/лайв Матч Исход Кэф Сумма</code>\n"
            f"Пример: <code>/лайв Реал-Барса тб 2.5 1.88 3500</code>\n\n"
            f"📊 /stats — Карточка статистики каппера\n"
            f"🔄 /refill — Восстановить банк до 100k коинов (100 Stars)",
            parse_mode="HTML"
        )

@router.message(F.text.regexp(r"^/(лайв|live)\s+(.+)\s+([0-9]+\.?[0-9]*)\s+([0-9]+)$"))
async def handle_live_bet(message: types.Message):
    # Парсинг команды: /лайв Реал-Барса тб 2.5 1.88 3500
    text = message.text.replace("/live", "/лайв").strip()
    parts = text.split()
    
    if len(parts) < 5:
        await message.answer(
            "⚠️ <b>Неверный формат!</b>\nИспользуйте: <code>/лайв Матч Рынок Коэффициент Сумма</code>\n"
            "Пример: <code>/лайв Реал-Барселона ТБ 2.5 1.88 3500</code>",
            parse_mode="HTML"
        )
        return

    try:
        stake = float(parts[-1])
        odds = float(parts[-2])
        match_and_market = parts[1:-2]
        
        # Разделяем матч и рынок
        match_title = match_and_market[0]
        market = " ".join(match_and_market[1:]) if len(match_and_market) > 1 else "Основной исход"
        
        if odds <= 1.01:
            await message.answer("⚠️ Коэффициент должен быть больше 1.01")
            return
            
        if stake <= 0:
            await message.answer("⚠️ Сумма ставки должна быть больше 0")
            return

        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(message.from_user, session)
            
            if user.coin_balance < stake:
                await message.answer(
                    f"❌ <b>Недостаточно коинов!</b>\n"
                    f"Текущий баланс: <b>{user.coin_balance:,.0f}</b>\n"
                    f"Запрошено: <b>{stake:,.0f}</b>\n\n"
                    f"Используйте /refill для пополнения банка.",
                    parse_mode="HTML"
                )
                return

            # Списываем баланс и создаем ставку
            user.coin_balance -= stake
            
            new_bet = Bet(
                user_id=user.id,
                match_title=match_title,
                market=market,
                odds=odds,
                stake=stake,
                status=BetStatus.PENDING
            )
            session.add(new_bet)
            await session.commit()
            await session.refresh(new_bet)

            # Клавиатура быстрого расчета для верификатора / оператора
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ Win", callback_data=f"settle_{new_bet.id}_win"),
                    types.InlineKeyboardButton(text="❌ Lose", callback_data=f"settle_{new_bet.id}_lose"),
                    types.InlineKeyboardButton(text="↩️ Возврат", callback_data=f"settle_{new_bet.id}_refund")
                ]
            ])

            await message.answer(
                f"🔒 <b>СТАВКА ЗАФИКСИРОВАНА #{new_bet.id}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⚽ <b>Матч:</b> {new_bet.match_title}\n"
                f"🎯 <b>Рынок:</b> {new_bet.market}\n"
                f"📈 <b>Коэффициент:</b> {new_bet.odds}\n"
                f"💵 <b>Сумма:</b> {new_bet.stake:,.0f} коинов\n"
                f"Статус: ⏳ <b>В игре (PENDING)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Остаток банка: <b>{user.coin_balance:,.0f}</b> коинов",
                reply_markup=kb,
                parse_mode="HTML"
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка обработки: {str(e)}")

# Расчет исхода ставки (Win/Lose/Refund)
@router.callback_query(F.data.startswith("settle_"))
async def handle_settlement(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    bet_id = int(parts[1])
    outcome = parts[2]
    
    async with AsyncSessionLocal() as session:
        stmt = select(Bet).where(Bet.id == bet_id)
        res = await session.execute(stmt)
        bet = res.scalar_one_or_none()
        
        if not bet or bet.status != BetStatus.PENDING:
            await callback.answer("Ставка уже рассчитана или не найдена!", show_alert=True)
            return

        user_stmt = select(User).where(User.id == bet.user_id)
        u_res = await session.execute(user_stmt)
        user = u_res.scalar_one()

        if outcome == "win":
            bet.status = BetStatus.WIN
            bet.profit = (bet.stake * bet.odds) - bet.stake
            user.coin_balance += (bet.stake * bet.odds)
            status_text = f"✅ <b>ВЫИГРЫШ (+{bet.profit:,.0f} коинов)</b>"
        elif outcome == "lose":
            bet.status = BetStatus.LOSE
            bet.profit = -bet.stake
            status_text = f"❌ <b>ПРОИГРЫШ (-{bet.stake:,.0f} коинов)</b>"
        else:
            bet.status = BetStatus.REFUND
            bet.profit = 0.0
            user.coin_balance += bet.stake
            status_text = "↩️ <b>ВОЗВРАТ</b>"

        await session.commit()
        
        await callback.message.edit_text(
            f"📋 <b>РАСЧЕТ СТАВКИ #{bet.id}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ <b>Матч:</b> {bet.match_title}\n"
            f"🎯 <b>Рынок:</b> {bet.market} (@{bet.odds})\n"
            f"💵 <b>Сумма:</b> {bet.stake:,.0f}\n"
            f"Итог: {status_text}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Новый баланс каппера: <b>{user.coin_balance:,.0f}</b>",
            parse_mode="HTML"
        )
        await callback.answer("Ставка рассчитана!")