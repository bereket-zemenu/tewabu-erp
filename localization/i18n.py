"""
Localization module for Tewabu ERP.
Supports Amharic (primary, default) and English with easy key lookup.
"""

from typing import Dict, Any

MESSAGES: Dict[str, Dict[str, str]] = {
    # App General
    "app_title": {
        "am": "🧵 <b>ተዋቡ ERP (Tewabu ERP)</b>\n<i>የልብስ ስፌት ቤት የወጪ እና ትርፍ መቆጣጠሪያ ሲስተም</i>",
        "en": "🧵 <b>Tewabu ERP</b>\n<i>Tailor House Cost & Profit Manager</i>",
    },
    "welcome_new_user": {
        "am": (
            "እንኳን ወደ <b>ተዋቡ ERP</b> በደህና መጡ! 🇪🇹\n\n"
            "ይህ ቦት ለልብስ ስፌት ቤቶች የተዘጋጀ ሲሆን፡\n"
            "• የልብስ ምርት ወጪን በትክክል ለማስላት\n"
            "• ተመራጭ መሸጫ ዋጋን ለመወሰን\n"
            "• ኪሳራን አስቀድሞ ለማወቅ እና ትርፋማነትን ለመከታተል ይረዳዎታል።\n\n"
            "ለመጀመር ከታች ካሉት አማራጮች አንዱን ይምረጡ፦"
        ),
        "en": (
            "Welcome to <b>Tewabu ERP</b>! 🇪🇹\n\n"
            "Designed for Ethiopian tailoring businesses to:\n"
            "• Accurately calculate clothing production expenses\n"
            "• Determine optimal selling prices\n"
            "• Prevent losses & track overall business profitability\n\n"
            "Please select an option from the menu below:"
        ),
    },
    "main_menu_title": {
        "am": "🏠 <b>ዋና ሜኑ | Main Menu</b>\nምን ማከናወን ይፈልጋሉ?",
        "en": "🏠 <b>Main Menu</b>\nWhat would you like to do?",
    },
    # Buttons
    "btn_new_design": {
        "am": "➕ አዲስ ዲዛይን (New Design)",
        "en": "➕ New Design",
    },
    "btn_cost_calculator": {
        "am": "🧮 ፈጣን የወጪ ማስያ (Cost Calculator)",
        "en": "🧮 Cost Calculator",
    },
    "btn_price_simulator": {
        "am": "🎯 የዋጋ አስመሳይ (Price Simulator)",
        "en": "🎯 Price Simulator",
    },
    "btn_dashboard": {
        "am": "📊 የንግድ ዳሽቦርድ (Dashboard)",
        "en": "📊 Business Dashboard",
    },
    "btn_history": {
        "am": "📜 የዲዛይን ታሪክ (Design History)",
        "en": "📜 Design History",
    },
    "btn_orders": {
        "am": "📦 የትዕዛዝ ክትትል (Order Manager)",
        "en": "📦 Order Management",
    },
    "btn_reports": {
        "am": "📈 የፋይናንስ ሪፖርት (Reports)",
        "en": "📈 Financial Reports",
    },
    "btn_settings": {
        "am": "⚙️ ቅንብሮች (Settings)",
        "en": "⚙️ Settings",
    },
    "btn_help": {
        "am": "❓ እገዛ እና መመሪያ (Help)",
        "en": "❓ Help & Guide",
    },
    "btn_back": {
        "am": "⬅️ ወደ ኋላ",
        "en": "⬅️ Back",
    },
    "btn_skip": {
        "am": "⏭️ ዝለል (0 ብር)",
        "en": "⏭️ Skip (0 ETB)",
    },
    "btn_cancel": {
        "am": "❌ ሰርዝ",
        "en": "❌ Cancel",
    },
    "btn_edit": {
        "am": "✏️ አስተካክል",
        "en": "✏️ Edit",
    },
    "btn_confirm": {
        "am": "✅ አረጋግጥ እና መዝግብ",
        "en": "✅ Confirm & Save",
    },
    "btn_add_extra_expense": {
        "am": "➕ ተጨማሪ ወጪ ጨምር",
        "en": "➕ Add Extra Expense",
    },
    "btn_finish_expenses": {
        "am": "✅ ወጪዎችን አጠናቅቅ",
        "en": "✅ Finish Expenses",
    },
    "btn_main_menu": {
        "am": "🏠 ወደ ዋና ሜኑ",
        "en": "🏠 Main Menu",
    },
    # Workflow Steps
    "step_design_name": {
        "am": "🏷️ <b>ደረጃ 1/6</b>: እባክዎ የልብሱን ወይም የዲዛይኑን ስም ያስገቡ፦\n<i>(ምሳሌ፡ የሀበሻ ቀሚስ፣ ዘመናዊ ጃኬት፣ የተጣለ ቀሚስ)</i>",
        "en": "🏷️ <b>Step 1/6</b>: Please enter the Clothing/Design Name:\n<i>(e.g., Habesha Kemis, Modern Suit, Kaftan)</i>",
    },
    "step_customer_name": {
        "am": "👤 <b>ደረጃ 2/6</b>: የደንበኛ ስም ወይም የትዕዛዝ መለያ (Order ID) ያስገቡ፦\n<i>(አማራጭ ነው፣ ካልፈለጉ 'ዝለል' የሚለውን ይጫኑ)</i>",
        "en": "👤 <b>Step 2/6</b>: Enter Customer Name or Order ID:\n<i>(Optional, click 'Skip' if not applicable)</i>",
    },
    "step_expense_menen_gever": {
        "am": "1️⃣ <b>የመነን እና ገቨር ወጪ</b> (Menen & Gever):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦\n<i>(ወጪ ከሌለው 'ዝለል' ወይም 0 ይፃፉ)</i>",
        "en": "1️⃣ <b>Menen & Gever (Fabric & Lining) Cost</b>:\nPlease enter amount in ETB:\n<i>(Click 'Skip' or type 0 if none)</i>",
    },
    "step_expense_thread": {
        "am": "2️⃣ <b>የክር ወጪ</b> (Thread):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦",
        "en": "2️⃣ <b>Thread Cost</b>:\nPlease enter amount in ETB:",
    },
    "step_expense_embroidery": {
        "am": "3️⃣ <b>የጠላፊ ክፍያ/ወጪ</b> (Embroidery Craft):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦",
        "en": "3️⃣ <b>Embroidery (Telafe) Cost</b>:\nPlease enter amount in ETB:",
    },
    "step_expense_sewing": {
        "am": "4️⃣ <b>የሰፊ ክፍያ/ወጪ</b> (Tailoring / Stitching):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦",
        "en": "4️⃣ <b>Sewing (Sefi) Labor Cost</b>:\nPlease enter amount in ETB:",
    },
    "step_expense_designer": {
        "am": "5️⃣ <b>የዲዛይነር ክፍያ</b> (Designer Fee):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦",
        "en": "5️⃣ <b>Designer Fee</b>:\nPlease enter amount in ETB:",
    },
    "step_expense_related": {
        "am": "6️⃣ <b>ተያያዥ እና ልዩ ልዩ ወጪዎች</b> (Related/Misc Expenses):\nእባክዎ በኢትዮጵያ ብር (ETB) ያስገቡ፦",
        "en": "6️⃣ <b>Related / Misc Expenses</b>:\nPlease enter amount in ETB:",
    },
    "step_extra_expense_name": {
        "am": "➕ እባክዎ የተጨማሪ ወጪውን ስም ይፃፉ፦\n<i>(ምሳሌ፡ ዚፕ እና ቁልፍ፣ ማጓጓዣ፣ ማሸጊያ)</i>",
        "en": "➕ Please enter the name of the extra expense:\n<i>(e.g., Zipper & Buttons, Transport, Packaging)</i>",
    },
    "step_extra_expense_amount": {
        "am": "💰 ለ <b>{name}</b> የወጣውን ወጪ በብር ያስገቡ፦",
        "en": "💰 Enter amount in ETB for <b>{name}</b>:",
    },
    "step_target_margin": {
        "am": (
            "🎯 <b>የታለመው የትርፍ መቶኛ (Target Profit Margin)</b>\n"
            "የአሁኑ መደበኛ ትርፍ መቶኛ፦ <b>{default_margin}%</b>\n\n"
            "ለዚህ ልብስ የተለየ የትርፍ መቶኛ ማስገባት ከፈለጉ ቁጥሩን ይፃፉ (ምሳሌ፡ <b>30</b> ወይም <b>0.30</b>)፦\n"
            "ወይም ነባሩን ለመጠቀም 'ነባሩን ተጠቀም' የሚለውን ይጫኑ።"
        ),
        "en": (
            "🎯 <b>Target Profit Margin</b>\n"
            "Current business default: <b>{default_margin}%</b>\n\n"
            "Enter custom margin percentage (e.g. <b>30</b> or <b>0.30</b>),\n"
            "or click 'Use Default' to continue."
        ),
    },
    "btn_use_default_margin": {
        "am": "✅ ነባሩን ({margin}%) ተጠቀም",
        "en": "✅ Use Default ({margin}%)",
    },
    "step_actual_selling_price": {
        "am": (
            "🏷️ <b>ትክክለኛ የመሸጫ ዋጋ (Actual Selling Price)</b>\n\n"
            "ይህን ልብስ ለደንበኛ የሚሸጡበትን ትክክለኛ ዋጋ በብር ያስገቡ፦\n"
            "<i>(ዋጋውን ገና ካልወሰኑ 'ዝለል' የሚለውን መጫን ይችላሉ)</i>"
        ),
        "en": (
            "🏷️ <b>Actual Selling Price</b>\n\n"
            "Enter the actual selling price negotiated with the customer in ETB:\n"
            "<i>(Or click 'Skip' if not yet decided)</i>"
        ),
    },
    # Status Titles and Explanations
    "status_loss": {
        "am": "🔴 <b>ኪሳራ (LOSS)</b>",
        "en": "🔴 <b>FINANCIAL LOSS</b>",
    },
    "status_loss_desc": {
        "am": "⚠️ ማስጠንቀቂያ፡ የመሸጫ ዋጋው ከአጠቃላይ የምርት ወጪው ያነሰ በመሆኑ <b>{loss}</b> ኪሳራ ያስከትላል!",
        "en": "⚠️ Warning: Selling price is below total production cost! Financial loss of <b>{loss}</b>.",
    },
    "status_break_even": {
        "am": "⚖️ <b>ወጪና ገቢ እኩል (BREAK EVEN)</b>",
        "en": "⚖️ <b>BREAK-EVEN</b>",
    },
    "status_break_even_desc": {
        "am": "ℹ️ የመሸጫ ዋጋው ከወጣው ወጪ ጋር እኩል ነው። ኪሳራ የለም፤ ትርፍም የለም።",
        "en": "ℹ️ Selling price exactly covers total production cost. Zero net profit.",
    },
    "status_optimal": {
        "am": "🪙 <b>ተመራጭ መሸጫ ዋጋ (RECOMMENDED OPTIMAL PRICE)</b>",
        "en": "🪙 <b>RECOMMENDED OPTIMAL PRICE</b>",
    },
    "status_optimal_desc": {
        "am": "🌟 ድንቅ! ይህ ዋጋ የታለመውን <b>{margin}%</b> ትርፍ ሙሉ በሙሉ ያስገኛል።",
        "en": "🌟 Optimal! This price achieves your target <b>{margin}%</b> profit margin.",
    },
    "status_above_target": {
        "am": "🟢 <b>ከተጠበቀው ትርፍ በላይ (ABOVE TARGET PROFIT)</b>",
        "en": "🟢 <b>ABOVE TARGET PROFIT</b>",
    },
    "status_above_target_desc": {
        "am": "🚀 በጣም ምርጥ! የመሸጫ ዋጋው ከተመራጩ ዋጋ በላይ በመሆኑ ተጨማሪ ከፍተኛ ትርፍ ያስገኛል።",
        "en": "🚀 Excellent! Selling price exceeds optimal target, yielding superior profits.",
    },
    "status_below_target": {
        "am": "🟡 <b>ትርፍ አለው (ግን ከዒላማው በታች)</b>",
        "en": "🟡 <b>BELOW TARGET PROFIT</b>",
    },
    "status_below_target_desc": {
        "am": "👌 ትርፍ ያገኛሉ፤ ነገር ግን ከተቀመጠው <b>{margin}%</b> የትርፍ ዒላማ ያነሰ ነው።",
        "en": "👌 Profitable, but lower than your target <b>{margin}%</b> margin.",
    },
    # Order Status Labels
    "order_status_PENDING": {
        "am": "⏳ በመጠባበቅ ላይ",
        "en": "⏳ Pending",
    },
    "order_status_IN_PRODUCTION": {
        "am": "🪡 በስራ ላይ",
        "en": "🪡 In Production",
    },
    "order_status_COMPLETED": {
        "am": "✅ የተጠናቀቀ",
        "en": "✅ Completed",
    },
    "order_status_DELIVERED": {
        "am": "📦 የተረከበ",
        "en": "📦 Delivered",
    },
    "order_status_CANCELLED": {
        "am": "🚫 የተሰረዘ",
        "en": "🚫 Cancelled",
    },
    # Errors & Validation
    "err_invalid_amount": {
        "am": "❌ እባክዎ ትክክለኛ ያልአሉታዊ የገንዘብ ቁጥር ያስገቡ (ምሳሌ፡ 250 ወይም 1500.50)፦",
        "en": "❌ Please enter a valid non-negative number (e.g. 250 or 1500.50):",
    },
    "err_invalid_margin": {
        "am": "❌ የትርፍ መቶኛ ከ0% እኩል ወይም በላይ እና ከ100% በታች መሆን አለበት (ምሳሌ፡ 25 ወይም 0.25)፦",
        "en": "❌ Profit margin must be >= 0% and < 100% (e.g. 25 or 0.25):",
    },
    "msg_action_cancelled": {
        "am": "❌ ክንውኑ ተሰርዟል። ወደ ዋናው ሜኑ ተመልሰዋል።",
        "en": "❌ Action cancelled. Returned to main menu.",
    },
    "msg_saved_success": {
        "am": "✅ መረጃው በተሳካ ሁኔታ ተመዝግቧል!",
        "en": "✅ Record saved successfully!",
    },
}

def t(key: str, lang: str = "am", **kwargs: Any) -> str:
    """Translate key to specified language with fallback to Amharic, formatting kwargs."""
    entry = MESSAGES.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get("am") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
