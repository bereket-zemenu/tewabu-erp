"""
Financial Reports and Analytics Handler for Tewabu ERP.
Provides daily, weekly, monthly summaries, Matplotlib charts, and CSV downloads.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business
import database.crud as crud
from core.calculations import format_currency
from localization.i18n import t
from services.report_service import get_period_summary, export_designs_csv, export_financial_records_csv
from services.chart_service import generate_financial_bar_chart
from keyboards.inline import get_reports_menu_keyboard, get_main_menu_keyboard

router = Router(name="reports")

@router.callback_query(F.data == "nav_reports")
async def show_reports_menu(callback: CallbackQuery, lang: str):
    prompt = (
        "📈 <b>የፋይናንስ ሪፖርቶች እና ትንተና</b>\n\n"
        "የሚፈልጉትን የሪፖርት አይነት ወይም የ CSV ኤክስፖርት ይምረጡ፦"
        if lang == "am" else
        "📈 <b>Financial Reports & Analytics</b>\n\n"
        "Select a reporting period, visual chart, or CSV export below:"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_reports_menu_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("rep_period:"))
async def show_period_report(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    period = callback.data.split(":")[1]  # daily, weekly, monthly
    summary = await get_period_summary(session, business.id, period)

    period_names = {
        "daily": ("የዛሬ ሪፖርት", "Daily Report"),
        "weekly": ("የሳምንቱ ሪፖርት", "Weekly Report"),
        "monthly": ("የወሩ ሪፖርት", "Monthly Report"),
    }
    title = period_names.get(period, ("ሪፖርት", "Report"))[0 if lang == "am" else 1]

    income = summary["total_income"]
    expenses = summary["total_expenses"]
    profit = summary["net_profit"]
    designs_count = summary["designs_count"]

    profit_icon = "🟢" if profit > Decimal("0") else ("⚖️" if profit == Decimal("0") else "🔴")

    lines = [
        f"📅 <b>{title}</b>\n"
        f"🏢 <b>{business.name}</b>\n"
        f"─────────────────────",
        f"👗 <b>የተመዘገቡ ዲዛይኖች፦</b> <b>{designs_count}</b>",
        f"💵 <b>የተሰበሰበ ገቢ (Revenue)፦</b> <b>{format_currency(income, lang=lang)}</b>",
        f"💸 <b>የወጣ ወጪ (Total Expenses)፦</b> <b>{format_currency(expenses, lang=lang)}</b>",
        f"{profit_icon} <b>የተጣራ ትርፍ (Net Profit)፦</b> <b>{format_currency(profit, lang=lang)}</b>",
        "─────────────────────",
    ]

    await callback.answer()
    await callback.message.edit_text(
        text="\n".join(lines),
        reply_markup=get_reports_menu_keyboard(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "rep_chart")
async def send_visual_chart(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await callback.answer("⏳ ቻርቱ እየተዘጋጀ ነው..." if lang == "am" else "⏳ Generating chart...")
    metrics = await crud.get_dashboard_metrics(session, business.id)

    chart_bytes = generate_financial_bar_chart(
        revenue=metrics["completed_revenue"],
        costs=metrics["total_expenses"],
        profit=metrics["realized_profit"],
    )

    photo_file = BufferedInputFile(chart_bytes, filename="tewabu_financial_chart.png")
    caption = (
        f"📊 <b>የፋይናንስ ገጽታ (Financial Overview)</b>\n"
        f"🏢 {business.name}\n"
        f"• ጠቅላላ ሽያጭ፦ {format_currency(metrics['completed_revenue'], lang=lang)}\n"
        f"• የምርት ወጪ፦ {format_currency(metrics['total_expenses'], lang=lang)}\n"
        f"• የተጣራ ትርፍ፦ {format_currency(metrics['realized_profit'], lang=lang)}"
    )

    await callback.message.answer_photo(photo=photo_file, caption=caption, parse_mode="HTML")

@router.callback_query(F.data == "rep_csv_designs")
async def send_designs_csv(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await callback.answer("⏳ CSV ፋይል እየተዘጋጀ ነው..." if lang == "am" else "⏳ Exporting CSV...")
    csv_bytes = await export_designs_csv(session, business.id)
    doc_file = BufferedInputFile(csv_bytes, filename=f"tewabu_designs_{business.id}.csv")
    caption = "📥 <b>የሁሉም ዲዛይኖች እና ወጪዎች መዝገብ በ CSV</b>" if lang == "am" else "📥 <b>Designs and Costs CSV Export</b>"
    await callback.message.answer_document(document=doc_file, caption=caption, parse_mode="HTML")

@router.callback_query(F.data == "rep_csv_ledger")
async def send_ledger_csv(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await callback.answer("⏳ የፋይናንስ መዝገብ እየተዘጋጀ ነው..." if lang == "am" else "⏳ Exporting Ledger...")
    csv_bytes = await export_financial_records_csv(session, business.id)
    doc_file = BufferedInputFile(csv_bytes, filename=f"tewabu_financial_records_{business.id}.csv")
    caption = "📥 <b>የገቢ እና ወጪ ሙሉ የፋይናንስ መዝገብ በ CSV</b>" if lang == "am" else "📥 <b>Financial Income & Expense Ledger CSV</b>"
    await callback.message.answer_document(document=doc_file, caption=caption, parse_mode="HTML")
