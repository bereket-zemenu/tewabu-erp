"""
Automated 5-Day Delivery Reminder Service for Tewabu ERP.
Periodically checks for pending/in-production orders due within 5 days
and sends an alert to the business owner on Telegram.
"""

import asyncio
import logging
from datetime import date
from aiogram import Bot
from database.engine import AsyncSessionLocal
import database.crud as crud
from core.calculations import format_currency

logger = logging.getLogger("tewabu_erp.reminder")

async def check_and_send_due_reminders(bot: Bot) -> int:
    """Check orders due in 5 days and dispatch Telegram notifications."""
    sent_count = 0
    async with AsyncSessionLocal() as session:
        due_orders = await crud.get_orders_due_for_reminder(session, days_ahead=5)
        for order, owner_tg_id in due_orders:
            days_left = (order.due_date - date.today()).days if order.due_date else 0
            
            days_text = f"<b>{days_left} ቀን/ቀናት</b>" if days_left > 0 else "<b>ዛሬ!</b>"
            msg = (
                f"🔔 <b>አስቸኳይ ማስታወሻ፦ የልብስ ማስረከቢያ ቀን ደርሷል!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>የትዕዛዝ ቁጥር፦</b> {order.order_number}\n"
                f"👤 <b>ደንበኛ፦</b> {order.customer_name}\n"
                f"📅 <b>የማስረከቢያ ቀን፦</b> {order.due_date.strftime('%Y-%m-%d')}\n"
                f"⏳ <b>የቀረው ጊዜ፦</b> {days_text} ብቻ ቀርተዋል!\n"
                f"📌 <b>የአሁኑ ሁኔታ፦</b> {order.status}\n"
                f"💰 <b>ቀሪ ክፍያ፦</b> {format_currency(order.balance_due)}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <i>እባክዎ ልብሱ በሰዓቱ ተጠናቆ ለደንበኛ እንዲደርስ ክትትል ያድርጉ!</i>"
            )
            try:
                await bot.send_message(chat_id=owner_tg_id, text=msg, parse_mode="HTML")
                await crud.mark_order_reminder_sent(session, order.id)
                sent_count += 1
                logger.info(f"Sent 5-day delivery reminder for order #{order.order_number} to user {owner_tg_id}")
            except Exception as e:
                logger.warning(f"Failed to send reminder for order #{order.id}: {e}")
                
    return sent_count

async def start_reminder_scheduler(bot: Bot, interval_seconds: int = 3600):
    """Background task running continuously to trigger delivery reminders."""
    logger.info("Delivery reminder scheduler started (checking every hour)...")
    while True:
        try:
            await check_and_send_due_reminders(bot)
        except Exception as e:
            logger.error(f"Error in reminder scheduler: {e}")
        await asyncio.sleep(interval_seconds)
