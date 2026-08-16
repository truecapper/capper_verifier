from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./verifier.db"  # Для быстрого старта или postgresql+asyncpg://...
    RENDER_EXTERNAL_URL: str = ""  # URL вида https://your-app.onrender.com
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    STARTING_BALANCE: float = 100000.0
    REFILL_STARS_PRICE: int = 100  # 100 TG Stars
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()