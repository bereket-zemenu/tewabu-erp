"""
Quick Cost Calculator Handler for Tewabu ERP.
Instant production cost calculator without requiring customer or order details.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import Business
from core.calculations import (
    calculate_design_financials,
    to_decimal,
    format_currency,
    validate_margin,
)
from keyboards.inline import get_cancel_keyboard, get_main_menu_keyboard

router = Router(name="cost_calc")

class QuickCalcStates(StatesGroup):
    waiting_for_inputs = State()

@router.callback_query(F.data == "nav_cost_calculator")
async def start_quick_calc(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await state.set_state(QuickCalcStates.waiting_for_inputs)
    prompt = (
        "🧮 <b>ፈጣን የወጪ ማስያ (Quick Cost Calculator)</b>\n\n"
        "የወጪዎችን ዝርዝር በደማር ወይም በቦታ ለይተው በአንድ ጊዜ ማስገባት ይችላሉ፦\n"
        "<i>(ምሳሌ፦ <b>500 + 120 + 350 + 200</b> ወይም <b>1200</b>)</i>"
        if lang == "am" else
        "🧮 <b>Quick Cost Calculator</b>\n\n"
        "Enter individual expense amounts separated by plus (+) or spaces:\n"
        "<i>(e.g., <b>500 + 120 + 350 + 200</b> or <b>1200</b>)</i>"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(QuickCalcStates.waiting_for_inputs)
async def process_quick_calc_input(message: Message, state: FSMContext, business: Business, lang: str):
    raw = message.text.strip() if message.text else ""
    # Support "500 + 200 + 300" or space separated "500 200 300"
    delimiters = ["+", ",", " "]
    parts = [raw]
    for d in delimiters:
        new_parts = []
        for p in parts:
            new_parts.extend(p.split(d))
        parts = new_parts

    amounts = []
    for p in parts:
        cleaned = p.strip()
        if cleaned:
            try:
                amt = to_decimal(cleaned)
                if amt > Decimal("0"):
                    amounts.append(amt)
            except Exception:
                pass

    if not amounts:
        await message.answer(
            "❌ እባክዎ ትክክለኛ የቁጥር ድምር ያስገቡ (ምሳሌ፦ 500 + 300 + 150)፦" if lang == "am" else "❌ Enter valid numbers (e.g. 500 + 300 + 150):",
            reply_markup=get_cancel_keyboard(lang),
        )
        return

    default_margin = business.default_profit_margin or Decimal("0.25")
    margin_pct = int(default_margin * 100)

    calc = calculate_design_financials(expenses=amounts, target_margin=default_margin)

    lines = [
        "🧮 <b>የፈጣን ወጪ ስሌት ውጤት፦</b>\n" if lang == "am" else "🧮 <b>Quick Calculation Result:</b>\n",
        f"• የገቡት የወጪ ክፍሎች ብዛት፦ <b>{len(amounts)}</b>",
        f"• አጠቃላይ የምርት ወጪ (Total Cost)፦ <b>{format_currency(calc.total_cost, lang=lang)}</b>",
        f"• ወጪ መሸፈኛ ዋጋ (Break-even)፦ <b>{format_currency(calc.break_even_price, lang=lang)}</b>",
        f"• የታለመው ትርፍ መቶኛ፦ <b>{margin_pct}%</b>\n",
        f"🪙 <b>ተመራጭ መሸጫ ዋጋ (OPTIMAL PRICE)፦</b>",
        f"👉 <b><u>{format_currency(calc.optimal_price, lang=lang)}</u></b>",
        f"<i>(ይህ ዋጋ የተጣራ {format_currency(calc.optimal_price - calc.total_cost, lang=lang)} ትርፍ ያስገኛል)</i>",
        "\n─────────────────────",
        "🔄 ሌላ ወጪ ለማስላት ቁጥሮችን ይፃፉ ወይም ወደ ዋና ሜኑ ይመለሱ።" if lang == "am" else "🔄 Type more numbers to calculate again or return to main menu.",
    ]
    await message.answer(text="\n".join(lines), reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")
