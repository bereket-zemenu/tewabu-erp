"""
Business Dashboard Handler for Tewabu ERP.
Aggregates and presents high-level KPIs, completed revenue vs pending orders,
realized profit, loss-making designs, and top-performing garments.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business
import database.crud as crud
from core.calculations import format_currency
from localization.i18n import t
from keyboards.inline import get_main_menu_keyboard

router = Router(name="dashboard")

@router.callback_query(F.data == "nav_dashboard")
async def show_business_dashboard(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    """Render comprehensive business dashboard."""
    metrics = await crud.get_dashboard_metrics(session, business.id)

    total_designs = metrics["total_designs"]
    total_expenses = metrics["total_expenses"]
    completed_rev = metrics["completed_revenue"]
    realized_profit = metrics["realized_profit"]
    pending_count = metrics["pending_orders_count"]
    expected_profit_pending = metrics["expected_profit_pending"]
    loss_count = metrics["loss_count"]
    loss_designs = metrics["loss_designs"]
    best_designs = metrics["best_designs"]

    profit_icon = "🟢" if realized_profit > Decimal("0") else ("⚖️" if realized_profit == Decimal("0") else "🔴")

    lines = [
        f"📊 <b>የንግድ ዳሽቦርድ (Business Dashboard)</b>\n"
        f"🏢 <b>{business.name}</b>\n"
        f"─────────────────────",
        f"👗 <b>ጠቅላላ የተፈጠሩ ዲዛይኖች፦</b> <b>{total_designs}</b>",
        f"💸 <b>አጠቃላይ የምርት ወጪዎች፦</b> <b>{format_currency(total_expenses, lang=lang)}</b>",
        "─────────────────────",
        f"💰 <b>የተጠናቀቁ ሽያጮች ገቢ፦</b> <b>{format_currency(completed_rev, lang=lang)}</b>",
        f"{profit_icon} <b>ትክክለኛ የተገኘ የተጣራ ትርፍ፦</b> <b>{format_currency(realized_profit, lang=lang)}</b>",
        "─────────────────────",
        f"⏳ <b>በመጠባበቅ ላይ ያሉ ትዕዛዞች፦</b> <b>{pending_count}</b>",
        f"🔮 <b>ከተጠባባቂ ትዕዛዞች የሚጠበቅ ትርፍ፦</b> <b>{format_currency(expected_profit_pending, lang=lang)}</b>",
        f"<i>(ማስታወሻ፦ ተጠባባቂ ትዕዛዞች ገና ስላልተጠናቀቁ እንደ ተጨባጭ ገቢ አልተቆጠሩም)</i>",
        "─────────────────────",
    ]

    # Best-performing designs
    if best_designs:
        lines.append("🏆 <b>ምርጥ አትራፊ ዲዛይኖች (Top Performers)፦</b>")
        for idx, bd in enumerate(best_designs[:3], 1):
            lines.append(f"  {idx}. {bd.name} (+{format_currency(bd.actual_profit or Decimal('0'), lang=lang)})")
        lines.append("─────────────────────")

    # Loss-making designs warning
    if loss_count > 0:
        lines.append(f"🔴 <b>ኪሳራ ያስከተሉ ዲዛይኖች፦ {loss_count}</b>")
        for ld in loss_designs[:3]:
            loss_val = ld.total_cost - (ld.actual_selling_price or Decimal("0"))
            lines.append(f"  • {ld.name}፦ -{format_currency(loss_val, lang=lang)}")
        lines.append("─────────────────────")
    else:
        lines.append("✅ <b>ምንም ኪሳራ ያስከተለ ዲዛይን የለም!</b>")

    await callback.answer()
    await callback.message.edit_text(
        text="\n".join(lines),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )
