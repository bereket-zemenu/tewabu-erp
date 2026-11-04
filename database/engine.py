"""
Database engine and async session provider for Tewabu ERP.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from config.settings import settings
from database.models import Base

# Ensure SQLite engine supports concurrent async operations properly
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def init_db() -> None:
    """Initialize database schema, creating tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Ensure is_verified, failed_attempts, and locked_until columns exist
        if "sqlite" in settings.DATABASE_URL:
            def check_and_add_column(sync_conn):
                try:
                    res = sync_conn.execute(text("PRAGMA table_info(users)")).fetchall()
                    col_names = [r[1] for r in res]
                    if "is_verified" not in col_names:
                        sync_conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0 NOT NULL"))
                    if "failed_attempts" not in col_names:
                        sync_conn.execute(text("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0 NOT NULL"))
                    if "locked_until" not in col_names:
                        sync_conn.execute(text("ALTER TABLE users ADD COLUMN locked_until DATETIME NULL"))

                    # Ensure image_file_id, gender, clothing_item, measurements_json exist on designs table
                    res_des = sync_conn.execute(text("PRAGMA table_info(designs)")).fetchall()
                    des_cols = [r[1] for r in res_des]
                    if "image_file_id" not in des_cols:
                        sync_conn.execute(text("ALTER TABLE designs ADD COLUMN image_file_id VARCHAR(256) NULL"))
                    if "gender" not in des_cols:
                        sync_conn.execute(text("ALTER TABLE designs ADD COLUMN gender VARCHAR(16) NULL"))
                    if "clothing_item" not in des_cols:
                        sync_conn.execute(text("ALTER TABLE designs ADD COLUMN clothing_item VARCHAR(64) NULL"))
                    if "measurements_json" not in des_cols:
                        sync_conn.execute(text("ALTER TABLE designs ADD COLUMN measurements_json TEXT NULL"))

                    # Ensure reminder_5d_sent exists on orders table
                    res_ord = sync_conn.execute(text("PRAGMA table_info(orders)")).fetchall()
                    ord_cols = [r[1] for r in res_ord]
                    if "reminder_5d_sent" not in ord_cols:
                        sync_conn.execute(text("ALTER TABLE orders ADD COLUMN reminder_5d_sent BOOLEAN DEFAULT 0 NOT NULL"))
                except Exception:
                    pass

            await conn.run_sync(check_and_add_column)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper to yield async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
