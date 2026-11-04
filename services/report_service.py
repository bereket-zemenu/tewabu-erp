"""
Financial Report and CSV Export Service for Tewabu ERP.
"""

import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from database.models import Design, Order, FinancialRecord
from core.calculations import round_money

def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Calculate start and end timestamps in UTC for daily, weekly, or monthly periods."""
    now = datetime.now(timezone.utc)
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default all time
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return start, now

async def get_period_summary(session: AsyncSession, business_id: int, period: str) -> Dict[str, Any]:
    """
    Compute total income, total expense, and net profit for a given period.
    """
    start_date, end_date = get_period_dates(period)

    # 1. Total Expenses from FinancialRecord
    exp_stmt = (
        select(func.coalesce(func.sum(FinancialRecord.amount), Decimal("0.00")))
        .where(
            and_(
                FinancialRecord.business_id == business_id,
                FinancialRecord.record_type == "EXPENSE",
                FinancialRecord.record_date >= start_date,
                FinancialRecord.record_date <= end_date,
            )
        )
    )
    total_expenses = (await session.execute(exp_stmt)).scalar_one()

    # 2. Total Income from FinancialRecord
    inc_stmt = (
        select(func.coalesce(func.sum(FinancialRecord.amount), Decimal("0.00")))
        .where(
            and_(
                FinancialRecord.business_id == business_id,
                FinancialRecord.record_type == "INCOME",
                FinancialRecord.record_date >= start_date,
                FinancialRecord.record_date <= end_date,
            )
        )
    )
    total_income = (await session.execute(inc_stmt)).scalar_one()

    # 3. Designs created during period
    des_stmt = (
        select(func.count(Design.id))
        .where(
            and_(
                Design.business_id == business_id,
                Design.created_at >= start_date,
                Design.created_at <= end_date,
            )
        )
    )
    designs_count = (await session.execute(des_stmt)).scalar_one()

    net_profit = total_income - total_expenses

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_income": round_money(total_income),
        "total_expenses": round_money(total_expenses),
        "net_profit": round_money(net_profit),
        "designs_count": designs_count,
    }

async def export_designs_csv(session: AsyncSession, business_id: int) -> bytes:
    """Generate a clean CSV export of all designs with cost breakdowns."""
    stmt = (
        select(Design)
        .where(Design.business_id == business_id)
        .order_by(Design.id.desc())
    )
    designs = list((await session.execute(stmt)).scalars().all())

    output = io.StringIO()
    # Add UTF-8 BOM so Excel opens Ethiopian characters and text cleanly
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow([
        "ID",
        "Design Name (የዲዛይን ስም)",
        "Customer Name (የደንበኛ ስም)",
        "Order Ref",
        "Total Cost (አጠቃላይ ወጪ - ETB)",
        "Break-even Price (ወጪ መሸፈኛ - ETB)",
        "Optimal Price (ተመራጭ ዋጋ - ETB)",
        "Actual Selling Price (ትክክለኛ ዋጋ - ETB)",
        "Actual Profit (ትክክለኛ ትርፍ - ETB)",
        "Profit Margin % (ትርፍ መቶኛ)",
        "Status (ሁኔታ)",
        "Date Created",
    ])

    for d in designs:
        writer.writerow([
            d.id,
            d.name,
            d.customer_name or "-",
            d.order_id_code or "-",
            f"{d.total_cost:.2f}",
            f"{d.break_even_price:.2f}",
            f"{d.optimal_price:.2f}",
            f"{d.actual_selling_price:.2f}" if d.actual_selling_price is not None else "-",
            f"{d.actual_profit:.2f}" if d.actual_profit is not None else "-",
            f"{d.profit_margin_pct:.2f}%" if d.profit_margin_pct is not None else "-",
            d.status or "-",
            d.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return output.getvalue().encode("utf-8")

async def export_financial_records_csv(session: AsyncSession, business_id: int) -> bytes:
    """Generate CSV export of all financial income and expense ledger records."""
    stmt = (
        select(FinancialRecord)
        .where(FinancialRecord.business_id == business_id)
        .order_by(FinancialRecord.record_date.desc())
    )
    records = list((await session.execute(stmt)).scalars().all())

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow([
        "Record ID",
        "Date",
        "Type (ገቢ/ወጪ)",
        "Category",
        "Amount (ብር / ETB)",
        "Description (ዝርዝር)",
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.record_date.strftime("%Y-%m-%d %H:%M"),
            r.record_type,
            r.category,
            f"{r.amount:.2f}",
            r.description or "",
        ])

    return output.getvalue().encode("utf-8")
