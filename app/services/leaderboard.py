from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Bet, BetStatus

async def get_top_cappers(session: AsyncSession, period_days: int = None, min_bets: int = 0, limit: int = 10):
    """
    Формирует ТОП капперов за период.
    Отказоустойчиво обрабатывает любые пустые значения и новые аккаунты.
    """
    now = datetime.now(timezone.utc)
    
    users_stmt = select(User)
    users_res = await session.execute(users_stmt)
    users = users_res.scalars().all()
    
    leaderboard = []
    
    for user in users:
        query = select(Bet).where(Bet.user_id == user.id)
        
        if period_days is not None:
            if period_days == 1:
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_time = now - timedelta(days=period_days)
            query = query.where(Bet.created_at >= start_time)
            
        bets_res = await session.execute(query)
        bets = bets_res.scalars().all()
        
        # Рассчитанные ставки
        settled_bets = [b for b in bets if b.status in [BetStatus.WIN, BetStatus.LOSE, BetStatus.REFUND]]
        total_settled = len(settled_bets)
        
        # Если задан фильтр минимального числа ставок и у пользователя меньше — пропускаем
        if min_bets > 0 and total_settled < min_bets:
            continue
            
        wins = sum(1 for b in settled_bets if b.status == BetStatus.WIN)
        losses = sum(1 for b in settled_bets if b.status == BetStatus.LOSE)
        turnover = sum((b.stake or 0.0) for b in settled_bets)
        profit = sum((b.profit or 0.0) for b in settled_bets)
        
        decided = wins + losses
        winrate = (wins / decided * 100) if decided > 0 else 0.0
        roi = (profit / turnover * 100) if turnover > 0 else 0.0
        
        name = user.full_name or f"@{user.username}" if user.username else f"Каппер #{user.id}"
        
        leaderboard.append({
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username or "",
            "name": name,
            "total_bets": len(bets),
            "settled_bets": total_settled,
            "wins": wins,
            "losses": losses,
            "winrate": round(winrate, 1),
            "roi": round(roi, 1),
            "profit": round(profit, 0),
            "balance": round(user.coin_balance or 100000.0, 0)
        })
        
    # Сортируем: сначала по ROI, затем по профиту
    leaderboard.sort(key=lambda x: (x["roi"], x["profit"], x["wins"]), reverse=True)
    return leaderboard[:limit]