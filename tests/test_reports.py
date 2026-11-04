"""
Unit and integration tests for Reports and Chart Generation.
"""

from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
import database.crud as crud
from core.calculations import calculate_design_financials
from services.chart_service import generate_expenses_pie_chart, generate_financial_bar_chart
from services.report_service import get_period_summary, export_designs_csv

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def async_session():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    await test_engine.dispose()

def test_generate_expenses_pie_chart():
    expenses = [
        {"category_key": "menen_gever", "amount": 500},
        {"category_key": "thread", "amount": 50},
        {"category_key": "embroidery", "amount": 300},
        {"category_key": "sewing", "amount": 200},
    ]
    png_bytes = generate_expenses_pie_chart(expenses)
    assert png_bytes is not None
    # Verify PNG header bytes: \x89PNG\r\n\x1a\n
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

def test_generate_financial_bar_chart():
    png_bytes = generate_financial_bar_chart(
        revenue=Decimal("15000.00"),
        costs=Decimal("9500.00"),
        profit=Decimal("5500.00"),
    )
    assert png_bytes is not None
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

@pytest.mark.asyncio
async def test_period_summary_and_csv_export(async_session: AsyncSession):
    _, bus = await crud.get_or_create_user(async_session, 888999, "chaltu", "Chaltu")

    calc = calculate_design_financials([Decimal("1200.00")], target_margin=Decimal("0.25"), actual_selling_price=Decimal("1600.00"))
    await crud.create_design(
        session=async_session,
        business_id=bus.id,
        name="Habesha Kemis Special",
        calc_result=calc,
        expenses_list=[{"category_key": "menen_gever", "category_name": "መነን", "amount": Decimal("1200.00")}],
    )

    summary = await get_period_summary(async_session, bus.id, "monthly")
    assert summary["designs_count"] == 1
    assert summary["total_expenses"] == Decimal("1200.00")

    csv_data = await export_designs_csv(async_session, bus.id)
    assert b"Habesha Kemis Special" in csv_data
    assert b"1200.00" in csv_data
