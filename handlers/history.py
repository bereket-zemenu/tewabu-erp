"""
Design History Handler for Tewabu ERP.
View, search, edit selling price, simulate, and delete saved clothing designs.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business
import database.crud as crud
from core.calculations import format_currency, to_decimal
from core.constants import ProfitStatus
from keyboards.inline import (
    get_history_list_keyboard,
    get_design_detail_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
)

router = Router(name="history")

PAGE_SIZE = 6

class HistoryStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_new_price = State()

@router.callback_query(F.data.startswith("nav_history:"))
async def show_history_page(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await state.clear()
    page = int(callback.data.split(":")[1])
    offset = page * PAGE_SIZE

    designs, total_count = await crud.list_designs(
        session=session,
        business_id=business.id,
        limit=PAGE_SIZE,
        offset=offset,
    )
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

    if total_count == 0:
        text = (
            "📜 <b>የዲዛይን ታሪክ ባዶ ነው</b>\n\nእስካሁን የተመዘገበ ዲዛይን የለም። 'አዲስ ዲዛይን'ን ተጭነው መመዝገብ ይችላሉ።"
            if lang == "am" else
            "📜 <b>Design History is Empty</b>\n\nNo designs recorded yet. Click 'New Design' to start."
        )
        await callback.answer()
        await callback.message.edit_text(text=text, reply_markup=get_main_menu_keyboard(lang), parse_mode="HTML")
        return

    text = (
        f"📜 <b>የዲዛይን ታሪክ (ጠቅላላ፦ {total_count})</b>\n\n"
        f"ዝርዝር መረጃ ለማየት ከታች ካሉት ዲዛይኖች አንዱን ይምረጡ፦"
        if lang == "am" else
        f"📜 <b>Design History (Total: {total_count})</b>\n\n"
        f"Select a design below to view details:"
    )

    markup = get_history_list_keyboard(designs, page, total_pages, lang=lang)
    await callback.answer()
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("view_design:"))
async def view_single_design(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    parts = callback.data.split(":")
    design_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    design = await crud.get_design(session, design_id, business.id)
    if not design:
        await callback.answer("❌ ዲዛይኑ አልተገኘም!" if lang == "am" else "❌ Design not found!")
        return

    margin_pct = int(design.target_profit_margin * 100)
    lines = [
        f"👗 <b>ዲዛይን #{design.id}፦ {design.name}</b>\n",
        f"📅 <b>የተመዘገበበት ቀን፦</b> {design.created_at.strftime('%Y-%m-%d %H:%M')}",
    ]
    if design.customer_name:
        lines.append(f"👤 <b>ደንበኛ፦</b> {design.customer_name}")
    if design.order_id_code:
        lines.append(f"🔖 <b>የትዕዛዝ መለያ፦</b> {design.order_id_code}")

    lines.append("\n<b>የወጪዎች ክፍፍል፦</b>")
    lines.append("─────────────────────")
    for exp in design.expenses:
        lines.append(f"• {exp.category_name}፦ <b>{format_currency(exp.amount, lang=lang)}</b>")
    lines.append("─────────────────────")
    lines.extend([
        f"💰 <b>አጠቃላይ ወጪ (Total Cost)፦</b> {format_currency(design.total_cost, lang=lang)}",
        f"⚖️ <b>ወጪ መሸፈኛ ዋጋ፦</b> {format_currency(design.break_even_price, lang=lang)}",
        f"🪙 <b>ተመራጭ መሸጫ ዋጋ፦</b> {format_currency(design.optimal_price, lang=lang)} <i>({margin_pct}%)</i>",
    ])

    if design.actual_selling_price is not None:
        lines.append(f"\n🏷️ <b>ትክክለኛ መሸጫ ዋጋ፦</b> {format_currency(design.actual_selling_price, lang=lang)}")
        if design.status == ProfitStatus.LOSS.value:
            lines.append(f"🔴 <b>ሁኔታ፦ ኪሳራ (-{format_currency(design.total_cost - design.actual_selling_price, lang=lang)})</b>")
        elif design.status == ProfitStatus.BREAK_EVEN.value:
            lines.append("⚖️ <b>ሁኔታ፦ ወጪና ገቢ እኩል (0.00 ብር ትርፍ)</b>")
        elif design.status == ProfitStatus.OPTIMAL.value:
            lines.append(f"🪙 <b>ሁኔታ፦ ተመራጭ ዋጋ (+{format_currency(design.actual_profit, lang=lang)})</b>")
        elif design.status == ProfitStatus.ABOVE_TARGET.value:
            lines.append(f"🟢 <b>ሁኔታ፦ ከተጠበቀው በላይ (+{format_currency(design.actual_profit, lang=lang)})</b>")
        else:
            lines.append(f"🟡 <b>ሁኔታ፦ ትርፍ አለው (+{format_currency(design.actual_profit, lang=lang)})</b>")
    else:
        lines.append("\n<i>ትክክለኛ መሸጫ ዋጋ አልተመዘገበም። 'ዋጋ አስተካክል'ን ተጭነው ማስገባት ይችላሉ።</i>")

    markup = get_design_detail_keyboard(design.id, return_page=page, lang=lang)
    await callback.answer()
    text = "\n".join(lines)

    if design.image_file_id:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=design.image_file_id,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "search_design")
async def start_design_search(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await state.set_state(HistoryStates.waiting_for_search_query)
    prompt = (
        "🔍 <b>ዲዛይን መፈለጊያ</b>\n\n"
        "የሚፈልጉትን የዲዛይን ስም ወይም የደንበኛ ስም ይፃፉ፦"
        if lang == "am" else
        "🔍 <b>Search Designs</b>\n\n"
        "Type the design name or customer name to search:"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(HistoryStates.waiting_for_search_query)
async def process_search_query(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    query = message.text.strip() if message.text else ""
    await state.clear()

    designs, count = await crud.list_designs(
        session=session,
        business_id=business.id,
        search_query=query,
        limit=PAGE_SIZE,
    )

    if count == 0:
        await message.answer(
            f"❌ ለ <b>'{query}'</b> የተገኘ ዲዛይን የለም።" if lang == "am" else f"❌ No designs found matching <b>'{query}'</b>.",
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML",
        )
        return

    text = (
        f"🔍 <b>የፍለጋ ውጤት ለ '{query}' (የተገኙ፦ {count})</b>፦"
        if lang == "am" else
        f"🔍 <b>Search results for '{query}' ({count} found)</b>:"
    )
    markup = get_history_list_keyboard(designs, 0, (count + PAGE_SIZE - 1) // PAGE_SIZE, lang=lang)
    await message.answer(text=text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_price:"))
async def prompt_edit_price(callback: CallbackQuery, state: FSMContext, lang: str):
    design_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(editing_design_id=design_id)
    await state.set_state(HistoryStates.waiting_for_new_price)
    prompt = (
        "✏️ <b>አዲስ የመሸጫ ዋጋ ያስገቡ፦</b>\n\n"
        "ይህን ዲዛይን ለደንበኛ የምትሸጡበትን አዲስ ትክክለኛ ዋጋ በብር ያስገቡ፦"
        if lang == "am" else
        "✏️ <b>Enter New Selling Price:</b>\n\n"
        "Enter new actual selling price in ETB:"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(HistoryStates.waiting_for_new_price)
async def process_edit_price(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    try:
        new_price = to_decimal(message.text)
        if new_price < Decimal("0"):
            raise ValueError
    except Exception:
        await message.answer("❌ እባክዎ ትክክለኛ ያልአሉታዊ ዋጋ ያስገቡ፦" if lang == "am" else "❌ Enter valid non-negative price:")
        return

    data = await state.get_data()
    design_id = data.get("editing_design_id")
    await state.clear()

    updated = await crud.update_design_selling_price(
        session=session,
        design_id=design_id,
        business_id=business.id,
        new_price=new_price,
    )

    if not updated:
        await message.answer("❌ ዲዛይኑ አልተገኘም!" if lang == "am" else "❌ Design not found!")
        return

    status_str = f"<b>{updated.status}</b>"
    profit_str = format_currency(updated.actual_profit or Decimal("0"), lang=lang)

    text = (
        f"✅ <b>የመሸጫ ዋጋው ተሻሽሏል!</b>\n\n"
        f"• አዲስ መሸጫ ዋጋ፦ <b>{format_currency(updated.actual_selling_price, lang=lang)}</b>\n"
        f"• ትርፍ/ኪሳራ፦ <b>{profit_str}</b>\n"
        f"• ሁኔታ፦ {status_str}"
        if lang == "am" else
        f"✅ <b>Selling Price Updated!</b>\n\n"
        f"• New Selling Price: <b>{format_currency(updated.actual_selling_price, lang=lang)}</b>\n"
        f"• Net Profit/Loss: <b>{profit_str}</b>\n"
        f"• Status: {status_str}"
    )
    await message.answer(text=text, reply_markup=get_design_detail_keyboard(design_id, 0, lang=lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("delete_design:"))
async def delete_design_handler(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    design_id = int(callback.data.split(":")[1])
    success = await crud.delete_design(session, design_id, business.id)
    if success:
        await callback.answer("✅ ዲዛይኑ ተሰርዟል!" if lang == "am" else "✅ Design deleted!", show_alert=True)
    else:
        await callback.answer("❌ ዲዛይኑ አልተገኘም!" if lang == "am" else "❌ Not found!")

    # Return to history page 0
    designs, total_count = await crud.list_designs(session, business.id, limit=PAGE_SIZE)
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
    markup = get_history_list_keyboard(designs, 0, total_pages, lang=lang) if total_count > 0 else get_main_menu_keyboard(lang)
    text = (
        f"📜 <b>የዲዛይን ታሪክ (ጠቅላላ፦ {total_count})</b>"
        if lang == "am" else
        f"📜 <b>Design History (Total: {total_count})</b>"
    )
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
