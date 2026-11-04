"""
Business Settings Handler for Tewabu ERP.
Configures target profit margin, language toggle, business profile, and database backups.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Business
import database.crud as crud
from core.calculations import validate_margin
from services.backup_service import create_database_backup
from localization.i18n import t
from keyboards.inline import get_settings_menu_keyboard, get_cancel_keyboard, get_main_menu_keyboard

router = Router(name="settings")

class SettingsStates(StatesGroup):
    waiting_for_margin = State()
    waiting_for_name = State()

@router.callback_query(F.data == "nav_settings")
async def show_settings_menu(
    callback: CallbackQuery,
    business: Business,
    lang: str,
):
    margin_pct = int((business.default_profit_margin or Decimal("0.25")) * 100)
    lang_name = "አማርኛ (Amharic)" if lang == "am" else "English"

    lines = [
        f"⚙️ <b>የቢዝነስ ቅንብሮች (Settings)</b>\n",
        f"🏢 <b>የንግድ ስም፦</b> {business.name}",
        f"🎯 <b>መደበኛ የታለመ ትርፍ መቶኛ፦</b> <b>{margin_pct}%</b>",
        f"💱 <b>የመገበያያ ገንዘብ፦</b> <b>{business.currency} (የኢትዮጵያ ብር)</b>",
        f"🌐 <b>ቋንቋ፦</b> {lang_name}\n",
        f"ከታች ካሉት አማራጮች ማስተካከል የሚፈልጉትን ይምረጡ፦",
    ]
    await callback.answer()
    await callback.message.edit_text(
        text="\n".join(lines),
        reply_markup=get_settings_menu_keyboard(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "set_lang_toggle")
async def toggle_language(
    callback: CallbackQuery,
    user: User,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    new_lang = "en" if lang == "am" else "am"
    await crud.update_user_language(session, user.telegram_id, new_lang)
    alert = "🌐 Language changed to English!" if new_lang == "en" else "🌐 ቋንቋው ወደ አማርኛ ተቀይሯል!"
    await callback.answer(alert, show_alert=True)

    # Re-render settings screen with new language
    await show_settings_menu(callback, business, new_lang)

@router.callback_query(F.data == "set_margin_change")
async def prompt_margin_change(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_margin)
    prompt = (
        "🎯 <b>አዲስ መደበኛ የታለመ ትርፍ መቶኛ ያስገቡ፦</b>\n\n"
        "ለምሳሌ፦ <b>30</b> ወይም <b>0.30</b> (ለ 30%) ያስገቡ፦"
        if lang == "am" else
        "🎯 <b>Enter New Default Target Profit Margin:</b>\n\n"
        "e.g. Enter <b>30</b> or <b>0.30</b> (for 30%):"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(SettingsStates.waiting_for_margin)
async def process_margin_change(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    try:
        new_margin = validate_margin(message.text)
    except ValueError:
        await message.answer(t("err_invalid_margin", lang), reply_markup=get_cancel_keyboard(lang))
        return

    await state.clear()
    updated = await crud.update_business_settings(
        session=session,
        business_id=business.id,
        default_profit_margin=new_margin,
    )
    margin_pct = int(new_margin * 100)
    text = (
        f"✅ <b>የታለመው መደበኛ ትርፍ መቶኛ ወደ {margin_pct}% ተቀይሯል!</b>"
        if lang == "am" else
        f"✅ <b>Default profit margin updated to {margin_pct}%!</b>"
    )
    await message.answer(text=text, reply_markup=get_main_menu_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data == "set_name_change")
async def prompt_name_change(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await state.set_state(SettingsStates.waiting_for_name)
    prompt = (
        "🏷️ <b>አዲስ የንግድ ስም ያስገቡ፦</b>\n\n"
        "ለምሳሌ፦ <b>የተዋቡ ዘመናዊ የሀበሻ ልብስ ስፌት</b>"
        if lang == "am" else
        "🏷️ <b>Enter New Business Name:</b>\n\n"
        "e.g. <b>Tewabu Habesha Tailors</b>"
    )
    await callback.answer()
    await callback.message.edit_text(text=prompt, reply_markup=get_cancel_keyboard(lang), parse_mode="HTML")

@router.message(SettingsStates.waiting_for_name)
async def process_name_change(
    message: Message,
    state: FSMContext,
    business: Business,
    session: AsyncSession,
    lang: str,
):
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await message.answer("❌ እባክዎ ትክክለኛ ስም ያስገቡ፦" if lang == "am" else "❌ Enter valid name:")
        return

    await state.clear()
    await crud.update_business_settings(session=session, business_id=business.id, name=name)
    text = (
        f"✅ <b>የንግድ ስምዎ ወደ '{name}' ተቀይሯል!</b>"
        if lang == "am" else
        f"✅ <b>Business name updated to '{name}'!</b>"
    )
    await message.answer(text=text, reply_markup=get_main_menu_keyboard(lang), parse_mode="HTML")

@router.callback_query(F.data == "set_backup_now")
async def trigger_backup(callback: CallbackQuery, lang: str):
    await callback.answer("⏳ የዳታቤዝ ባካፕ እየተወሰደ ነው..." if lang == "am" else "⏳ Creating backup...")
    try:
        backup_path = create_database_backup()
        doc_file = FSInputFile(str(backup_path), filename=backup_path.name)
        caption = (
            f"💾 <b>የዳታቤዝ ባካፕ በተሳካ ሁኔታ ተጠናቋል!</b>\n"
            f"📁 ፋይል፦ {backup_path.name}"
            if lang == "am" else
            f"💾 <b>Database backup completed!</b>\n"
            f"📁 File: {backup_path.name}"
        )
        await callback.message.answer_document(document=doc_file, caption=caption, parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"❌ የባካፕ ስህተት፦ {str(e)}")
