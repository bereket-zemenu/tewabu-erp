"""
Tests for Async Database CRUD and strict tenant isolation in Tewabu ERP.
"""

from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
import database.crud as crud
from core.calculations import calculate_design_financials
from core.constants import OrderStatus

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

@pytest.mark.asyncio
async def test_user_and_business_creation(async_session: AsyncSession):
    user, business = await crud.get_or_create_user(
        session=async_session,
        telegram_id=111222333,
        username="abebe_tailor",
        full_name="Abebe Bikila",
        language="am",
    )
    assert user.telegram_id == 111222333
    assert user.language == "am"
    assert user.is_verified is False
    assert business.user_id == user.id
    assert business.currency == "ETB"
    assert business.default_profit_margin == Decimal("0.25")

    # Verify lifetime authentication
    await crud.verify_user(async_session, user.telegram_id)
    await async_session.refresh(user)
    assert user.is_verified is True

@pytest.mark.asyncio
async def test_create_design_and_expenses(async_session: AsyncSession):
    user, business = await crud.get_or_create_user(
        session=async_session,
        telegram_id=222333444,
        username="almaz",
        full_name="Almaz",
    )

    expenses_list = [
        {"category_key": "menen_gever", "category_name": "መነን & ገቨር", "amount": Decimal("600.00")},
        {"category_key": "thread", "category_name": "ክር", "amount": Decimal("80.00")},
        {"category_key": "embroidery", "category_name": "ጠላፊ", "amount": Decimal("350.00")},
        {"category_key": "sewing", "category_name": "ሰፊ", "amount": Decimal("250.00")},
        {"category_key": "designer", "category_name": "ዲዛይነር", "amount": Decimal("100.00")},
        {"category_key": "related_expenses", "category_name": "ተያያዥ ወጪ", "amount": Decimal("70.00")},
    ]

    calc = calculate_design_financials(
        expenses=[e["amount"] for e in expenses_list],
        target_margin=Decimal("0.25"),
        actual_selling_price=Decimal("2000.00"),
    )

    design = await crud.create_design(
        session=async_session,
        business_id=business.id,
        name="የሀበሻ የሰርግ ቀሚስ",
        calc_result=calc,
        expenses_list=expenses_list,
        customer_name="ወ/ሮ ትዕግስት",
    )

    assert design.id is not None
    assert design.total_cost == Decimal("1450.00")
    assert design.break_even_price == Decimal("1450.00")
    # Optimal: 1450 / 0.75 = 1933.33
    assert design.optimal_price == Decimal("1933.33")
    assert design.actual_profit == Decimal("550.00")
    assert design.status == "ABOVE_TARGET"

    # Verify retrieval
    retrieved = await crud.get_design(async_session, design.id, business.id)
    assert retrieved is not None
    assert len(retrieved.expenses) == 6

@pytest.mark.asyncio
async def test_business_data_isolation(async_session: AsyncSession):
    """Verify that User A cannot see User B's designs or financial data."""
    _, bus_a = await crud.get_or_create_user(async_session, 1001, "owner_a", "Owner A")
    _, bus_b = await crud.get_or_create_user(async_session, 2002, "owner_b", "Owner B")

    calc = calculate_design_financials([Decimal("500")], target_margin=Decimal("0.20"))
    design_a = await crud.create_design(
        session=async_session,
        business_id=bus_a.id,
        name="Business A Design",
        calc_result=calc,
        expenses_list=[{"category_key": "thread", "category_name": "ክር", "amount": Decimal("500")}],
    )

    # Owner B attempts to access Owner A's design
    forbidden_fetch = await crud.get_design(async_session, design_a.id, business_id=bus_b.id)
    assert forbidden_fetch is None

    # Listing designs for Owner B returns empty
    designs_b, total_b = await crud.list_designs(async_session, business_id=bus_b.id)
    assert total_b == 0
    assert len(designs_b) == 0

@pytest.mark.asyncio
async def test_order_management_and_revenue_isolation(async_session: AsyncSession):
    """
    Test requirement:
    'Do not count pending orders as completed revenue.'
    """
    _, bus = await crud.get_or_create_user(async_session, 3003, "chala", "Chala")

    calc = calculate_design_financials([Decimal("1000.00")], target_margin=Decimal("0.20"))
    design = await crud.create_design(
        session=async_session,
        business_id=bus.id,
        name="Suit 1",
        calc_result=calc,
        expenses_list=[{"category_key": "menen_gever", "category_name": "ጨርቅ", "amount": Decimal("1000.00")}],
    )

    # 1. Create a Pending order
    order_pending = await crud.create_order_from_design(
        session=async_session,
        business_id=bus.id,
        design_id=design.id,
        customer_name="Dawit",
        agreed_price=Decimal("1500.00"),
        advance_payment=Decimal("500.00"),
    )
    assert order_pending.status == OrderStatus.PENDING.value

    # Dashboard check: pending order should NOT be in completed_revenue!
    metrics = await crud.get_dashboard_metrics(async_session, bus.id)
    assert metrics["completed_revenue"] == Decimal("0.00")
    assert metrics["realized_profit"] == Decimal("0.00")
    # Expected profit pending: 1500 - 1000 = 500
    assert metrics["expected_profit_pending"] == Decimal("500.00")
    assert metrics["pending_orders_count"] == 1

    # 2. Mark order as COMPLETED
    await crud.update_order_status(
        session=async_session,
        order_id=order_pending.id,
        business_id=bus.id,
        new_status=OrderStatus.COMPLETED.value,
        record_final_payment=True,
    )

    metrics_after = await crud.get_dashboard_metrics(async_session, bus.id)
    assert metrics_after["completed_revenue"] == Decimal("1500.00")
    assert metrics_after["realized_profit"] == Decimal("500.00")
    assert metrics_after["pending_orders_count"] == 0
    assert metrics_after["expected_profit_pending"] == Decimal("0.00")

@pytest.mark.asyncio
async def test_password_lockout_mechanism(async_session: AsyncSession):
    user, _ = await crud.get_or_create_user(async_session, 999111, "test_lock", "Lock User")
    assert user.is_verified is False
    assert user.failed_attempts == 0
    assert user.locked_until is None

    # Attempt 1
    attempts, lock = await crud.record_failed_password_attempt(async_session, user)
    assert attempts == 1
    assert lock is None
    is_locked, _ = await crud.check_user_lock(async_session, user)
    assert is_locked is False

    # Attempt 2
    attempts, lock = await crud.record_failed_password_attempt(async_session, user)
    assert attempts == 2
    assert lock is None
    is_locked, _ = await crud.check_user_lock(async_session, user)
    assert is_locked is False

    # Attempt 3 -> Triggers 24-hour lockout!
    attempts, lock = await crud.record_failed_password_attempt(async_session, user)
    assert attempts == 3
    assert lock is not None
    is_locked, remaining = await crud.check_user_lock(async_session, user)
    assert is_locked is True
    assert remaining is not None
    assert remaining.total_seconds() > 0

    # User enters valid password and unlocks
    await crud.verify_user(async_session, user.telegram_id)
    await async_session.refresh(user)
    assert user.is_verified is True
    assert user.failed_attempts == 0
    assert user.locked_until is None
    is_locked_after, _ = await crud.check_user_lock(async_session, user)
    assert is_locked_after is False
