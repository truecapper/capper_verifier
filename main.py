import asyncio
import logging
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from app.config import settings
from app.database import init_db
from app.bot.handlers.bet_tracker import router as bet_router
from app.bot.handlers.stats_card import router as stats_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.leaderboard_handler import router as leaderboard_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Регистрация всех роутеров
dp.include_router(bet_router)
dp.include_router(stats_router)
dp.include_router(payments_router)
dp.include_router(leaderboard_router)

async def keep_awake():
    """Фоновый пинг каждые 10 минут, чтобы Render не засыпал."""
    await asyncio.sleep(30)
    base_url = settings.RENDER_EXTERNAL_URL or "https://liga-dena.onrender.com"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(f"{base_url}/health", timeout=10.0)
            except Exception as e:
                logger.warning(f"Keep-alive ping error: {e}")
            await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Инициализируем таблицы БД
    await init_db()
    
    # 2. Определяем URL вебхука
    base_url = settings.RENDER_EXTERNAL_URL if settings.RENDER_EXTERNAL_URL else "https://liga-dena.onrender.com"
    webhook_url = f"{base_url.rstrip('/')}/webhook"
    
    try:
        # Сбрасываем старый и жестко ставим актуальный вебхук
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "pre_checkout_query"]
        )
        logger.info(f"✅ Webhook successfully connected: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Failed to set Telegram webhook: {e}")

    # Запускаем фоновый пинг
    asyncio.create_task(keep_awake())
    
    yield
    
    try:
        await bot.session.close()
    except Exception:
        pass

app = FastAPI(title="Live Bet Verifier API", lifespan=lifespan)

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "alive", "service": "Live Bet Verifier"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT)