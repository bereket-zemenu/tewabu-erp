"""
Interactive Price Simulator Handler for Tewabu ERP.
Enables tailor house owners to simulate various selling prices against production costs
and instantly see color-coded profit or loss outcomes.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business
import database.crud as crud
from core.calculations import (
    calculate_design_financials,
    to_decimal,
    format_currency,
    validate_margin,
)
from core.constants import ProfitStatus
from localization.i18n import t
from keyboards.inline import get_cancel_keyboard, get_main_menu_keyboard

router = Router(name="simulator")

class SimulatorStates(StatesGroup):
    waiting_for_cost = State()
    waiting_for_margin = State()
    waiting_for_test_price = State()

@router.callback_query(F.data == "nav_price_simulator")
async def start_simulator_fresh(callback: CallbackQuery, state: FSMContext, lang: str):
    """Entry point for standalone price simulation."""
    await state.clear()
    await state.set_state(SimulatorStates.waiting_for_cost)
    prompt = (
        "🎯 <b>የዋጋ አስመሳይ (Price Simulator)</b>\n\n"
        "የተለያዩ መሸጫ ዋጋዎችን በመሞከር ትርፍ እና ኪሳራን አስቀድመው ይመልከቱ!\n\n"
        "እባክዎ መጀመሪያ የልብሱን <b>አጠቃላይ የምርት ወጪ (Total Cost)</b> በብር ያስገቡ፦"
        if lang == "am" else
        "🎯 <b>Selling Price Simulator</b>\n\n"
        "Simulate different selling prices and preview profit or loss instantly!\n\n"
        "Please enter the <b>Total Production Cost</b> in ETB:"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("sim_design:"))
async def start_simulator_from_design(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    """Entry point from an existing design."""
    design_id = int(callback.data.split(":")[1])
    design = await crud.get_design(session, design_id, business.id)
    if not design:
        await callback.answer("❌ ዲዛይኑ አልተገኘም!" if lang == "am" else "❌ Design not found!")
        return

    await state.clear()
    await state.update_data(
        total_cost_val=str(design.total_cost),
        target_margin_val=str(design.target_profit_margin),
        design_name=design.name,
    )
    await state.set_state(SimulatorStates.waiting_for_test_price)
    
    margin_pct = int(design.target_profit_margin * 100)
    prompt = (
        f"🎯 <b>የዋጋ አስመሳይ፦ {design.name}</b>\n"
        f"• አጠቃላይ ወጪ፦ <b>{format_currency(design.total_cost, lang=lang)}</b>\n"
        f"• ወጪ መሸፈኛ ዋጋ፦ <b>{format_currency(design.break_even_price, lang=lang)}</b>\n"
        f"• ተመራጭ መሸጫ ዋጋ (🪙 {margin_pct}%)፦ <b>{format_currency(design.optimal_price, lang=lang)}</b>\n\n"
        f"ለመሞከር የሚፈልጉትን <b>መሸጫ ዋጋ በብር</b> ይፃፉ (ምሳሌ፦ {design.optimal_price + 200:.0f})፦"
        if lang == "am" else
        f"🎯 <b>Price Simulator: {design.name}</b>\n"
        f"• Total Cost: <b>{format_currency(design.total_cost, lang=lang)}</b>\n"
        f"• Break-even: <b>{format_currency(design.break_even_price, lang=lang)}</b>\n"
        f"• Optimal Price (🪙 {margin_pct}%): <b>{format_currency(design.optimal_price, lang=lang)}</b>\n\n"
        f"Type any <b>hypothetical selling price in ETB</b> to simulate:"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(SimulatorStates.waiting_for_cost)
async def process_sim_cost(message: Message, state: FSMContext, business: Business, lang: str):
    try:
        cost = to_decimal(message.text)
        if cost <= Decimal("0"):
            raise ValueError
    except Exception:
        await message.answer("❌ እባክዎ ከዜሮ በላይ የሆነ ትክክለኛ ወጪ ያስገቡ፦" if lang == "am" else "❌ Enter valid positive cost:")
        return

    default_margin = business.default_profit_margin or Decimal("0.25")
    await state.update_data(
        total_cost_val=str(cost),
        target_margin_val=str(default_margin),
    )
    await state.set_state(SimulatorStates.waiting_for_test_price)

    calc = calculate_design_financials(expenses=[cost], target_margin=default_margin)
    margin_pct = int(default_margin * 100)

    prompt = (
        f"📊 <b>የወጪ መረጃ፦</b>\n"
        f"• አጠቃላይ ወጪ፦ <b>{format_currency(calc.total_cost, lang=lang)}</b>\n"
        f"• ወጪ መሸፈኛ፦ <b>{format_currency(calc.break_even_price, lang=lang)}</b>\n"
        f"• ተመራጭ መሸጫ ዋጋ (🪙 {margin_pct}%)፦ <b>{format_currency(calc.optimal_price, lang=lang)}</b>\n\n"
        f"አሁን ለመሞከር የሚፈልጉትን <b>መሸጫ ዋጋ በብር</b> ያስገቡ፦"
        if lang == "am" else
        f"📊 <b>Cost Summary:</b>\n"
        f"• Total Cost: <b>{format_currency(calc.total_cost, lang=lang)}</b>\n"
        f"• Break-even: <b>{format_currency(calc.break_even_price, lang=lang)}</b>\n"
        f"• Optimal Price (🪙 {margin_pct}%): <b>{format_currency(calc.optimal_price, lang=lang)}</b>\n\n"
        f"Now enter any <b>test selling price in ETB</b> to simulate:"
    )
    await message.answer(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(SimulatorStates.waiting_for_test_price)
async def process_test_price(message: Message, state: FSMContext, lang: str):
    try:
        test_price = to_decimal(message.text)
        if test_price < Decimal("0"):
            raise ValueError
    except Exception:
        await message.answer("❌ እባክዎ ትክክለኛ መሸጫ ዋጋ ያስገቡ፦" if lang == "am" else "❌ Enter valid selling price:")
        return

    data = await state.get_data()
    total_cost = Decimal(data["total_cost_val"])
    target_margin = Decimal(data["target_margin_val"])
    margin_pct = int(target_margin * 100)

    calc = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=test_price,
    )

    lines = [
        "🎯 <b>የዋጋ አስመሳይ ውጤት (Simulation Result)</b>\n" if lang == "am" else "🎯 <b>Price Simulation Result</b>\n",
        f"• የምርት ወጪ፦ <b>{format_currency(calc.total_cost, lang=lang)}</b>",
        f"• የተሞከረው መሸጫ ዋጋ፦ <b>{format_currency(calc.actual_selling_price, lang=lang)}</b>",
        f"• ተመራጭ መሸጫ ዋጋ፦ <b>{format_currency(calc.optimal_price, lang=lang)}</b> <i>({margin_pct}% ዒላማ)</i>",
        "─────────────────────",
    ]

    if calc.status == ProfitStatus.LOSS:
        lines.extend([
            "🔴 <b>ሁኔታ፦ ኪሳራ (FINANCIAL LOSS)</b>",
            f"❌ <b>የኪሳራ መጠን፦ -{format_currency(calc.loss_amount, lang=lang)}</b>",
            f"<i>ይህ ዋጋ ከወጣው ወጪ በ {format_currency(calc.loss_amount, lang=lang)} ያንሳል!</i>",
        ])
    elif calc.status == ProfitStatus.BREAK_EVEN:
        lines.extend([
            "⚖️ <b>ሁኔታ፦ ወጪና ገቢ እኩል (BREAK-EVEN)</b>",
            "<i>ወጪውን ብቻ ይሸፍናል፤ የተጣራ ትርፍ 0 ብር ነው።</i>",
        ])
    elif calc.status == ProfitStatus.OPTIMAL:
        lines.extend([
            "🪙 <b>ሁኔታ፦ ተመራጭ ዋጋ (OPTIMAL PRICE - GOLD)</b>",
            f"🌟 <b>የሚገኝ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)} ({calc.profit_margin_pct:.1f}%)</b>",
            f"<i>በትክክል የታለመውን {margin_pct}% ትርፍ ያስገኛል!</i>",
        ])
    elif calc.status == ProfitStatus.ABOVE_TARGET:
        lines.extend([
            "🟢 <b>ሁኔታ፦ ከተጠበቀው ትርፍ በላይ (ABOVE TARGET PROFIT)</b>",
            f"🚀 <b>የሚገኝ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)} ({calc.profit_margin_pct:.1f}%)</b>",
            "<i>በጣም ምርጥ! ከተመራጩ ዋጋ በላይ ከፍተኛ ትርፍ ያስገኛል።</i>",
        ])
    else:  # BELOW_TARGET
        lines.extend([
            "🟡 <b>ሁኔታ፦ ትርፍ አለው (ግን ከዒላማው በታች)</b>",
            f"👌 <b>የሚገኝ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)} ({calc.profit_margin_pct:.1f}%)</b>",
            f"<i>ትርፍ አለው፤ ነገር ግን ከ {margin_pct}% ዒላማ ያነሰ ነው።</i>",
        ])

    lines.append("\n🔄 ሌላ ዋጋ ለመሞከር ቁጥር ይፃፉ ወይም ወደ ዋና ሜኑ ለመመለስ 'ሰርዝ'ን ይጫኑ።" if lang == "am" else "\n🔄 Type another price to re-simulate or Cancel to exit.")

    await message.answer(text="\n".join(lines), reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")
