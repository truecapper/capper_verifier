from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Bet, BetStatus

async def calculate_capper_metrics(user_id: int, session: AsyncSession, period_days: int = None):
    now = datetime.now(timezone.utc)
    query = select(Bet).where(
        Bet.user_id == user_id,
        Bet.status.in_([BetStatus.WIN, BetStatus.LOSE, BetStatus.REFUND])
    )
    
    if period_days is not None:
        if period_days == 1:
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_time = now - timedelta(days=period_days)
        query = query.where(Bet.created_at >= start_time)
        
    res = await session.execute(query)
    bets = res.scalars().all()
    
    total_bets = len(bets)
    if total_bets == 0:
        return {"total": 0, "wins": 0, "losses": 0, "winrate": 0.0, "roi": 0.0, "profit": 0.0, "turnover": 0.0}
        
    wins = sum(1 for b in bets if b.status == BetStatus.WIN)
    losses = sum(1 for b in bets if b.status == BetStatus.LOSE)
    turnover = sum(b.stake for b in bets)
    total_profit = sum(b.profit for b in bets)
    
    decided_bets = wins + losses
    winrate = (wins / decided_bets * 100) if decided_bets > 0 else 0.0
    roi = (total_profit / turnover * 100) if turnover > 0 else 0.0
    
    return {
        "total": total_bets,
        "wins": wins,
        "losses": losses,
        "winrate": round(winrate, 1),
        "roi": round(roi, 2),
        "profit": round(total_profit, 2),
        "turnover": round(turnover, 2)
    }