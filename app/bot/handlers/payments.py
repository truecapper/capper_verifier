from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.config import settings

router = Router()

@router.message(Command("refill"))
@router.callback_query(F.data == "buy_refill")
async def send_refill_invoice(event: types.Message | types.CallbackQuery, bot: Bot):
    chat_id = event.chat.id if isinstance(event, types.Message) else event.message.chat.id
    
    prices = [LabeledPrice(label="Восстановление баланса (100,000 Coins)", amount=settings.REFILL_STARS_PRICE)]
    
    await bot.send_invoice(
        chat_id=chat_id,
        title="Восстановление игрового банка",
        description="Пополнение баланса верификатора на 100 000 коинов за 100 Telegram Stars (XTR)",
        payload=f"refill_balance_{chat_id}",
        provider_token="",  # Для Telegram Stars ВСЕГДА пустая строка
        currency="XTR",
        prices=prices,
        start_parameter="refill-bank"
    )
    if isinstance(event, types.CallbackQuery):
        await event.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if user:
            user.coin_balance += settings.STARTING_BALANCE
            await session.commit()
            
            await message.answer(
                f"🎉 <b>Оплата успешно принята!</b>\n\n"
                f"На ваш баланс зачислено <b>+100,000 коинов</b>.\n"
                f"Текущий банк: <b>{user.coin_balance:,.0f} коинов</b>.\n"
                f"Удачи в лайв-сессиях! 🚀",
                parse_mode="HTML"
            )