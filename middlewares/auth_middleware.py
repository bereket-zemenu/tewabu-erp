"""
Authentication and Session Middleware for Tewabu ERP.
Automatically registers or fetches the user and business, and enforces
security password verification with 3-attempt 24-hour lockout.
"""

from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timezone
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from config.settings import settings
from database.engine import AsyncSessionLocal
import database.crud as crud
from localization.i18n import t
from keyboards.inline import get_main_menu_keyboard

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        async with AsyncSessionLocal() as session:
            db_user, db_business = await crud.get_or_create_user(
                session=session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )

            data["session"] = session
            data["user"] = db_user
            data["business"] = db_business
            lang = db_user.language or "am"
            data["lang"] = lang

            # 1. Check if user account is temporarily locked (after 3 failed attempts)
            is_locked, remaining_td = await crud.check_user_lock(session, db_user)
            if is_locked and remaining_td:
                total_seconds = int(remaining_td.total_seconds())
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                
                lock_msg = (
                    f"⛔ <b>አካውንትዎ ለጊዜው ተቆልፏል! (Account Locked)</b>\n\n"
                    f"የይለፍ ቃል 3 ጊዜ በተሳሳተ መንገድ ስላስገቡ አካውንትዎ ለ 1 ቀን (24 ሰዓት) ተቆልፏል።\n\n"
                    f"⏳ የመቆለፊያው ጊዜ እስኪያበቃ ድረስ <b>{hours} ሰዓት ከ {mins} ደቂቃ</b> ይቀራል፦\n\n"
                    f"<i>(Account locked for 24h due to 3 failed attempts. Time remaining: {hours}h {mins}m)</i>"
                    if lang == "am" else
                    f"⛔ <b>Account Temporarily Locked!</b>\n\n"
                    f"Account is locked for 24 hours due to 3 failed password attempts.\n\n"
                    f"⏳ Time remaining: <b>{hours} hours and {mins} minutes</b>."
                )
                if isinstance(event, Message):
                    await event.answer(text=lock_msg, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ አካውንትዎ ለ 24 ሰዓት ተቆልፏል!", show_alert=True)
                    await event.message.answer(text=lock_msg, parse_mode="HTML")
                return None

            # 2. Check lifetime password verification
            if not getattr(db_user, "is_verified", False):
                if isinstance(event, Message):
                    text = (event.text or "").strip()
                    # Check if password matches
                    if text == settings.ACCESS_PASSWORD:
                        await crud.verify_user(session, db_user.telegram_id)
                        db_user.is_verified = True

                        welcome_text = (
                            f"🎉 <b>የይለፍ ቃሉ በትክክል ተረጋግጧል! (Access Granted)</b>\n\n"
                            f"እንኳን ወደ <b>ተዋቡ ERP</b> በደህና መጡ! 🇪🇹\n"
                            f"አካውንትዎ ለህይወት ዘመን (Lifetime) ሙሉ በሙሉ ተከፍቷል። አሁን ሁሉንም የወጪ ማስያ፣ የዋጋ አስመሳይ፣ የትዕዛዝ እና የሪፖርት አገልግሎቶች መጠቀም ይችላሉ።\n\n"
                            f"{t('main_menu_title', lang)}"
                            if lang == "am" else
                            f"🎉 <b>Password Verified! (Access Granted)</b>\n\n"
                            f"Welcome to <b>Tewabu ERP</b>! 🇪🇹\n"
                            f"Your account has been unlocked for lifetime access. All features are now available.\n\n"
                            f"{t('main_menu_title', lang)}"
                        )
                        await event.answer(
                            text=welcome_text,
                            reply_markup=get_main_menu_keyboard(lang),
                            parse_mode="HTML",
                        )
                        return None
                    else:
                        # If user simply sent /start for the first time
                        if text == "/start":
                            prompt = (
                                "🔐 <b>የተዋቡ ERP የይለፍ ቃል ማረጋገጫ (Security Access)</b>\n\n"
                                "ቦቱን ለመጠቀም እባክዎ የተሰጠዎትን <b>የይለፍ ቃል (Password)</b> ያስገቡ፦\n\n"
                                "<i>Please enter your access password to unlock Tewabu ERP:</i>"
                            )
                        else:
                            # User entered a wrong password - record failure attempt
                            attempts, locked_until = await crud.record_failed_password_attempt(session, db_user)
                            if attempts >= 3:
                                prompt = (
                                    "⛔ <b>አካውንትዎ ለ 1 ቀን (24 ሰዓት) ተቆልፏል!</b>\n\n"
                                    "የይለፍ ቃል 3 ጊዜ በተሳሳተ መንገድ ስላስገቡ አካውንትዎ ለ 24 ሰዓት ተቆልፏል። እባክዎ ከ 24 ሰዓት በኋላ እንደገና ይሞክሩ።\n\n"
                                    "<i>(Account locked for 24 hours due to 3 failed attempts.)</i>"
                                )
                            else:
                                remaining_tries = 3 - attempts
                                prompt = (
                                    f"❌ <b>የተሳሳተ የይለፍ ቃል ነው! (Incorrect Password)</b>\n\n"
                                    f"እባክዎ ትክክለኛውን የይለፍ ቃል ያስገቡ፦\n"
                                    f"⚠️ <b>የቀረዎት ሙከራ፦ {remaining_tries}</b>\n\n"
                                    f"<i>(Incorrect password! Attempts remaining: {remaining_tries})</i>"
                                )

                        await event.answer(text=prompt, parse_mode="HTML")
                        return None

                elif isinstance(event, CallbackQuery):
                    await event.answer("🔐 እባክዎ መጀመሪያ የይለፍ ቃል ያስገቡ! (Please enter password first!)", show_alert=True)
                    prompt = (
                        "🔐 <b>የተዋቡ ERP የይለፍ ቃል ማረጋገጫ (Security Access)</b>\n\n"
                        "ቦቱን ለመጠቀም እባክዎ የተሰጠዎትን <b>የይለፍ ቃል (Password)</b> ያስገቡ፦\n\n"
                        "<i>Please enter your access password to unlock Tewabu ERP:</i>"
                    )
                    await event.message.answer(text=prompt, parse_mode="HTML")
                    return None

            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise
