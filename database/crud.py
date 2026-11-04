"""
Asynchronous CRUD operations for Tewabu ERP.
Enforces strict business-level isolation so no user can access another user's financial records.
"""

from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, update, delete, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import User, Business, Design, Expense, Order, FinancialRecord, BusinessSetting
from core.calculations import (
    CalculationResult,
    calculate_design_financials,
    round_money,
    to_decimal,
)
from core.constants import OrderStatus, ProfitStatus

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    language: str = "am",
) -> Tuple[User, Business]:
    """Retrieve existing user and business or register a new one atomically."""
    stmt = (
        select(User)
        .options(selectinload(User.business))
        .where(User.telegram_id == telegram_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update user profile if changed
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            updated = True
        if updated:
            await session.commit()
        return user, user.business

    # Create new User and default Business
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        language=language,
    )
    session.add(user)
    await session.flush()

    business = Business(
        user_id=user.id,
        name=f"የ{full_name or username or 'ተዋቡ'} ስፌት ቤት",
        currency="ETB",
        default_profit_margin=Decimal("0.25"),
    )
    session.add(business)
    await session.commit()
    await session.refresh(user)
    await session.refresh(business)
    return user, business

async def update_user_language(session: AsyncSession, telegram_id: int, language: str) -> None:
    """Update language preference for a user."""
    stmt = update(User).where(User.telegram_id == telegram_id).values(language=language)
    await session.execute(stmt)
    await session.commit()

async def verify_user(session: AsyncSession, telegram_id: int) -> bool:
    """Mark user as permanently verified for lifetime access and clear failure counters."""
    stmt = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(is_verified=True, failed_attempts=0, locked_until=None)
    )
    await session.execute(stmt)
    await session.commit()
    return True

async def record_failed_password_attempt(session: AsyncSession, user: User) -> Tuple[int, Optional[datetime]]:
    """Increment failed password count and lock account for 24h after 3 failed attempts."""
    now = datetime.now(timezone.utc)
    # Check if lock has expired
    if user.locked_until and user.locked_until <= now:
        user.failed_attempts = 0
        user.locked_until = None

    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= 3:
        user.locked_until = now + timedelta(days=1)

    await session.commit()
    await session.refresh(user)
    return user.failed_attempts, user.locked_until

async def check_user_lock(session: AsyncSession, user: User) -> Tuple[bool, Optional[timedelta]]:
    """Check if user is currently locked. Resets counter if lock duration passed."""
    if not user.locked_until:
        return False, None

    now = datetime.now(timezone.utc)
    if user.locked_until.tzinfo is None:
        user_lock_utc = user.locked_until.replace(tzinfo=timezone.utc)
    else:
        user_lock_utc = user.locked_until

    if user_lock_utc > now:
        remaining = user_lock_utc - now
        return True, remaining
    else:
        # Lock expired, reset
        user.failed_attempts = 0
        user.locked_until = None
        await session.commit()
        await session.refresh(user)
        return False, None

async def update_business_settings(
    session: AsyncSession,
    business_id: int,
    name: Optional[str] = None,
    default_profit_margin: Optional[Decimal] = None,
    currency: Optional[str] = None,
) -> Business:
    """Update business profile and default parameters."""
    stmt = select(Business).where(Business.id == business_id)
    res = await session.execute(stmt)
    business = res.scalar_one()

    if name:
        business.name = name.strip()
    if default_profit_margin is not None:
        business.default_profit_margin = default_profit_margin
    if currency:
        business.currency = currency.strip().upper()

    await session.commit()
    await session.refresh(business)
    return business

async def create_design(
    session: AsyncSession,
    business_id: int,
    name: str,
    calc_result: CalculationResult,
    expenses_list: List[Dict[str, Any]],
    customer_name: Optional[str] = None,
    order_id_code: Optional[str] = None,
    image_file_id: Optional[str] = None,
    gender: Optional[str] = None,
    clothing_item: Optional[str] = None,
    measurements_json: Optional[str] = None,
    notes: Optional[str] = None,
) -> Design:
    """
    Save complete clothing design calculation and individual expense items.
    """
    design = Design(
        business_id=business_id,
        name=name.strip(),
        customer_name=customer_name.strip() if customer_name else None,
        order_id_code=order_id_code.strip() if order_id_code else None,
        image_file_id=image_file_id.strip() if image_file_id else None,
        gender=gender,
        clothing_item=clothing_item,
        measurements_json=measurements_json,
        target_profit_margin=calc_result.target_margin,
        total_cost=calc_result.total_cost,
        break_even_price=calc_result.break_even_price,
        optimal_price=calc_result.optimal_price,
        actual_selling_price=calc_result.actual_selling_price,
        actual_profit=calc_result.actual_profit,
        profit_margin_pct=calc_result.profit_margin_pct,
        status=calc_result.status.value if calc_result.status else None,
        notes=notes,
    )
    session.add(design)
    await session.flush()

    for item in expenses_list:
        exp = Expense(
            design_id=design.id,
            category_key=item.get("category_key", "custom"),
            category_name=item.get("category_name", "Extra"),
            amount=round_money(to_decimal(item.get("amount", 0))),
            is_custom=item.get("is_custom", False),
            note=item.get("note"),
        )
        session.add(exp)

    # Track overall production expense record in financial records
    fin_record = FinancialRecord(
        business_id=business_id,
        design_id=design.id,
        record_type="EXPENSE",
        amount=calc_result.total_cost,
        category="PRODUCTION_COST",
        description=f"የልብስ ስፌት ወጪ: {design.name}",
        record_date=utc_now(),
    )
    session.add(fin_record)

    await session.commit()
    await session.refresh(design)
    return design

async def get_design(session: AsyncSession, design_id: int, business_id: int) -> Optional[Design]:
    """Fetch single design ensuring business data isolation."""
    stmt = (
        select(Design)
        .options(selectinload(Design.expenses))
        .where(and_(Design.id == design_id, Design.business_id == business_id))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def list_designs(
    session: AsyncSession,
    business_id: int,
    search_query: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> Tuple[List[Design], int]:
    """Retrieve list of designs for a business with pagination and optional search."""
    filters = [Design.business_id == business_id]
    if search_query:
        pattern = f"%{search_query.strip()}%"
        filters.append(
            or_(
                Design.name.ilike(pattern),
                Design.customer_name.ilike(pattern),
                Design.order_id_code.ilike(pattern),
            )
        )

    count_stmt = select(func.count(Design.id)).where(and_(*filters))
    total_count = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(Design)
        .where(and_(*filters))
        .order_by(desc(Design.id))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    designs = list(result.scalars().all())
    return designs, total_count

async def update_design_selling_price(
    session: AsyncSession,
    design_id: int,
    business_id: int,
    new_price: Decimal,
) -> Optional[Design]:
    """Update actual selling price and recalculate profit metrics."""
    design = await get_design(session, design_id, business_id)
    if not design:
        return None

    # Re-calculate with existing expenses & margin
    calc = calculate_design_financials(
        expenses=[e.amount for e in design.expenses],
        target_margin=design.target_profit_margin,
        actual_selling_price=new_price,
    )

    design.actual_selling_price = calc.actual_selling_price
    design.actual_profit = calc.actual_profit
    design.profit_margin_pct = calc.profit_margin_pct
    design.status = calc.status.value if calc.status else None
    design.updated_at = utc_now()

    await session.commit()
    await session.refresh(design)
    return design

async def delete_design(session: AsyncSession, design_id: int, business_id: int) -> bool:
    """Delete a design ensuring business isolation."""
    design = await get_design(session, design_id, business_id)
    if not design:
        return False
    await session.delete(design)
    await session.commit()
    return True

async def create_order_from_design(
    session: AsyncSession,
    business_id: int,
    design_id: Optional[int],
    customer_name: str,
    agreed_price: Decimal,
    customer_phone: Optional[str] = None,
    advance_payment: Decimal = Decimal("0.00"),
    due_date: Optional[date] = None,
    notes: Optional[str] = None,
) -> Order:
    """Create an order linked to a design."""
    count_stmt = select(func.count(Order.id)).where(Order.business_id == business_id)
    total_orders = (await session.execute(count_stmt)).scalar_one()
    order_number = f"ORD-{datetime.now().year}-{total_orders + 1:04d}"

    balance_due = agreed_price - advance_payment

    order = Order(
        business_id=business_id,
        design_id=design_id,
        order_number=order_number,
        customer_name=customer_name.strip(),
        customer_phone=customer_phone.strip() if customer_phone else None,
        status=OrderStatus.PENDING.value,
        agreed_price=agreed_price,
        advance_payment=advance_payment,
        balance_due=balance_due,
        due_date=due_date,
        notes=notes,
    )
    session.add(order)
    await session.flush()

    if advance_payment > Decimal("0.00"):
        fin_record = FinancialRecord(
            business_id=business_id,
            order_id=order.id,
            design_id=design_id,
            record_type="INCOME",
            amount=advance_payment,
            category="ADVANCE_PAYMENT",
            description=f"የቅድመ ክፍያ ለትዕዛዝ {order_number} ({customer_name})",
            record_date=utc_now(),
        )
        session.add(fin_record)

    await session.commit()
    await session.refresh(order)
    return order

async def get_orders_due_for_reminder(session: AsyncSession, days_ahead: int = 5) -> List[Tuple[Order, int]]:
    """
    Retrieve active orders whose due_date is within days_ahead days (e.g. <= 5 days from today)
    and haven't had the reminder sent yet.
    Returns list of tuples: (Order, owner_telegram_id).
    """
    today = date.today()
    target_date = today + timedelta(days=days_ahead)

    stmt = (
        select(Order, User.telegram_id)
        .join(Business, Order.business_id == Business.id)
        .join(User, Business.user_id == User.id)
        .options(selectinload(Order.design))
        .where(
            and_(
                Order.status.in_([OrderStatus.PENDING.value, OrderStatus.IN_PRODUCTION.value]),
                Order.due_date.is_not(None),
                Order.due_date <= target_date,
                Order.due_date >= today,
                Order.reminder_5d_sent == False,
            )
        )
    )
    result = await session.execute(stmt)
    return list(result.all())

async def mark_order_reminder_sent(session: AsyncSession, order_id: int) -> None:
    """Mark that 5-day reminder has been sent for this order."""
    stmt = update(Order).where(Order.id == order_id).values(reminder_5d_sent=True)
    await session.execute(stmt)
    await session.commit()

async def get_order(session: AsyncSession, order_id: int, business_id: int) -> Optional[Order]:
    """Retrieve an order ensuring business isolation."""
    stmt = (
        select(Order)
        .options(selectinload(Order.design))
        .where(and_(Order.id == order_id, Order.business_id == business_id))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def list_orders(
    session: AsyncSession,
    business_id: int,
    status_filter: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> Tuple[List[Order], int]:
    """List orders with optional status filter and pagination."""
    filters = [Order.business_id == business_id]
    if status_filter:
        filters.append(Order.status == status_filter)

    count_stmt = select(func.count(Order.id)).where(and_(*filters))
    total_count = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(Order)
        .options(selectinload(Order.design))
        .where(and_(*filters))
        .order_by(desc(Order.id))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total_count

async def update_order_status(
    session: AsyncSession,
    order_id: int,
    business_id: int,
    new_status: str,
    record_final_payment: bool = False,
) -> Optional[Order]:
    """
    Update order status. If order is marked completed or delivered,
    record final payment in financial records if requested.
    """
    order = await get_order(session, order_id, business_id)
    if not order:
        return None

    order.status = new_status
    order.updated_at = utc_now()

    if new_status in (OrderStatus.COMPLETED.value, OrderStatus.DELIVERED.value) and record_final_payment:
        remaining_balance = order.balance_due
        if remaining_balance > Decimal("0.00"):
            order.advance_payment = order.agreed_price
            order.balance_due = Decimal("0.00")
            
            fin_record = FinancialRecord(
                business_id=business_id,
                order_id=order.id,
                design_id=order.design_id,
                record_type="INCOME",
                amount=remaining_balance,
                category="FINAL_PAYMENT",
                description=f"የቀሪ ክፍያ ማጠናቀቂያ ለትዕዛዝ {order.order_number}",
                record_date=utc_now(),
            )
            session.add(fin_record)

    await session.commit()
    await session.refresh(order)
    return order

async def get_dashboard_metrics(session: AsyncSession, business_id: int) -> Dict[str, Any]:
    """
    Calculate business dashboard KPIs:
    - Total designs created.
    - Total production expenses.
    - Total revenue from completed sales ONLY (Delivered/Completed).
    - Total realized profit (Completed sales revenue minus their production costs).
    - Expected profit from pending/in-production orders (NOT counted as completed revenue!).
    - Count and list of loss-making designs.
    - Best-performing designs.
    """
    # 1. Total designs & total production expenses
    designs_stmt = (
        select(
            func.count(Design.id),
            func.coalesce(func.sum(Design.total_cost), Decimal("0.00")),
        )
        .where(Design.business_id == business_id)
    )
    designs_res = await session.execute(designs_stmt)
    total_designs, total_expenses = designs_res.one()
    total_expenses = round_money(total_expenses)

    # 2. Orders breakdown
    # Completed/Delivered orders = Realized revenue
    completed_stmt = (
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.agreed_price), Decimal("0.00")),
        )
        .where(
            and_(
                Order.business_id == business_id,
                Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.DELIVERED.value]),
            )
        )
    )
    completed_res = await session.execute(completed_stmt)
    completed_orders_count, completed_revenue = completed_res.one()
    completed_revenue = round_money(completed_revenue)

    # Cost of designs that belong to completed orders
    completed_cost_stmt = (
        select(func.coalesce(func.sum(Design.total_cost), Decimal("0.00")))
        .select_from(Order)
        .join(Design, Order.design_id == Design.id)
        .where(
            and_(
                Order.business_id == business_id,
                Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.DELIVERED.value]),
            )
        )
    )
    completed_cost = (await session.execute(completed_cost_stmt)).scalar_one()
    realized_profit = round_money(completed_revenue - completed_cost)

    # 3. Pending & In-Production orders (Expected future profit)
    pending_stmt = (
        select(Order)
        .options(selectinload(Order.design))
        .where(
            and_(
                Order.business_id == business_id,
                Order.status.in_([OrderStatus.PENDING.value, OrderStatus.IN_PRODUCTION.value]),
            )
        )
    )
    pending_orders = list((await session.execute(pending_stmt)).scalars().all())
    pending_orders_count = len(pending_orders)
    expected_profit_pending = Decimal("0.00")
    for po in pending_orders:
        cost = po.design.total_cost if po.design else Decimal("0.00")
        expected_profit_pending += (po.agreed_price - cost)
    expected_profit_pending = round_money(expected_profit_pending)

    # 4. Loss-making designs (selling price < total cost)
    loss_stmt = (
        select(Design)
        .where(
            and_(
                Design.business_id == business_id,
                Design.actual_selling_price.is_not(None),
                Design.actual_selling_price < Design.total_cost,
            )
        )
        .order_by(asc_or_desc := desc(Design.total_cost - Design.actual_selling_price))
    )
    loss_designs = list((await session.execute(loss_stmt)).scalars().all())
    loss_count = len(loss_designs)

    # 5. Best-performing designs (highest actual_profit)
    best_stmt = (
        select(Design)
        .where(
            and_(
                Design.business_id == business_id,
                Design.actual_profit.is_not(None),
                Design.actual_profit > Decimal("0.00"),
            )
        )
        .order_by(desc(Design.actual_profit))
        .limit(5)
    )
    best_designs = list((await session.execute(best_stmt)).scalars().all())

    return {
        "total_designs": total_designs or 0,
        "total_expenses": total_expenses,
        "completed_orders_count": completed_orders_count or 0,
        "completed_revenue": completed_revenue,
        "realized_profit": realized_profit,
        "pending_orders_count": pending_orders_count,
        "expected_profit_pending": expected_profit_pending,
        "loss_count": loss_count,
        "loss_designs": loss_designs,
        "best_designs": best_designs,
    }

async def get_financial_records(
    session: AsyncSession,
    business_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[FinancialRecord]:
    """Retrieve financial records for reporting within an optional date range."""
    filters = [FinancialRecord.business_id == business_id]
    if start_date:
        filters.append(FinancialRecord.record_date >= start_date)
    if end_date:
        filters.append(FinancialRecord.record_date <= end_date)

    stmt = (
        select(FinancialRecord)
        .where(and_(*filters))
        .order_by(desc(FinancialRecord.record_date))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
