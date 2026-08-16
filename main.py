import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from app.config import settings
from app.database import init_db
from app.bot.handlers.bet_tracker import router as bet_router
from app.bot.handlers.stats_card import router as stats_router
from app.bot.handlers.payments import router as payments_router

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

dp.include_router(bet_router)
dp.include_router(stats_router)
dp.include_router(payments_router)

# Фоновый пинг, чтобы бесплатный Render не засыпал во время работы
async def keep_awake():
    if not settings.RENDER_EXTERNAL_URL:
        return
    await asyncio.sleep(60)
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(f"{settings.RENDER_EXTERNAL_URL}/health")
            except Exception:
                pass
            await asyncio.sleep(600)  # каждые 10 минут

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    if settings.RENDER_EXTERNAL_URL:
        webhook_url = f"{settings.RENDER_EXTERNAL_URL}/webhook"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        asyncio.create_task(keep_awake())
    else:
        # Режим локального тестирования
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot))
        
    yield
    await bot.session.close()

app = FastAPI(title="Live Bet Verifier API", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "alive", "service": "Live Bet Verifier"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT)