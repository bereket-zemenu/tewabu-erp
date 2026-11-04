"""
Common command and navigation handlers for Tewabu ERP.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.models import User, Business
from localization.i18n import t
from keyboards.inline import get_main_menu_keyboard

router = Router(name="common")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User, business: Business, lang: str):
    """Handle /start command."""
    await state.clear()
    welcome_text = (
        f"{t('app_title', lang)}\n\n"
        f"🇪🇹 <b>{business.name}</b>\n\n"
        f"{t('welcome_new_user', lang)}"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )

@router.message(Command("help"))
@router.callback_query(F.data == "nav_help")
async def cmd_help(event: Message | CallbackQuery, state: FSMContext, lang: str):
    """Handle /help command or help button."""
    await state.clear()
    help_text_am = (
        "📖 <b>የተዋቡ ERP አጠቃቀም መመሪያ እና የቀመር ማብራሪያ</b>\n\n"
        "<b>1. የወጪ አሰላል ቀመር (Formulas)፦</b>\n"
        "• <b>አጠቃላይ ወጪ (Total Cost)</b> = የመነን/ገቨር + የክር + የጠላፊ + የሰፊ + የዲዛይነር + ተያያዥ ወጪዎች ድምር\n"
        "• <b>ወጪ መሸፈኛ ዋጋ (Break-even Price)</b> = አጠቃላይ ወጪ\n"
        "• <b>ተመራጭ መሸጫ ዋጋ (Optimal Price)</b> = አጠቃላይ ወጪ / (1 - የታለመው ትርፍ መቶኛ)\n"
        "• <b>ትክክለኛ ትርፍ (Actual Profit)</b> = ትክክለኛ መሸጫ ዋጋ - አጠቃላይ ወጪ\n\n"
        "<b>2. የቀለም እና ሁኔታ አመልካቾች፦</b>\n"
        "🔴 <b>ኪሳራ (LOSS)</b>፦ መሸጫ ዋጋው ከወጣው ወጪ በታች ሲሆን።\n"
        "⚖️ <b>ወጪና ገቢ እኩል (BREAK-EVEN)</b>፦ መሸጫ ዋጋው ከወጣው ወጪ ጋር እኩል ሲሆን።\n"
        "🟡 <b>ትርፍ አለው (ከዒላማ በታች)</b>፦ ትርፍ ያገኛሉ ነገር ግን ከታለመው መቶኛ ያነሰ ነው።\n"
        "🪙 <b>ተመራጭ መሸጫ ዋጋ (OPTIMAL)</b>፦ የታለመውን ትርፍ በትክክል የሚያስገኝ ወርቃማ ዋጋ።\n"
        "🟢 <b>ከተጠበቀው በላይ (ABOVE TARGET)</b>፦ ከተመራጩ ዋጋ በላይ ከፍተኛ ትርፍ።\n\n"
        "<b>3. ዋና ዋና አገልግሎቶች፦</b>\n"
        "• <b>አዲስ ዲዛይን</b>፦ ደረጃ በደረጃ ወጪዎችን መዝግቦ ትርፍን ያሰላል።\n"
        "• <b>የዋጋ አስመሳይ</b>፦ የተለያዩ መሸጫ ዋጋዎችን በመሞከር ትርፍ እና ኪሳራን አስቀድሞ ማየት።\n"
        "• <b>ዳሽቦርድ እና ሪፖርቶች</b>፦ የንግድዎን አጠቃላይ ገቢ፣ ወጪ፣ የተጣራ ትርፍ እና ቻርቶችን ያሳያል።"
    )
    help_text_en = (
        "📖 <b>Tewabu ERP User Guide & Financial Formulas</b>\n\n"
        "<b>1. Financial Calculation Formulas:</b>\n"
        "• <b>Total Cost</b> = Sum of all 6 expenses + custom extras\n"
        "• <b>Break-even Price</b> = Total Cost\n"
        "• <b>Optimal Selling Price</b> = Total Cost / (1 - Target Margin)\n"
        "• <b>Actual Profit</b> = Actual Selling Price - Total Cost\n\n"
        "<b>2. Color-coded Statuses:</b>\n"
        "🔴 <b>LOSS</b>: Selling price is below total production cost.\n"
        "⚖️ <b>BREAK-EVEN</b>: Selling price exactly covers total cost.\n"
        "🟡 <b>BELOW TARGET</b>: Profitable, but lower than target margin.\n"
        "🪙 <b>OPTIMAL PRICE</b>: Achieves exact target profit margin.\n"
        "🟢 <b>ABOVE TARGET</b>: Selling price exceeds optimal target.\n\n"
        "<b>3. Key Features:</b>\n"
        "• <b>New Design</b>: Guided 11-step production costing workflow.\n"
        "• <b>Price Simulator</b>: Test hypothetical prices instantly.\n"
        "• <b>Dashboard & Reports</b>: Visual charts and CSV exports."
    )
    text = help_text_am if lang == "am" else help_text_en
    markup = get_main_menu_keyboard(lang)

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
    else:
        await event.answer(text=text, reply_markup=markup, parse_mode="HTML")

@router.message(Command("cancel"))
@router.callback_query(F.data == "flow_cancel")
async def cmd_cancel(event: Message | CallbackQuery, state: FSMContext, lang: str):
    """Cancel current FSM workflow and return to main menu."""
    await state.clear()
    msg_text = f"{t('msg_action_cancelled', lang)}\n\n{t('main_menu_title', lang)}"
    markup = get_main_menu_keyboard(lang)

    if isinstance(event, CallbackQuery):
        await event.answer(t("msg_action_cancelled", lang))
        await event.message.edit_text(text=msg_text, reply_markup=markup, parse_mode="HTML")
    else:
        await event.answer(text=msg_text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def nav_main_menu(callback: CallbackQuery, state: FSMContext, lang: str):
    """Return to main menu."""
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        text=t("main_menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
