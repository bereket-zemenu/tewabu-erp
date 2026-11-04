"""
New Clothing Design Guided Workflow for Tewabu ERP.
Guides the tailor house owner step-by-step through:
1. Gender selection (👨 ወንድ / 👩 ሴት)
2. Clothing item selection (ቲሸርት ተከፋች/ያለተከፋች፣ ጃኬት፣ ሱሪ፣ የሀበሻ ቀሚስ...)
3. Item-specific custom measurements collection (ቶፕ፣ ትከሻ፣ ደረት፣ ወገብ፣ እጅ፣ ቁመት፣ ዳሌ፣ ጡት፣ አንገት)
4. Reference photo upload (optional)
5. Customer name (optional)
6. 6 Standard guided expenses + optional extras
7. Target profit margin configuration & optimal price calculation
8. Actual selling price & profit/loss status
9. Delivery date selection & 5-day prior delivery reminder activation
10. Done audio chime & final visual summary
"""

import json
import logging
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Business
import database.crud as crud
from localization.i18n import t
from core.calculations import (
    calculate_design_financials,
    to_decimal,
    format_currency,
    validate_margin,
)
from core.constants import ProfitStatus
from keyboards.inline import (
    get_gender_keyboard,
    get_male_clothing_keyboard,
    get_female_clothing_keyboard,
    get_neck_style_keyboard,
    get_due_date_keyboard,
    get_step_nav_keyboard,
    get_extra_expenses_keyboard,
    get_margin_choice_keyboard,
    get_actual_price_keyboard,
    get_design_result_keyboard,
)
from services.audio_service import get_chime_bytes

logger = logging.getLogger("tewabu_erp.new_design")
router = Router(name="new_design")

class NewDesignStates(StatesGroup):
    waiting_for_gender = State()
    waiting_for_male_item = State()
    waiting_for_female_item = State()
    waiting_for_measurement = State()
    waiting_for_design_photo = State()
    waiting_for_customer_name = State()
    waiting_for_expense_menen = State()
    waiting_for_expense_thread = State()
    waiting_for_expense_embroidery = State()
    waiting_for_expense_sewing = State()
    waiting_for_expense_designer = State()
    waiting_for_expense_related = State()
    waiting_for_extra_choice = State()
    waiting_for_extra_name = State()
    waiting_for_extra_amount = State()
    waiting_for_target_margin = State()
    waiting_for_actual_selling_price = State()
    waiting_for_due_date = State()

MEASUREMENT_LABELS = {
    "ቶፕ": {"en": "Top Length", "am": "ቶፕ"},
    "ትከሻ": {"en": "Shoulder", "am": "ትከሻ"},
    "ደረት": {"en": "Chest", "am": "ደረት"},
    "ወገብ": {"en": "Waist", "am": "ወገብ"},
    "እጅ": {"en": "Sleeve / Arm", "am": "እጅ"},
    "ቁመት": {"en": "Full Length", "am": "ቁመት"},
    "ዳሌ": {"en": "Hip", "am": "ዳሌ"},
    "ጡት": {"en": "Bust / Breast", "am": "ጡት"},
    "አንገት": {"en": "Neck Style", "am": "አንገት"},
}

MALE_TOP_ITEMS = {
    "tshirt_open": "ቲሸርት (ተከፋች)",
    "tshirt_closed": "ቲሸርት (ያለተከፋች)",
    "jacket": "ጃኬት",
}

FEMALE_ITEM_MAP = {
    "habesha_dress": "የሀበሻ ቀሚስ",
    "full_dress": "ሙሉ ቀሚስ",
    "top_skirt": "ቶፕ እና ቀሚስ",
    "shirt_top": "ሸሚዝ / ቶፕ",
}

# ==========================================
# 1. Entry Point: Gender Selection
# ==========================================
@router.callback_query(F.data == "nav_new_design")
async def start_new_design_workflow(callback: CallbackQuery, state: FSMContext, lang: str):
    """Step 1: Choose Male or Female."""
    await state.clear()
    await state.update_data(
        expenses_dict={},
        extra_expenses=[],
        measurements_dict={},
    )
    await state.set_state(NewDesignStates.waiting_for_gender)
    await callback.answer()
    
    text = (
        "👤 <b>ደረጃ 1፦ የልብስ ዓይነት ይምረጡ (ጾታ)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "እባክዎ የደንበኛውን ጾታ ይምረጡ፦\n\n"
        "<i>(Please select customer gender to proceed with tailored measurements)</i>"
        if lang == "am" else
        "👤 <b>Step 1: Select Gender</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Please choose customer gender:"
    )
    await callback.message.edit_text(text=text, reply_markup=get_gender_keyboard(lang), parse_mode="HTML")

# ==========================================
# 2. Gender Handlers & Clothing Item Selection
# ==========================================
@router.callback_query(F.data == "gender_choice:MALE")
async def process_gender_male(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(gender="MALE")
    await state.set_state(NewDesignStates.waiting_for_male_item)
    await callback.answer()

    text = (
        "👔 <b>የወንድ ልብስ ዓይነት ይምረጡ፦</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. 👕 ቲሸርት (ተከፋች)\n"
        "2. 👕 ቲሸርት (ያለተከፋች)\n"
        "3. 🧥 ጃኬት\n"
        "4. 👖 ሱሪ\n\n"
        "ከታች ካሉት አዝራሮች አንዱን ይጫኑ፦"
        if lang == "am" else
        "👔 <b>Select Male Garment Type:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. Open T-Shirt\n"
        "2. Closed T-Shirt\n"
        "3. Jacket\n"
        "4. Pants / Trousers"
    )
    await callback.message.edit_text(text=text, reply_markup=get_male_clothing_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data == "gender_choice:FEMALE")
async def process_gender_female(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(gender="FEMALE")
    await state.set_state(NewDesignStates.waiting_for_female_item)
    await callback.answer()

    text = (
        "👗 <b>የሴት ልብስ ዓይነት ይምረጡ ወይም ስም ይጻፉ፦</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ከታች ካሉት አማራጮች አንዱን ይምረጡ ወይም የዲዛይኑን ስም በጽሁፍ ይላኩ፦"
        if lang == "am" else
        "👗 <b>Select Female Garment Type or type name:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Choose an option below or type the custom dress name:"
    )
    await callback.message.edit_text(text=text, reply_markup=get_female_clothing_keyboard(lang), parse_mode="HTML")

# Male item selection
@router.callback_query(NewDesignStates.waiting_for_male_item, F.data.startswith("male_item:"))
async def process_male_item_choice(callback: CallbackQuery, state: FSMContext, lang: str):
    item_code = callback.data.split(":")[1]
    if item_code == "pants":
        item_name = "ሱሪ"
        # Pants measurements: ቁመት, ወገብ, ዳሌ
        keys = ["ቁመት", "ወገብ", "ዳሌ"]
    else:
        item_name = MALE_TOP_ITEMS.get(item_code, "ቲሸርት (ተከፋች)")
        # 1 to 3 measurements: ቶፕ, ትከሻ, ደረት, ወገብ, እጅ
        keys = ["ቶፕ", "ትከሻ", "ደረት", "ወገብ", "እጅ"]

    await state.update_data(
        clothing_item=item_name,
        design_name=f"የወንድ {item_name}",
        measurement_keys=keys,
        measurement_idx=0,
        measurements_dict={},
    )
    await callback.answer()
    await show_current_measurement_prompt(callback, state, lang, edit_existing=True)

# Female item selection (via inline button or text)
@router.callback_query(NewDesignStates.waiting_for_female_item, F.data.startswith("female_item:"))
async def process_female_item_cb(callback: CallbackQuery, state: FSMContext, lang: str):
    item_code = callback.data.split(":")[1]
    item_name = FEMALE_ITEM_MAP.get(item_code, "የሀበሻ ቀሚስ")
    keys = ["ቶፕ", "ቁመት", "ወገብ", "ጡት", "ትከሻ", "እጅ", "አንገት"]

    await state.update_data(
        clothing_item=item_name,
        design_name=f"የሴት {item_name}",
        measurement_keys=keys,
        measurement_idx=0,
        measurements_dict={},
    )
    await callback.answer()
    await show_current_measurement_prompt(callback, state, lang, edit_existing=True)

@router.message(NewDesignStates.waiting_for_female_item)
async def process_female_item_text(message: Message, state: FSMContext, lang: str):
    name = message.text.strip() if message.text else "የሴት ልብስ"
    keys = ["ቶፕ", "ቁመት", "ወገብ", "ጡት", "ትከሻ", "እጅ", "አንገት"]

    await state.update_data(
        clothing_item=name,
        design_name=name,
        measurement_keys=keys,
        measurement_idx=0,
        measurements_dict={},
    )
    await show_current_measurement_prompt(message, state, lang, edit_existing=False)

# ==========================================
# 3. Measurement Workflow (Prompt & Handlers)
# ==========================================
async def show_current_measurement_prompt(
    event: Message | CallbackQuery,
    state: FSMContext,
    lang: str,
    edit_existing: bool = False,
):
    await state.set_state(NewDesignStates.waiting_for_measurement)
    data = await state.get_data()
    keys = data.get("measurement_keys", [])
    idx = data.get("measurement_idx", 0)

    # When all measurements are collected, transition to photo
    if idx >= len(keys):
        await state.set_state(NewDesignStates.waiting_for_design_photo)
        photo_prompt = (
            "📸 <b>ደረጃ 3፦ የዲዛይኑን ፎቶ/ምስል ይላኩ (Optional Photo)</b>\n\n"
            "የልብሱን ንድፍ ወይም ሞዴል ፎቶ መላክ ይችላሉ፤ ፎቶ ከሌለዎት ከታች <b>'⏭️ ዝለል (Skip)'</b> የሚለውን ይጫኑ፦\n\n"
            "<i>(Send a reference photo of the dress, or click 'Skip')</i>"
            if lang == "am" else
            "📸 <b>Step 3: Upload Design Photo (Optional)</b>\n\n"
            "You can upload a reference photo of the garment, or click <b>'Skip'</b> below:"
        )
        markup = get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="design_photo")
        if edit_existing and isinstance(event, CallbackQuery):
            await event.message.edit_text(text=photo_prompt, reply_markup=markup, parse_mode="HTML")
        elif isinstance(event, Message):
            await event.answer(text=photo_prompt, reply_markup=markup, parse_mode="HTML")
        else:
            await event.message.edit_text(text=photo_prompt, reply_markup=markup, parse_mode="HTML")
        return

    key = keys[idx]
    total = len(keys)
    step_num = idx + 1
    en_label = MEASUREMENT_LABELS.get(key, {}).get("en", key)

    if key == "አንገት":
        prompt = (
            f"📏 <b>የልኬት ምዝገባ ({step_num}/{total})፦ አንገት (Neck Style / Cut)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>ይህ ምርጫ የጽሁፍ ምርጫ ነው (Text option)።</i>\n\n"
            f"ከታች ካሉት ቅድመ-ምርጫዎች አንዱን መምረጥ ወይም የአንገቱን ዲዛይን ጽፈው መላክ ይችላሉ፦\n"
            f"<i>(ምሳሌ፦ ክብ፣ V-አንገት፣ ካሬ፣ ኮላ/ቆሌት...)</i>"
            if lang == "am" else
            f"📏 <b>Measurement ({step_num}/{total}): Neck Style</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>This option is text input.</i>\n"
            f"Select a style below or type any custom neck design:"
        )
        markup = get_neck_style_keyboard(lang)
    else:
        prompt = (
            f"📏 <b>የልኬት ምዝገባ ({step_num}/{total})፦ {key} ({en_label})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"እባክዎ የ<b>{key}</b> ልኬት በ ሴ.ሜ (cm) ወይም ኢንች (inch) ያስገቡ፦\n"
            f"<i>(ምሳሌ፦ 42 ወይም 38.5)</i>\n\n"
            f"ካላስፈለገ '⏭️ ዝለል'ን ይጫኑ፦"
            if lang == "am" else
            f"📏 <b>Measurement ({step_num}/{total}): {en_label}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Please enter <b>{en_label}</b> measurement in cm or inches:\n"
            f"<i>(e.g., 42 or 38.5)</i>"
        )
        buttons = [
            [
                InlineKeyboardButton(text=t("btn_skip", lang), callback_data="step_skip:measurement"),
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:measurement"),
            ],
            [
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
            ],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if edit_existing and isinstance(event, CallbackQuery):
        await event.message.edit_text(text=prompt, reply_markup=markup, parse_mode="HTML")
    elif isinstance(event, Message):
        await event.answer(text=prompt, reply_markup=markup, parse_mode="HTML")
    else:
        await event.message.edit_text(text=prompt, reply_markup=markup, parse_mode="HTML")

# Handle neck style quick button
@router.callback_query(NewDesignStates.waiting_for_measurement, F.data.startswith("neck_style:"))
async def process_neck_style_cb(callback: CallbackQuery, state: FSMContext, lang: str):
    style = callback.data.split(":", 1)[1]
    data = await state.get_data()
    m_dict = data.get("measurements_dict", {})
    m_dict["አንገት"] = style
    idx = data.get("measurement_idx", 0) + 1

    await state.update_data(measurements_dict=m_dict, measurement_idx=idx)
    await callback.answer(f"✅ አንገት፦ {style}")
    await show_current_measurement_prompt(callback, state, lang, edit_existing=True)

# Handle skip measurement
@router.callback_query(NewDesignStates.waiting_for_measurement, F.data == "step_skip:measurement")
async def skip_measurement(callback: CallbackQuery, state: FSMContext, lang: str):
    data = await state.get_data()
    idx = data.get("measurement_idx", 0) + 1
    await state.update_data(measurement_idx=idx)
    await callback.answer()
    await show_current_measurement_prompt(callback, state, lang, edit_existing=True)

# Handle back measurement
@router.callback_query(NewDesignStates.waiting_for_measurement, F.data == "step_back:measurement")
async def back_measurement(callback: CallbackQuery, state: FSMContext, lang: str):
    data = await state.get_data()
    idx = data.get("measurement_idx", 0)
    await callback.answer()
    if idx > 0:
        await state.update_data(measurement_idx=idx - 1)
        await show_current_measurement_prompt(callback, state, lang, edit_existing=True)
    else:
        # Step back to clothing item selection
        gender = data.get("gender")
        if gender == "MALE":
            await state.set_state(NewDesignStates.waiting_for_male_item)
            await callback.message.edit_text(
                text="👔 <b>የወንድ ልብስ ዓይነት ይምረጡ፦</b>",
                reply_markup=get_male_clothing_keyboard(lang),
                parse_mode="HTML",
            )
        else:
            await state.set_state(NewDesignStates.waiting_for_female_item)
            await callback.message.edit_text(
                text="👗 <b>የሴት ልብስ ዓይነት ይምረጡ ወይም ስም ይጻፉ፦</b>",
                reply_markup=get_female_clothing_keyboard(lang),
                parse_mode="HTML",
            )

# Handle text input for measurement (numbers or neck style string)
@router.message(NewDesignStates.waiting_for_measurement)
async def process_measurement_text(message: Message, state: FSMContext, lang: str):
    val = message.text.strip() if message.text else ""
    if not val:
        return

    data = await state.get_data()
    keys = data.get("measurement_keys", [])
    idx = data.get("measurement_idx", 0)

    if idx < len(keys):
        current_key = keys[idx]
        m_dict = data.get("measurements_dict", {})
        m_dict[current_key] = val
        await state.update_data(measurements_dict=m_dict, measurement_idx=idx + 1)

    await show_current_measurement_prompt(message, state, lang, edit_existing=False)

# ==========================================
# 4. Photo & Customer Name Handlers
# ==========================================
@router.message(NewDesignStates.waiting_for_design_photo, F.photo)
async def process_design_photo(message: Message, state: FSMContext, lang: str):
    photo_id = message.photo[-1].file_id
    await state.update_data(image_file_id=photo_id)
    await state.set_state(NewDesignStates.waiting_for_customer_name)
    await message.answer(
        text=f"✅ ፎቶው ተይዟል!\n\n{t('step_customer_name', lang)}" if lang == "am" else f"✅ Photo attached!\n\n{t('step_customer_name', lang)}",
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="customer_name"),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "step_skip:design_photo")
async def skip_design_photo(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(image_file_id=None)
    await state.set_state(NewDesignStates.waiting_for_customer_name)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_customer_name", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="customer_name"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_design_photo)
async def process_invalid_design_photo(message: Message, state: FSMContext, lang: str):
    await message.answer(
        "📸 እባክዎ ፎቶ ይላኩ ወይም ፎቶ ከሌለዎት ከታች <b>'⏭️ ዝለል (Skip)'</b> የሚለውን ይጫኑ፦"
        if lang == "am" else
        "📸 Please send a photo or click <b>'Skip'</b> below:",
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="design_photo"),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "step_skip:customer_name")
async def skip_customer_name(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(customer_name=None)
    await state.set_state(NewDesignStates.waiting_for_expense_menen)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_menen_gever", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="menen"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_customer_name)
async def process_customer_name(message: Message, state: FSMContext, lang: str):
    cust = message.text.strip() if message.text else ""
    await state.update_data(customer_name=cust if cust else None)
    await state.set_state(NewDesignStates.waiting_for_expense_menen)
    await message.answer(
        text=t("step_expense_menen_gever", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="menen"),
        parse_mode="HTML",
    )

# ==========================================
# 5. 6 Standard Guided Expenses Flow
# ==========================================
# 1. Menen & Gever
@router.callback_query(F.data == "step_skip:menen")
async def skip_menen_expense(callback: CallbackQuery, state: FSMContext, lang: str):
    await save_standard_expense(state, "menen_gever", "መነን & ገቨር", Decimal("0.00"))
    await state.set_state(NewDesignStates.waiting_for_expense_thread)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_thread", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="thread"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_expense_menen)
async def process_menen_expense(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="menen"))
        return
    await save_standard_expense(state, "menen_gever", "መነን & ገቨር", amount)
    await state.set_state(NewDesignStates.waiting_for_expense_thread)
    await message.answer(
        text=t("step_expense_thread", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="thread"),
        parse_mode="HTML",
    )

# 2. Thread
@router.callback_query(F.data == "step_skip:thread")
async def skip_thread_expense(callback: CallbackQuery, state: FSMContext, lang: str):
    await save_standard_expense(state, "thread", "ክር", Decimal("0.00"))
    await state.set_state(NewDesignStates.waiting_for_expense_embroidery)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_embroidery", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="embroidery"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_expense_thread)
async def process_thread_expense(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="thread"))
        return
    await save_standard_expense(state, "thread", "ክር", amount)
    await state.set_state(NewDesignStates.waiting_for_expense_embroidery)
    await message.answer(
        text=t("step_expense_embroidery", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="embroidery"),
        parse_mode="HTML",
    )

# 3. Embroidery (ጠላፊ)
@router.callback_query(F.data == "step_skip:embroidery")
async def skip_embroidery_expense(callback: CallbackQuery, state: FSMContext, lang: str):
    await save_standard_expense(state, "embroidery", "ጠላፊ", Decimal("0.00"))
    await state.set_state(NewDesignStates.waiting_for_expense_sewing)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_sewing", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="sewing"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_expense_embroidery)
async def process_embroidery_expense(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="embroidery"))
        return
    await save_standard_expense(state, "embroidery", "ጠላፊ", amount)
    await state.set_state(NewDesignStates.waiting_for_expense_sewing)
    await message.answer(
        text=t("step_expense_sewing", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="sewing"),
        parse_mode="HTML",
    )

# 4. Sewing (ሰፊ)
@router.callback_query(F.data == "step_skip:sewing")
async def skip_sewing_expense(callback: CallbackQuery, state: FSMContext, lang: str):
    await save_standard_expense(state, "sewing", "ሰፊ", Decimal("0.00"))
    await state.set_state(NewDesignStates.waiting_for_expense_designer)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_designer", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="designer"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_expense_sewing)
async def process_sewing_expense(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="sewing"))
        return
    await save_standard_expense(state, "sewing", "ሰፊ", amount)
    await state.set_state(NewDesignStates.waiting_for_expense_designer)
    await message.answer(
        text=t("step_expense_designer", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="designer"),
        parse_mode="HTML",
    )

# 5. Designer (ዲዛይነር)
@router.callback_query(F.data == "step_skip:designer")
async def skip_designer_expense(callback: CallbackQuery, state: FSMContext, lang: str):
    await save_standard_expense(state, "designer", "ዲዛይነር", Decimal("0.00"))
    await state.set_state(NewDesignStates.waiting_for_expense_related)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_expense_related", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="related"),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_expense_designer)
async def process_designer_expense(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="designer"))
        return
    await save_standard_expense(state, "designer", "ዲዛይነር", amount)
    await state.set_state(NewDesignStates.waiting_for_expense_related)
    await message.answer(
        text=t("step_expense_related", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="related"),
        parse_mode="HTML",
    )

# 6. Related Expenses (ተያያዥ ወጪ)
@router.callback_query(F.data == "step_skip:related")
async def skip_related_expense(callback: CallbackQuery, state: FSMContext, business: Business, lang: str):
    await save_standard_expense(state, "related_expenses", "ተያያዥ ወጪ", Decimal("0.00"))
    await callback.answer()
    await show_extra_choice_screen(callback.message, state, lang, edit_existing=True)

@router.message(NewDesignStates.waiting_for_expense_related)
async def process_related_expense(message: Message, state: FSMContext, business: Business, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="related"))
        return
    await save_standard_expense(state, "related_expenses", "ተያያዥ ወጪ", amount)
    await show_extra_choice_screen(message, state, lang, edit_existing=False)

# Extra expenses prompt
async def show_extra_choice_screen(
    event: Message | CallbackQuery,
    state: FSMContext,
    lang: str,
    edit_existing: bool = False,
):
    await state.set_state(NewDesignStates.waiting_for_extra_choice)
    data = await state.get_data()
    summary = build_expenses_summary_text(data, lang)
    prompt = (
        f"{summary}\n\n"
        f"<b>ተጨማሪ ልዩ ወጪ አለዎት?</b>\n"
        f"<i>(ተጨማሪ ወጪ ከሌለ <b>'🧮 ወጪ አስላ (Calculate Costs)'</b> የሚለውን ይጫኑ፤ ካለ ደግሞ '➕ ተጨማሪ ወጪ'ን ይጫኑ)</i>"
        if lang == "am" else
        f"{summary}\n\n"
        f"<b>Do you have extra expenses?</b>\n"
        f"<i>(If none, click <b>'🧮 Calculate Costs'</b> to proceed, or '➕ Add Extra')</i>"
    )
    markup = get_extra_expenses_keyboard(lang)
    if edit_existing and isinstance(event, Message):
        await event.edit_text(text=prompt, reply_markup=markup, parse_mode="HTML")
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(text=prompt, reply_markup=markup, parse_mode="HTML")
    else:
        await event.answer(text=prompt, reply_markup=markup, parse_mode="HTML")

# Step Back Navigation
@router.callback_query(F.data.startswith("step_back:"))
async def handle_step_back(callback: CallbackQuery, state: FSMContext, business: Business, lang: str):
    step_key = callback.data.split(":")[1]
    await callback.answer()

    if step_key == "gender":
        await state.set_state(NewDesignStates.waiting_for_gender)
        await callback.message.edit_text(
            text="👤 <b>ደረጃ 1፦ የልብስ ዓይነት ይምረጡ (ጾታ)</b>",
            reply_markup=get_gender_keyboard(lang),
            parse_mode="HTML",
        )
    elif step_key == "design_photo":
        # Back to last measurement
        data = await state.get_data()
        keys = data.get("measurement_keys", [])
        if keys:
            await state.update_data(measurement_idx=len(keys) - 1)
            await show_current_measurement_prompt(callback, state, lang, edit_existing=True)
        else:
            await state.set_state(NewDesignStates.waiting_for_gender)
            await callback.message.edit_text(
                text="👤 <b>ደረጃ 1፦ የልብስ ዓይነት ይምረጡ (ጾታ)</b>",
                reply_markup=get_gender_keyboard(lang),
                parse_mode="HTML",
            )
    elif step_key == "customer_name":
        await state.set_state(NewDesignStates.waiting_for_design_photo)
        photo_prompt = (
            "📸 <b>ደረጃ 3፦ የዲዛይኑን ፎቶ/ምስል ይላኩ (Optional Photo)</b>\n\n"
            "የልብሱን ንድፍ ወይም ሞዴል ፎቶ መላክ ይችላሉ፤ ፎቶ ከሌለዎት ከታች <b>'⏭️ ዝለል (Skip)'</b> የሚለውን ይጫኑ፦"
            if lang == "am" else
            "📸 <b>Step 3: Upload Design Photo (Optional)</b>\n\n"
            "You can upload a reference photo of the garment, or click <b>'Skip'</b> below:"
        )
        await callback.message.edit_text(
            text=photo_prompt,
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="design_photo"),
            parse_mode="HTML",
        )
    elif step_key == "menen":
        await state.set_state(NewDesignStates.waiting_for_customer_name)
        await callback.message.edit_text(
            text=t("step_customer_name", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="customer_name"),
            parse_mode="HTML",
        )
    elif step_key == "thread":
        await state.set_state(NewDesignStates.waiting_for_expense_menen)
        await callback.message.edit_text(
            text=t("step_expense_menen_gever", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="menen"),
            parse_mode="HTML",
        )
    elif step_key == "embroidery":
        await state.set_state(NewDesignStates.waiting_for_expense_thread)
        await callback.message.edit_text(
            text=t("step_expense_thread", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="thread"),
            parse_mode="HTML",
        )
    elif step_key == "sewing":
        await state.set_state(NewDesignStates.waiting_for_expense_embroidery)
        await callback.message.edit_text(
            text=t("step_expense_embroidery", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="embroidery"),
            parse_mode="HTML",
        )
    elif step_key == "designer":
        await state.set_state(NewDesignStates.waiting_for_expense_sewing)
        await callback.message.edit_text(
            text=t("step_expense_sewing", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="sewing"),
            parse_mode="HTML",
        )
    elif step_key == "related":
        await state.set_state(NewDesignStates.waiting_for_expense_designer)
        await callback.message.edit_text(
            text=t("step_expense_designer", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="designer"),
            parse_mode="HTML",
        )
    elif step_key == "extra_choice":
        await state.set_state(NewDesignStates.waiting_for_expense_related)
        await callback.message.edit_text(
            text=t("step_expense_related", lang),
            reply_markup=get_step_nav_keyboard(lang, show_skip=True, show_back=True, step_key="related"),
            parse_mode="HTML",
        )
    elif step_key == "due_date":
        data = await state.get_data()
        margin = Decimal(data.get("target_margin_val", "0.25"))
        await calculate_and_prompt_actual_price(callback.message, state, margin, lang, is_edit=True)

@router.callback_query(F.data == "extra_add")
async def ask_extra_expense_name(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(NewDesignStates.waiting_for_extra_name)
    await callback.answer()
    await callback.message.edit_text(
        text=t("step_extra_expense_name", lang),
        reply_markup=get_step_nav_keyboard(lang, show_skip=False, show_back=False),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_extra_name)
async def process_extra_expense_name(message: Message, state: FSMContext, lang: str):
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("❌ እባክዎ የወጪውን ስም ያስገቡ፦" if lang == "am" else "❌ Enter expense name:")
        return
    await state.update_data(current_extra_name=name)
    await state.set_state(NewDesignStates.waiting_for_extra_amount)
    await message.answer(
        text=t("step_extra_expense_amount", lang, name=name),
        reply_markup=get_step_nav_keyboard(lang, show_skip=False, show_back=False),
        parse_mode="HTML",
    )

@router.message(NewDesignStates.waiting_for_extra_amount)
async def process_extra_expense_amount(message: Message, state: FSMContext, lang: str):
    amount = parse_positive_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang))
        return
    data = await state.get_data()
    name = data.get("current_extra_name", "Extra")
    extras = data.get("extra_expenses", [])
    extras.append({
        "category_key": "custom",
        "category_name": name,
        "amount": amount,
        "is_custom": True,
    })
    await state.update_data(extra_expenses=extras)
    await show_extra_choice_screen(message, state, lang)

@router.callback_query(F.data == "extra_finish")
async def finish_expenses_and_prompt_margin(callback: CallbackQuery, state: FSMContext, business: Business, lang: str):
    """Step: Show complete breakdown and ask for target profit margin."""
    await state.set_state(NewDesignStates.waiting_for_target_margin)
    data = await state.get_data()
    default_margin = business.default_profit_margin or Decimal("0.25")
    margin_pct = int(default_margin * 100)

    summary = build_expenses_summary_text(data, lang)
    prompt = (
        f"{summary}\n\n"
        f"{t('step_target_margin', lang, default_margin=margin_pct)}"
    )
    await callback.answer()
    await callback.message.edit_text(
        text=prompt,
        reply_markup=get_margin_choice_keyboard(default_margin, lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("use_default_margin:"))
async def process_default_margin_cb(callback: CallbackQuery, state: FSMContext, business: Business, lang: str):
    default_margin = business.default_profit_margin or Decimal("0.25")
    await calculate_and_prompt_actual_price(callback.message, state, default_margin, lang, is_edit=True)
    await callback.answer()

@router.message(NewDesignStates.waiting_for_target_margin)
async def process_custom_margin(message: Message, state: FSMContext, lang: str):
    try:
        margin = validate_margin(message.text)
    except ValueError:
        await message.answer(t("err_invalid_margin", lang))
        return

    await calculate_and_prompt_actual_price(message, state, margin, lang, is_edit=False)

# ==========================================
# 6. Pricing & Delivery Date
# ==========================================
async def calculate_and_prompt_actual_price(
    msg: Message,
    state: FSMContext,
    target_margin: Decimal,
    lang: str,
    is_edit: bool = False,
):
    await state.set_state(NewDesignStates.waiting_for_actual_selling_price)
    data = await state.get_data()

    all_expenses_list = collect_all_expenses_list(data)
    amounts = [e["amount"] for e in all_expenses_list]

    calc = calculate_design_financials(expenses=amounts, target_margin=target_margin)
    await state.update_data(
        calc_result_dict=calc.to_dict(),
        target_margin_val=str(target_margin),
    )

    margin_pct = int(target_margin * 100)
    text = (
        f"📊 <b>የወጪ እና ተመራጭ መሸጫ ዋጋ ስሌት</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• የዲዛይን ስም፦ <b>{data.get('design_name')}</b>\n"
        f"• አጠቃላይ የምርት ወጪ (Total Cost)፦ <b>{format_currency(calc.total_cost, lang=lang)}</b>\n"
        f"• ወጪ መሸፈኛ ዋጋ (Break-even Price)፦ <b>{format_currency(calc.break_even_price, lang=lang)}</b>\n"
        f"• የታለመው ትርፍ መቶኛ፦ <b>{margin_pct}%</b>\n\n"
        f"🪙 <b>ተመራጭ መሸጫ ዋጋ (OPTIMAL PRICE)፦</b>\n"
        f"👉 <b><u>{format_currency(calc.optimal_price, lang=lang)}</u></b>\n"
        f"<i>(ይህ ወርቃማ ዋጋ የታለመውን {margin_pct}% ትርፍ ሙሉ በሙሉ ያስገኝልዎታል)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{t('step_actual_selling_price', lang)}"
        if lang == "am" else
        f"📊 <b>Cost & Optimal Price Analysis</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• Design Name: <b>{data.get('design_name')}</b>\n"
        f"• Total Production Cost: <b>{format_currency(calc.total_cost, lang=lang)}</b>\n"
        f"• Break-even Price: <b>{format_currency(calc.break_even_price, lang=lang)}</b>\n"
        f"• Target Profit Margin: <b>{margin_pct}%</b>\n\n"
        f"🪙 <b>RECOMMENDED OPTIMAL PRICE:</b>\n"
        f"👉 <b><u>{format_currency(calc.optimal_price, lang=lang)}</u></b>\n"
        f"<i>(Guarantees full achievement of your {margin_pct}% target margin)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{t('step_actual_selling_price', lang)}"
    )

    if is_edit:
        await msg.edit_text(text=text, reply_markup=get_actual_price_keyboard(lang), parse_mode="HTML")
    else:
        await msg.answer(text=text, reply_markup=get_actual_price_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data == "skip_actual_price")
async def skip_actual_selling_price(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
):
    await callback.answer()
    await prompt_delivery_date(callback.message, state, lang, actual_price=None, is_edit=True)

@router.message(NewDesignStates.waiting_for_actual_selling_price)
async def process_actual_selling_price(
    message: Message,
    state: FSMContext,
    lang: str,
):
    price = parse_positive_amount(message.text)
    if price is None:
        await message.answer(t("err_invalid_amount", lang), reply_markup=get_actual_price_keyboard(lang))
        return
    await prompt_delivery_date(message, state, lang, actual_price=price, is_edit=False)

# Prompt for Delivery Date
async def prompt_delivery_date(
    msg: Message,
    state: FSMContext,
    lang: str,
    actual_price: Optional[Decimal],
    is_edit: bool = False,
):
    await state.set_state(NewDesignStates.waiting_for_due_date)
    await state.update_data(actual_selling_price_val=str(actual_price) if actual_price is not None else None)

    prompt = (
        "📅 <b>ደረጃ 9፦ የማስረከቢያ ቀን (Delivery Date)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ይህ ልብስ ለደንበኛ የሚደርስበትን ቀን ያስገቡ፦\n"
        "• የስንት ቀን ውስጥ እንደሆነ ቁጥር ብቻ ማስገባት ይችላሉ (ምሳሌ፦ <code>7</code>)\n"
        "• ወይም በ ቀን (ምሳሌ፦ <code>2026-11-20</code>)\n"
        "• ቀኑ ካልታወቀ ከታች <b>'⏭️ ዝለል (Skip)'</b> የሚለውን ይጫኑ፦\n\n"
        "🔔 <i>(ማሳሰቢያ፦ ቀኑ ከመድረሱ 5 ቀን በፊት ቦቱ የማስጠንቀቂያ መልዕክት ይልክልዎታል!)</i>"
        if lang == "am" else
        "📅 <b>Step 9: Delivery Date</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Enter delivery deadline for this garment:\n"
        "• Enter number of days (e.g. <code>7</code>)\n"
        "• Or enter ISO date (e.g. <code>2026-11-20</code>)\n"
        "• Or click <b>'Skip'</b> below:\n\n"
        "🔔 <i>(The bot will alert you 5 days before delivery!)</i>"
    )
    markup = get_due_date_keyboard(lang)
    if is_edit:
        await msg.edit_text(text=prompt, reply_markup=markup, parse_mode="HTML")
    else:
        await msg.answer(text=prompt, reply_markup=markup, parse_mode="HTML")

@router.callback_query(NewDesignStates.waiting_for_due_date, F.data.startswith("due_days:"))
async def process_due_days_cb(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    days = int(callback.data.split(":")[1])
    target_due = date.today() + timedelta(days=days)
    await callback.answer(f"✅ {days} ቀናት")
    await finalize_and_save_design(callback.message, state, business, session, lang, due_date=target_due, is_edit=True)

@router.callback_query(NewDesignStates.waiting_for_due_date, F.data == "step_skip:due_date")
async def skip_due_date_cb(
    callback: CallbackQuery,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    await callback.answer()
    await finalize_and_save_design(callback.message, state, business, session, lang, due_date=None, is_edit=True)

@router.message(NewDesignStates.waiting_for_due_date)
async def process_due_date_text(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    due_date = parse_delivery_date(message.text)
    if due_date is None:
        await message.answer(
            "❌ እባክዎ ትክክለኛ የቀን ብዛት (ምሳሌ፦ '7') ወይም ቀን (YYYY-MM-DD) ያስገቡ፤ ወይም 'ዝለል'ን ይጫኑ፦"
            if lang == "am" else
            "❌ Please enter valid number of days (e.g. '7') or date (YYYY-MM-DD), or click Skip:",
            reply_markup=get_due_date_keyboard(lang),
        )
        return

    await finalize_and_save_design(message, state, business, session, lang, due_date=due_date, is_edit=False)

# ==========================================
# 7. Finalize, Save, Done Chime & Summary
# ==========================================
async def finalize_and_save_design(
    msg: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
    due_date: Optional[date] = None,
    is_edit: bool = False,
):
    data = await state.get_data()
    all_expenses_list = collect_all_expenses_list(data)
    amounts = [e["amount"] for e in all_expenses_list]
    target_margin = Decimal(data.get("target_margin_val", "0.25"))

    actual_price_str = data.get("actual_selling_price_val")
    actual_selling_price = Decimal(actual_price_str) if actual_price_str is not None else None

    # Final calculation with actual selling price
    calc = calculate_design_financials(
        expenses=amounts,
        target_margin=target_margin,
        actual_selling_price=actual_selling_price,
    )

    measurements_dict = data.get("measurements_dict", {})
    measurements_json = json.dumps(measurements_dict, ensure_ascii=False) if measurements_dict else None
    gender = data.get("gender")
    clothing_item = data.get("clothing_item")

    # 1. Save design in DB
    design = await crud.create_design(
        session=session,
        business_id=business.id,
        name=data.get("design_name", "Design"),
        calc_result=calc,
        expenses_list=all_expenses_list,
        customer_name=data.get("customer_name"),
        image_file_id=data.get("image_file_id"),
        gender=gender,
        clothing_item=clothing_item,
        measurements_json=measurements_json,
    )

    # 2. If delivery date or customer is provided, auto-create linked order
    order = None
    if due_date or design.customer_name:
        agreed_price = calc.actual_selling_price if calc.actual_selling_price is not None else calc.optimal_price
        order = await crud.create_order_from_design(
            session=session,
            business_id=business.id,
            design_id=design.id,
            customer_name=design.customer_name or "ደንበኛ",
            agreed_price=agreed_price,
            due_date=due_date,
            notes=f"Gender: {gender}, Item: {clothing_item}",
        )

    await state.clear()

    # 3. Audio Chime (Done like sound)
    try:
        chime_bytes = get_chime_bytes()
        await msg.answer_audio(
            audio=BufferedInputFile(chime_bytes, filename="success_chime.wav"),
            title="✅ ምዝገባው ተጠናቋል (Success)",
            performer="Tewabu ERP",
        )
    except Exception as e:
        logger.warning(f"Could not dispatch audio chime: {e}")

    # 4. Final Analysis Summary
    analysis_text = format_final_analysis_text(
        design=design,
        calc=calc,
        lang=lang,
        due_date=due_date,
        measurements=measurements_dict,
        order=order,
    )
    markup = get_design_result_keyboard(design.id, lang)

    if design.image_file_id:
        if is_edit:
            try:
                await msg.delete()
            except Exception:
                pass
        await msg.answer_photo(
            photo=design.image_file_id,
            caption=analysis_text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        if is_edit:
            await msg.edit_text(text=analysis_text, reply_markup=markup, parse_mode="HTML")
        else:
            await msg.answer(text=analysis_text, reply_markup=markup, parse_mode="HTML")

# ==========================================
# Helpers
# ==========================================
def parse_positive_amount(text: str | None) -> Decimal | None:
    if not text:
        return None
    try:
        dec = to_decimal(text)
        return dec if dec >= Decimal("0.00") else None
    except Exception:
        return None

def parse_delivery_date(text: str | None) -> Optional[date]:
    if not text:
        return None
    cleaned = text.strip()
    match_days = re.match(r"^(\d+)\s*(?:ቀን|ቀናት|days?)?$", cleaned, re.IGNORECASE)
    if match_days:
        num_days = int(match_days.group(1))
        if 0 <= num_days <= 365:
            return date.today() + timedelta(days=num_days)

    match_iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", cleaned)
    if match_iso:
        try:
            return date(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3)))
        except ValueError:
            pass

    match_dmy = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", cleaned)
    if match_dmy:
        try:
            return date(int(match_dmy.group(3)), int(match_dmy.group(2)), int(match_dmy.group(1)))
        except ValueError:
            pass

    return None

async def save_standard_expense(state: FSMContext, key: str, name_am: str, amount: Decimal):
    data = await state.get_data()
    exp_dict = data.get("expenses_dict", {})
    exp_dict[key] = {
        "category_key": key,
        "category_name": name_am,
        "amount": amount,
        "is_custom": False,
    }
    await state.update_data(expenses_dict=exp_dict)

def collect_all_expenses_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    exp_dict = data.get("expenses_dict", {})
    extras = data.get("extra_expenses", [])
    result = list(exp_dict.values())
    result.extend(extras)
    return result

def build_expenses_summary_text(data: Dict[str, Any], lang: str) -> str:
    all_expenses = collect_all_expenses_list(data)
    total = sum((e["amount"] for e in all_expenses), Decimal("0.00"))
    lines = [f"🧵 <b>{data.get('design_name')} - የወጪ ዝርዝር</b>" if lang == "am" else f"🧵 <b>{data.get('design_name')} - Expense Summary</b>"]
    lines.append("─────────────────────")
    for e in all_expenses:
        lines.append(f"• {e['category_name']}፦ <b>{format_currency(e['amount'], lang=lang)}</b>")
    lines.append("─────────────────────")
    lines.append(f"💰 <b>አጠቃላይ ድምር ወጪ፦ {format_currency(total, lang=lang)}</b>" if lang == "am" else f"💰 <b>Total Expenses: {format_currency(total, lang=lang)}</b>")
    return "\n".join(lines)

def format_final_analysis_text(
    design: Any,
    calc: Any,
    lang: str,
    due_date: Optional[date] = None,
    measurements: Optional[dict] = None,
    order: Any = None,
) -> str:
    margin_pct = int(calc.target_margin * 100)
    lines = [
        f"✅ <b>ዲዛይኑ በተሳካ ሁኔታ ተመዝግቧል! (ID #{design.id})</b>\n" if lang == "am" else f"✅ <b>Design Saved Successfully! (ID #{design.id})</b>\n",
        f"🏷️ <b>የዲዛይን ስም፦</b> {design.name}",
    ]
    if design.gender:
        gender_icon = "👨 ወንድ (Male)" if design.gender == "MALE" else "👩 ሴት (Female)"
        lines.append(f"👤 <b>ጾታ እና ዓይነት፦</b> {gender_icon} | {design.clothing_item or ''}")

    if design.customer_name:
        lines.append(f"👤 <b>ደንበኛ፦</b> {design.customer_name}")

    if measurements:
        m_lines = []
        for k, v in measurements.items():
            unit = "" if k == "አንገት" else " ሴ.ሜ/in"
            m_lines.append(f"• {k}፦ {v}{unit}")
        if m_lines:
            lines.append("📏 <b>የልኬት ዝርዝር፦</b>\n" + "\n".join(m_lines))

    if due_date:
        days_left = (due_date - date.today()).days
        days_str = f"({days_left} ቀን ይቀራል)" if days_left >= 0 else "(ቀኑ አልፏል)"
        lines.append(f"📅 <b>የማስረከቢያ ቀን፦</b> {due_date.strftime('%Y-%m-%d')} {days_str}")
        lines.append("🔔 <i>የ 5-ቀን ቅድመ ማስታወሻ ነቅቷል!</i>")

    if order:
        lines.append(f"📦 <b>የትዕዛዝ ቁጥር፦</b> {order.order_number}")

    lines.extend([
        "─────────────────────",
        f"💰 <b>አጠቃላይ የምርት ወጪ፦</b> {format_currency(calc.total_cost, lang=lang)}",
        f"⚖️ <b>ወጪ መሸፈኛ ዋጋ፦</b> {format_currency(calc.break_even_price, lang=lang)}",
        f"🪙 <b>ተመራጭ መሸጫ ዋጋ፦</b> {format_currency(calc.optimal_price, lang=lang)} <i>({margin_pct}% ትርፍ)</i>",
        "─────────────────────",
    ])

    if calc.actual_selling_price is not None:
        lines.append(f"🏷️ <b>ትክክለኛ መሸጫ ዋጋ፦</b> {format_currency(calc.actual_selling_price, lang=lang)}")
        
        # Color-coded status badge and explanation
        if calc.status == ProfitStatus.LOSS:
            lines.extend([
                f"\n🔴 <b>ሁኔታ፦ ኪሳራ (LOSS)</b>",
                f"⚠️ <b>የኪሳራ መጠን፦ -{format_currency(calc.loss_amount, lang=lang)}</b>",
                f"<i>ማስጠንቀቂያ፦ የመሸጫ ዋጋው ከወጣው ወጪ በ {format_currency(calc.loss_amount, lang=lang)} ያነሰ በመሆኑ ኪሳራ ያስከትላል!</i>",
            ])
        elif calc.status == ProfitStatus.BREAK_EVEN:
            lines.extend([
                f"\n⚖️ <b>ሁኔታ፦ ወጪና ገቢ እኩል (BREAK-EVEN)</b>",
                f"<i>የመሸጫ ዋጋው ከወጣው ወጪ ጋር እኩል በመሆኑ ትርፍም ኪሳራም የለም።</i>",
            ])
        elif calc.status == ProfitStatus.OPTIMAL:
            lines.extend([
                f"\n🪙 <b>ሁኔታ፦ ተመራጭ መሸጫ ዋጋ (RECOMMENDED OPTIMAL)</b>",
                f"🌟 <b>ትክክለኛ የተገኘ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)}</b> <i>({calc.profit_margin_pct:.1f}%)</i>",
                f"<i>ድንቅ! የታለመውን {margin_pct}% ትርፍ በትክክል የሚያስገኝ ወርቃማ ዋጋ ነው።</i>",
            ])
        elif calc.status == ProfitStatus.ABOVE_TARGET:
            lines.extend([
                f"\n🟢 <b>ሁኔታ፦ ከተጠበቀው ትርፍ በላይ (ABOVE TARGET PROFIT)</b>",
                f"🚀 <b>ትክክለኛ የተገኘ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)}</b> <i>({calc.profit_margin_pct:.1f}%)</i>",
                f"<i>በጣም ምርጥ! ከተመራጩ ዋጋ በላይ ከፍተኛ ትርፍ ያስገኛል።</i>",
            ])
        else: # BELOW_TARGET
            lines.extend([
                f"\n🟡 <b>ሁኔታ፦ ትርፍ አለው (ግን ከዒላማው በታች)</b>",
                f"👌 <b>ትክክለኛ የተገኘ ትርፍ፦ +{format_currency(calc.actual_profit, lang=lang)}</b> <i>({calc.profit_margin_pct:.1f}%)</i>",
                f"<i>ትርፍ አለው፤ ነገር ግን ከተቀመጠው የ {margin_pct}% ትርፍ ዒላማ ያነሰ ነው።</i>",
            ])
    else:
        lines.append("\n<i>ℹ️ ትክክለኛ መሸጫ ዋጋ አልተመዘገበም። 'ዋጋ ሞክር'ን በመጫን ማስመሰል ይችላሉ።</i>")

    return "\n".join(lines)
