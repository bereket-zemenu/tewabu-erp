"""
Inline Keyboard builders for Tewabu ERP with full Amharic and English localization.
"""

from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from localization.i18n import t

def get_gender_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Gender selection keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="👨 ወንድ (Male)" if lang == "am" else "👨 Male", callback_data="gender_choice:MALE"),
            InlineKeyboardButton(text="👩 ሴት (Female)" if lang == "am" else "👩 Female", callback_data="gender_choice:FEMALE"),
        ],
        [
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_male_clothing_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Male clothing item options."""
    buttons = [
        [
            InlineKeyboardButton(text="1. 👕 ቲሸርት (ተከፋች)", callback_data="male_item:tshirt_open"),
            InlineKeyboardButton(text="2. 👕 ቲሸርት (ያለተከፋች)", callback_data="male_item:tshirt_closed"),
        ],
        [
            InlineKeyboardButton(text="3. 🧥 ጃኬት", callback_data="male_item:jacket"),
            InlineKeyboardButton(text="4. 👖 ሱሪ", callback_data="male_item:pants"),
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:gender"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_female_clothing_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Female clothing item options."""
    buttons = [
        [
            InlineKeyboardButton(text="1. 👗 የሀበሻ ቀሚስ", callback_data="female_item:habesha_dress"),
            InlineKeyboardButton(text="2. 👗 ሙሉ ቀሚስ", callback_data="female_item:full_dress"),
        ],
        [
            InlineKeyboardButton(text="3. 👚 ቶፕ እና ቀሚስ", callback_data="female_item:top_skirt"),
            InlineKeyboardButton(text="4. 👘 ሸሚዝ / ቶፕ", callback_data="female_item:shirt_top"),
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:gender"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_neck_style_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Quick choice buttons for female neck style (አንገት)."""
    buttons = [
        [
            InlineKeyboardButton(text="⭕ ክብ (Round)", callback_data="neck_style:ክብ (Round)"),
            InlineKeyboardButton(text="📐 V-አንገት (V-Neck)", callback_data="neck_style:V-አንገት (V-Neck)"),
        ],
        [
            InlineKeyboardButton(text="⏹️ ካሬ (Square)", callback_data="neck_style:ካሬ (Square)"),
            InlineKeyboardButton(text="👔 ቆሌት / ኮላ (Collar)", callback_data="neck_style:ቆሌት / ኮላ (Collar)"),
        ],
        [
            InlineKeyboardButton(text=t("btn_skip", lang), callback_data="step_skip:measurement"),
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:measurement"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_due_date_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Quick delivery date selections."""
    buttons = [
        [
            InlineKeyboardButton(text="📅 በ 5 ቀን ውስጥ", callback_data="due_days:5"),
            InlineKeyboardButton(text="📅 በ 7 ቀን ውስጥ", callback_data="due_days:7"),
        ],
        [
            InlineKeyboardButton(text="📅 በ 10 ቀን ውስጥ", callback_data="due_days:10"),
            InlineKeyboardButton(text="📅 በ 15 ቀን ውስጥ", callback_data="due_days:15"),
        ],
        [
            InlineKeyboardButton(text=t("btn_skip", lang), callback_data="step_skip:due_date"),
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:due_date"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Build the primary 8-action menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_new_design", lang), callback_data="nav_new_design"),
        ],
        [
            InlineKeyboardButton(text=t("btn_cost_calculator", lang), callback_data="nav_cost_calculator"),
            InlineKeyboardButton(text=t("btn_price_simulator", lang), callback_data="nav_price_simulator"),
        ],
        [
            InlineKeyboardButton(text=t("btn_dashboard", lang), callback_data="nav_dashboard"),
            InlineKeyboardButton(text=t("btn_history", lang), callback_data="nav_history:0"),
        ],
        [
            InlineKeyboardButton(text=t("btn_orders", lang), callback_data="nav_orders:all:0"),
            InlineKeyboardButton(text=t("btn_reports", lang), callback_data="nav_reports"),
        ],
        [
            InlineKeyboardButton(text=t("btn_settings", lang), callback_data="nav_settings"),
            InlineKeyboardButton(text=t("btn_help", lang), callback_data="nav_help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_step_nav_keyboard(
    lang: str = "am",
    show_skip: bool = False,
    show_back: bool = True,
    step_key: str = "",
) -> InlineKeyboardMarkup:
    """Navigation keyboard for guided entry steps (Back, Skip, Cancel)."""
    row = []
    if show_back:
        row.append(InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"step_back:{step_key}"))
    if show_skip:
        row.append(InlineKeyboardButton(text=t("btn_skip", lang), callback_data=f"step_skip:{step_key}"))
    row.append(InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])

def get_extra_expenses_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Options after standard 6 expenses: Calculate costs or Add extra."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🧮 ወጪ አስላ (Calculate Costs)" if lang == "am" else "🧮 Calculate Costs",
                callback_data="extra_finish",
            ),
            InlineKeyboardButton(
                text="➕ ተጨማሪ ወጪ (Add Extra)" if lang == "am" else "➕ Add Extra",
                callback_data="extra_add",
            ),
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data="step_back:extra_choice"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_margin_choice_keyboard(default_margin: Decimal, lang: str = "am") -> InlineKeyboardMarkup:
    """Option to use business default profit margin or type custom."""
    margin_pct = int(default_margin * 100)
    buttons = [
        [
            InlineKeyboardButton(
                text=t("btn_use_default_margin", lang, margin=margin_pct),
                callback_data=f"use_default_margin:{margin_pct}",
            )
        ],
        [
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_actual_price_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Skip or cancel button during actual selling price prompt."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip_actual_price"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_design_result_keyboard(design_id: int, lang: str = "am") -> InlineKeyboardMarkup:
    """Action buttons after calculation is completed and saved."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🎯 ዋጋ ሞክር (Simulate Price)" if lang == "am" else "🎯 Simulate Price",
                callback_data=f"sim_design:{design_id}",
            ),
            InlineKeyboardButton(
                text="📦 ትዕዛዝ ፍጠር (Create Order)" if lang == "am" else "📦 Create Order",
                callback_data=f"order_create_from:{design_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✏️ ዋጋ ቀይር (Edit Price)" if lang == "am" else "✏️ Edit Price",
                callback_data=f"edit_price:{design_id}",
            ),
            InlineKeyboardButton(
                text="➕ አዲስ ዲዛይን (New Design)" if lang == "am" else "➕ New Design",
                callback_data="nav_new_design",
            ),
        ],
        [
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_history_list_keyboard(
    designs: list,
    page: int,
    total_pages: int,
    lang: str = "am",
) -> InlineKeyboardMarkup:
    """List of designs with pagination buttons."""
    buttons = []
    for d in designs:
        status_icon = "🔴" if d.status == "LOSS" else ("🪙" if d.status == "OPTIMAL" else "🟢")
        text = f"{status_icon} {d.name} ({d.total_cost:.2f} ብር)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_design:{d.id}:{page}")])

    # Pagination navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ ወደ ኋላ", callback_data=f"nav_history:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{max(1, total_pages)}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="ወደ ፊት ▶️", callback_data=f"nav_history:{page + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(
            text="🔍 ፈልግ (Search)" if lang == "am" else "🔍 Search",
            callback_data="search_design",
        ),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_design_detail_keyboard(design_id: int, return_page: int = 0, lang: str = "am") -> InlineKeyboardMarkup:
    """Actions on single design detail view."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🎯 ዋጋ አስመስል (Simulate)" if lang == "am" else "🎯 Simulate",
                callback_data=f"sim_design:{design_id}",
            ),
            InlineKeyboardButton(
                text="✏️ ዋጋ አስተካክል (Edit Price)" if lang == "am" else "✏️ Edit Price",
                callback_data=f"edit_price:{design_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📦 ትዕዛዝ ክፈት (Order)" if lang == "am" else "📦 Order",
                callback_data=f"order_create_from:{design_id}",
            ),
            InlineKeyboardButton(
                text="🗑️ ሰርዝ (Delete)" if lang == "am" else "🗑️ Delete",
                callback_data=f"delete_design:{design_id}",
            ),
        ],
        [
            InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"nav_history:{return_page}"),
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_orders_list_keyboard(
    orders: list,
    status_filter: str,
    page: int,
    total_pages: int,
    lang: str = "am",
) -> InlineKeyboardMarkup:
    """Order list with filter and pagination."""
    buttons = []

    # Filter chips
    filter_row = [
        InlineKeyboardButton(
            text=("• ሁሉንም •" if status_filter == "all" else "ሁሉንም"),
            callback_data="nav_orders:all:0",
        ),
        InlineKeyboardButton(
            text=("• በመጠባበቅ •" if status_filter == "PENDING" else "በመጠባበቅ"),
            callback_data="nav_orders:PENDING:0",
        ),
        InlineKeyboardButton(
            text=("• በስራ ላይ •" if status_filter == "IN_PRODUCTION" else "በስራ ላይ"),
            callback_data="nav_orders:IN_PRODUCTION:0",
        ),
        InlineKeyboardButton(
            text=("• የተጠናቀቁ •" if status_filter == "COMPLETED" else "የተጠናቀቁ"),
            callback_data="nav_orders:COMPLETED:0",
        ),
    ]
    buttons.append(filter_row)

    for o in orders:
        btn_text = f"📦 {o.order_number} - {o.customer_name} ({o.status})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_order:{o.id}:{status_filter}:{page}")])

    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ ወደ ኋላ", callback_data=f"nav_orders:{status_filter}:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{max(1, total_pages)}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="ወደ ፊት ▶️", callback_data=f"nav_orders:{status_filter}:{page + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_detail_keyboard(
    order_id: int,
    current_status: str,
    status_filter: str = "all",
    page: int = 0,
    lang: str = "am",
) -> InlineKeyboardMarkup:
    """Status updater buttons for an order."""
    buttons = []
    # Status progression buttons
    status_row = []
    if current_status == "PENDING":
        status_row.append(InlineKeyboardButton(text="🪡 ወደ ስራ አስገባ", callback_data=f"set_ord_st:{order_id}:IN_PRODUCTION"))
    elif current_status == "IN_PRODUCTION":
        status_row.append(InlineKeyboardButton(text="✅ አጠናቅቅ (Completed)", callback_data=f"set_ord_st:{order_id}:COMPLETED"))
    elif current_status == "COMPLETED":
        status_row.append(InlineKeyboardButton(text="📦 ለደንበኛ አስረክብ (Delivered)", callback_data=f"set_ord_st:{order_id}:DELIVERED"))

    if current_status not in ("CANCELLED", "DELIVERED"):
        status_row.append(InlineKeyboardButton(text="🚫 ሰርዝ (Cancel)", callback_data=f"set_ord_st:{order_id}:CANCELLED"))

    if status_row:
        buttons.append(status_row)

    buttons.append([
        InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"nav_orders:{status_filter}:{page}"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reports_menu_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Financial reporting menu."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 የዛሬ ሪፖርት (Daily)" if lang == "am" else "📅 Daily Report",
                callback_data="rep_period:daily",
            ),
            InlineKeyboardButton(
                text="📆 የሳምንቱ ሪፖርት (Weekly)" if lang == "am" else "📆 Weekly Report",
                callback_data="rep_period:weekly",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 የወሩ ሪፖርት (Monthly)" if lang == "am" else "📊 Monthly Report",
                callback_data="rep_period:monthly",
            ),
            InlineKeyboardButton(
                text="📈 የፋይናንስ ቻርት (Visual Chart)" if lang == "am" else "📈 Visual Chart",
                callback_data="rep_chart",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📥 ዲዛይኖችን በ CSV አውርድ" if lang == "am" else "📥 Export Designs CSV",
                callback_data="rep_csv_designs",
            ),
            InlineKeyboardButton(
                text="📥 የፋይናንስ መዝገብ በ CSV" if lang == "am" else "📥 Export Ledger CSV",
                callback_data="rep_csv_ledger",
            ),
        ],
        [
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_menu_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Settings menu options."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🌐 ቋንቋ ቀይር / Change Language",
                callback_data="set_lang_toggle",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎯 የታለመውን ትርፍ መቶኛ ቀይር" if lang == "am" else "🎯 Change Target Profit Margin",
                callback_data="set_margin_change",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏷️ የንግድ ስም ቀይር" if lang == "am" else "🏷️ Change Business Name",
                callback_data="set_name_change",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💾 የዳታቤዝ ባካፕ ውሰድ (Backup)" if lang == "am" else "💾 Database Backup",
                callback_data="set_backup_now",
            ),
        ],
        [
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_keyboard(lang: str = "am") -> InlineKeyboardMarkup:
    """Simple cancel button."""
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="flow_cancel")]])
