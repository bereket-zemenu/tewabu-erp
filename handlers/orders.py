"""
Order Management Handler for Tewabu ERP.
Enables tailoring businesses to track customer orders through all stages:
Pending, In Production, Completed, Delivered, Cancelled.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business, Order
import database.crud as crud
from core.calculations import format_currency, to_decimal
from core.constants import OrderStatus
from localization.i18n import t
from keyboards.inline import (
    get_orders_list_keyboard,
    get_order_detail_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
)

router = Router(name="orders")

PAGE_SIZE = 6

class OrderCreationStates(StatesGroup):
    waiting_for_customer_name = State()
    waiting_for_agreed_price = State()
    waiting_for_advance = State()
    waiting_for_phone = State()

@router.callback_query(F.data.startswith("nav_orders:"))
async def show_orders_list(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await state.clear()
    parts = callback.data.split(":")
    status_filter = parts[1]  # 'all' or OrderStatus value
    page = int(parts[2]) if len(parts) > 2 else 0
    offset = page * PAGE_SIZE

    filter_val = None if status_filter == "all" else status_filter
    orders, total_count = await crud.list_orders(
        session=session,
        business_id=business.id,
        status_filter=filter_val,
        limit=PAGE_SIZE,
        offset=offset,
    )
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

    text = (
        f"📦 <b>የትዕዛዝ ክትትል (ጠቅላላ፦ {total_count})</b>\n\n"
        f"ከትዕዛዞቹ አንዱን በመምረጥ ዝርዝሩን ማየት እና ሁኔታውን መቀየር ይችላሉ፦"
        if lang == "am" else
        f"📦 <b>Order Management (Total: {total_count})</b>\n\n"
        f"Select an order to view details and update production status:"
    )

    markup = get_orders_list_keyboard(orders, status_filter, page, total_pages, lang=lang)
    await callback.answer()
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("view_order:"))
async def view_single_order(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    status_filter = parts[2] if len(parts) > 2 else "all"
    page = int(parts[3]) if len(parts) > 3 else 0

    order = await crud.get_order(session, order_id, business.id)
    if not order:
        await callback.answer("❌ ትዕዛዙ አልተገኘም!" if lang == "am" else "❌ Order not found!")
        return

    status_label = t(f"order_status_{order.status}", lang)
    lines = [
        f"📦 <b>የትዕዛዝ ቁጥር፦ {order.order_number}</b>\n",
        f"👤 <b>የደንበኛ ስም፦</b> {order.customer_name}",
    ]
    if order.customer_phone:
        lines.append(f"📞 <b>ስልክ ቁጥር፦</b> {order.customer_phone}")
    if order.design:
        lines.append(f"👗 <b>የተመረጠ ዲዛይን፦</b> {order.design.name} (ወጪ: {format_currency(order.design.total_cost, lang=lang)})")

    lines.extend([
        f"🏷️ <b>የተስማማው ዋጋ፦</b> {format_currency(order.agreed_price, lang=lang)}",
        f"💵 <b>የቅድመ ክፍያ (Advance)፦</b> {format_currency(order.advance_payment, lang=lang)}",
        f"⏳ <b>ቀሪ ክፍያ (Balance Due)፦</b> <b>{format_currency(order.balance_due, lang=lang)}</b>",
        f"📌 <b>የአሁኑ ሁኔታ፦</b> {status_label}",
        f"📅 <b>የትዕዛዝ ቀን፦</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}",
    ])

    markup = get_order_detail_keyboard(order.id, order.status, status_filter, page, lang=lang)
    await callback.answer()
    await callback.message.edit_text(text="\n".join(lines), reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("set_ord_st:"))
async def update_order_status_handler(
    callback: CallbackQuery,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    # If completing or delivering, record final settlement
    record_final = new_status in ("COMPLETED", "DELIVERED")
    updated = await crud.update_order_status(
        session=session,
        order_id=order_id,
        business_id=business.id,
        new_status=new_status,
        record_final_payment=record_final,
    )

    if not updated:
        await callback.answer("❌ ትዕዛዙ አልተገኘም!" if lang == "am" else "❌ Order not found!")
        return

    status_name = t(f"order_status_{new_status}", lang)
    alert_msg = (
        f"✅ የትዕዛዙ ሁኔታ ወደ '{status_name}' ተቀይሯል!"
        if lang == "am" else
        f"✅ Order status changed to '{status_name}'!"
    )
    await callback.answer(alert_msg, show_alert=True)

    # Re-render order view
    order = await crud.get_order(session, order_id, business.id)
    status_label = t(f"order_status_{order.status}", lang)
    lines = [
        f"📦 <b>የትዕዛዝ ቁጥር፦ {order.order_number}</b>\n",
        f"👤 <b>የደንበኛ ስም፦</b> {order.customer_name}",
        f"🏷️ <b>የተስማማው ዋጋ፦</b> {format_currency(order.agreed_price, lang=lang)}",
        f"💵 <b>የተከፈለ፦</b> {format_currency(order.advance_payment, lang=lang)}",
        f"⏳ <b>ቀሪ ክፍያ፦</b> {format_currency(order.balance_due, lang=lang)}",
        f"📌 <b>የአሁኑ ሁኔታ፦</b> {status_label}",
    ]
    markup = get_order_detail_keyboard(order.id, order.status, "all", 0, lang=lang)
    await callback.message.edit_text(text="\n".join(lines), reply_markup=markup, parse_mode="HTML")

# Create order from a design
@router.callback_query(F.data.startswith("order_create_from:"))
async def start_order_creation_from_design(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    design_id = int(callback.data.split(":")[1])
    design = await crud.get_design(session, design_id, business.id)
    if not design:
        await callback.answer("❌ ዲዛይኑ አልተገኘም!" if lang == "am" else "❌ Design not found!")
        return

    await state.clear()
    await state.update_data(
        target_design_id=design.id,
        suggested_price=str(design.actual_selling_price or design.optimal_price),
        default_customer=design.customer_name or "",
    )

    if design.customer_name:
        await state.update_data(customer_name=design.customer_name)
        await state.set_state(OrderCreationStates.waiting_for_agreed_price)
        prompt = (
            f"📦 <b>ትዕዛዝ መክፈቻ፦ {design.name}</b>\n"
            f"👤 ደንበኛ፦ <b>{design.customer_name}</b>\n\n"
            f"የተስማሙበትን <b>ጠቅላላ መሸጫ ዋጋ በብር</b> ያስገቡ፦\n"
            f"<i>(ተመራጭ ዋጋ፦ {format_currency(design.optimal_price, lang=lang)})</i>"
            if lang == "am" else
            f"📦 <b>Create Order: {design.name}</b>\n"
            f"👤 Customer: <b>{design.customer_name}</b>\n\n"
            f"Enter the <b>Agreed Selling Price in ETB</b>:\n"
            f"<i>(Optimal: {format_currency(design.optimal_price, lang=lang)})</i>"
        )
    else:
        await state.set_state(OrderCreationStates.waiting_for_customer_name)
        prompt = (
            f"📦 <b>ትዕዛዝ መክፈቻ፦ {design.name}</b>\n\n"
            f"እባክዎ የደንበኛውን ስም ያስገቡ፦"
            if lang == "am" else
            f"📦 <b>Create Order: {design.name}</b>\n\n"
            f"Please enter customer name:"
        )

    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(OrderCreationStates.waiting_for_customer_name)
async def process_order_customer(message: Message, state: FSMContext, lang: str):
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("❌ እባክዎ የደንበኛ ስም ያስገቡ፦" if lang == "am" else "❌ Enter customer name:")
        return
    await state.update_data(customer_name=name)
    await state.set_state(OrderCreationStates.waiting_for_agreed_price)
    await message.answer(
        "💰 የተስማሙበትን <b>ጠቅላላ መሸጫ ዋጋ በብር</b> ያስገቡ፦" if lang == "am" else "💰 Enter the agreed selling price in ETB:",
        reply_markup=get_cancel_keyboard(lang),
        parse_mode="HTML",
    )

@router.message(OrderCreationStates.waiting_for_agreed_price)
async def process_order_price(message: Message, state: FSMContext, lang: str):
    try:
        price = to_decimal(message.text)
        if price <= Decimal("0"):
            raise ValueError
    except Exception:
        await message.answer("❌ እባክዎ ትክክለኛ ዋጋ ያስገቡ፦" if lang == "am" else "❌ Enter valid positive price:")
        return
    await state.update_data(agreed_price=str(price))
    await state.set_state(OrderCreationStates.waiting_for_advance)
    prompt = (
        "💵 <b>የቅድመ ክፍያ (Advance Payment)</b> መጠን በብር ያስገቡ፦\n"
        "<i>(ቅድመ ክፍያ ከሌለ 0 ይፃፉ)</i>"
        if lang == "am" else
        "💵 Enter <b>Advance Payment amount in ETB</b>:\n"
        "<i>(Type 0 if none)</i>"
    )
    await message.answer(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(OrderCreationStates.waiting_for_advance)
async def process_order_advance(message: Message, state: FSMContext, lang: str):
    try:
        advance = to_decimal(message.text)
        if advance < Decimal("0"):
            raise ValueError
    except Exception:
        await message.answer("❌ እባክዎ ትክክለኛ ያልአሉታዊ ቁጥር ያስገቡ፦" if lang == "am" else "❌ Enter non-negative amount:")
        return
    await state.update_data(advance_payment=str(advance))
    await state.set_state(OrderCreationStates.waiting_for_phone)
    prompt = (
        "📞 የደንበኛውን <b>ስልክ ቁጥር</b> ያስገቡ፦\n"
        "<i>(ካልፈለጉ 0 ወይም '-' ይፃፉ)</i>"
        if lang == "am" else
        "📞 Enter <b>Customer Phone Number</b>:\n"
        "<i>(Or type '-' to skip)</i>"
    )
    await message.answer(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(OrderCreationStates.waiting_for_phone)
async def process_order_finish(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    phone_raw = message.text.strip() if message.text else ""
    phone = None if phone_raw in ("0", "-", "") else phone_raw
    data = await state.get_data()
    await state.clear()

    design_id = data.get("target_design_id")
    customer_name = data.get("customer_name", "Customer")
    agreed_price = Decimal(data["agreed_price"])
    advance_payment = Decimal(data["advance_payment"])

    order = await crud.create_order_from_design(
        session=session,
        business_id=business.id,
        design_id=design_id,
        customer_name=customer_name,
        agreed_price=agreed_price,
        customer_phone=phone,
        advance_payment=advance_payment,
    )

    lines = [
        f"✅ <b>ትዕዛዝ #{order.order_number} በተሳካ ሁኔታ ተከፍቷል!</b>\n" if lang == "am" else f"✅ <b>Order #{order.order_number} Created Successfully!</b>\n",
        f"👤 <b>ደንበኛ፦</b> {order.customer_name}",
        f"🏷️ <b>የተስማማው ዋጋ፦</b> {format_currency(order.agreed_price, lang=lang)}",
        f"💵 <b>የቅድመ ክፍያ፦</b> {format_currency(order.advance_payment, lang=lang)}",
        f"⏳ <b>ቀሪ ክፍያ፦</b> <b>{format_currency(order.balance_due, lang=lang)}</b>",
        f"📌 <b>ሁኔታ፦</b> ⏳ በመጠባበቅ ላይ (PENDING)",
    ]

    markup = get_order_detail_keyboard(order.id, order.status, "all", 0, lang=lang)
    await message.answer(text="\n".join(lines), reply_markup=markup, parse_mode="HTML")
