from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    DATABASE_URL: str = Field(default=f"sqlite+aiosqlite:///{BASE_DIR / 'tewabu_erp.db'}")
    ACCESS_PASSWORD: str = Field(default="122337", description="Access password required to unlock bot")
    DEFAULT_CURRENCY: str = Field(default="ETB")
    DEFAULT_PROFIT_MARGIN: Decimal = Field(default=Decimal("0.25"))
    DEFAULT_LANGUAGE: str = Field(default="am")
    LOG_LEVEL: str = Field(default="INFO")
    BACKUP_DIR: Path = Field(default=BASE_DIR / "backups")
    EXPORTS_DIR: Path = Field(default=BASE_DIR / "exports")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
