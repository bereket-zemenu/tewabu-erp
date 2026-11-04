"""
Tests for New Design features:
1. Gender and clothing item measurement mappings
2. Delivery date parsing
3. Audio chime WAV generation
4. 5-day delivery reminder queries
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
from core.calculations import calculate_design_financials
from handlers.new_design import parse_delivery_date, MEASUREMENT_LABELS
from services.audio_service import get_chime_bytes
import database.crud as crud

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

def test_measurement_labels():
    expected_keys = ["ቶፕ", "ትከሻ", "ደረት", "ወገብ", "እጅ", "ቁመት", "ዳሌ", "ጡት", "አንገት"]
    for k in expected_keys:
        assert k in MEASUREMENT_LABELS
        assert "en" in MEASUREMENT_LABELS[k]
        assert "am" in MEASUREMENT_LABELS[k]

def test_parse_delivery_date():
    today = date.today()
    
    # Days as string
    d7 = parse_delivery_date("7")
    assert d7 == today + timedelta(days=7)
    
    d15 = parse_delivery_date("15 ቀናት")
    assert d15 == today + timedelta(days=15)
    
    # ISO format
    iso_d = parse_delivery_date("2026-12-25")
    assert iso_d == date(2026, 12, 25)
    
    # Empty / invalid
    assert parse_delivery_date("") is None
    assert parse_delivery_date("invalid_text") is None

def test_audio_chime_generation():
    chime_bytes = get_chime_bytes()
    assert isinstance(chime_bytes, bytes)
    assert len(chime_bytes) > 1000
    # Check RIFF and WAVE headers
    assert chime_bytes[:4] == b"RIFF"
    assert chime_bytes[8:12] == b"WAVE"

@pytest.mark.asyncio
async def test_order_reminder_flow(async_session: AsyncSession):
    # Setup user and business
    user, business = await crud.get_or_create_user(
        async_session,
        telegram_id=987654321,
        username="reminder_tester",
    )
    
    calc = calculate_design_financials(expenses=[Decimal("200.00")], target_margin=Decimal("0.25"))
    design = await crud.create_design(
        session=async_session,
        business_id=business.id,
        name="የወንድ ጃኬት",
        calc_result=calc,
        expenses_list=[{"category_key": "menen", "category_name": "መነን", "amount": Decimal("200.00")}],
        gender="MALE",
        clothing_item="ጃኬት",
        measurements_json='{"ቶፕ": "45", "ትከሻ": "42", "ደረት": "98", "ወገብ": "84", "እጅ": "62"}',
    )
    assert design.id is not None
    assert design.gender == "MALE"
    assert design.clothing_item == "ጃኬት"

    # Create order due in 3 days
    due_in_3d = date.today() + timedelta(days=3)
    order = await crud.create_order_from_design(
        session=async_session,
        business_id=business.id,
        design_id=design.id,
        customer_name="አበበ ተፈራ",
        agreed_price=Decimal("400.00"),
        due_date=due_in_3d,
    )
    assert order.id is not None
    assert order.reminder_5d_sent is False

    # Check that reminder service queries this order
    due_orders = await crud.get_orders_due_for_reminder(async_session, days_ahead=5)
    matched = [o for o, tg_id in due_orders if o.id == order.id]
    assert len(matched) == 1
    assert matched[0].customer_name == "አበበ ተፈራ"

    # Mark reminder sent
    await crud.mark_order_reminder_sent(async_session, order.id)
    await async_session.refresh(order)
    assert order.reminder_5d_sent is True

    # Should not appear again
    due_orders_after = await crud.get_orders_due_for_reminder(async_session, days_ahead=5)
    matched_after = [o for o, tg_id in due_orders_after if o.id == order.id]
    assert len(matched_after) == 0
