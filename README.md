# 🧵 ተዋቡ ERP (Tewabu ERP)
### Tailor House Cost & Profit Manager for Ethiopian Tailoring Businesses 🇪🇹

**ተዋቡ ERP (Tewabu ERP)** is a professional Telegram bot application tailored specifically for Ethiopian fashion designers, traditional Shemma/Habesha dressmakers, and tailoring workshops. It automates clothing production expense tracking, determines optimal selling prices with decimal precision, flags potential losses, tracks customer orders, and provides financial reports with visual charts and CSV exports.

---

## 🌟 Key Features

1. **Guided 11-Step Clothing Design Workflow**:
   - Collects the 6 standard Ethiopian tailoring expense categories step-by-step:
     1. **መነን & ገቨር** (Traditional Fabric / Shemma & Lining)
     2. **ክር** (Embroidery & Sewing Threads)
     3. **ጠላፊ** (Hand embroidery craft / Telafe labor)
     4. **ሰፊ** (Tailoring & stitching labor / Sefi)
     5. **ዲዛይነር** (Designer creative fee)
     6. **ተያያዥ ወጪ** (Miscellaneous & related costs)
   - Allows adding optional custom extra expenses (zippers, packaging, transport).
   - Navigation support with **Back**, **Skip (0 ETB)**, and **Cancel** buttons at every stage.

2. **Accurate Financial Calculations (`decimal.Decimal`)**:
   - All currency arithmetic is performed using Python's `decimal.Decimal` with `ROUND_HALF_UP` to prevent floating-point discrepancies.
   - **Total Production Cost**: $\sum \text{expenses}$
   - **Break-even Selling Price**: $\text{Total Cost}$
   - **Recommended Optimal Price**: $\frac{\text{Total Cost}}{1 - \text{Target Profit Margin}}$
   - **Actual Profit**: $\text{Actual Selling Price} - \text{Total Cost}$
   - **Profit Margin Percentage**: $\left(\frac{\text{Actual Profit}}{\text{Actual Selling Price}}\right) \times 100$

3. **Color-Coded Status Badges**:
   - 🔴 **ኪሳራ (LOSS)**: Selling price below total cost. Displays exact loss amount.
   - ⚖️ **ወጪና ገቢ እኩል (BREAK-EVEN)**: Selling price equals total cost.
   - 🟡 **ትርፍ አለው (ከዒላማው በታች)**: Profitable, but lower than target margin.
   - 🪙 **ተመራጭ መሸጫ ዋጋ (RECOMMENDED OPTIMAL PRICE - GOLD)**: Achieves exact target profit margin.
   - 🟢 **ከተጠበቀው ትርፍ በላይ (ABOVE TARGET PROFIT)**: Selling price exceeds optimal target.

4. **Interactive Price Simulator**:
   - Test various hypothetical selling prices against production costs in real time.
   - Instant feedback with color status, profit amount, and profit percentage.

5. **Design History & Catalog**:
   - Browse saved designs with pagination and live search.
   - View expense breakdowns, edit selling prices, or delete records.

6. **Order Management**:
   - Track orders across stages:
     - ⏳ **በመጠባበቅ ላይ (Pending)**
     - 🪡 **በስራ ላይ (In Production)**
     - ✅ **የተጠናቀቀ (Completed)**
     - 📦 **የተረከበ (Delivered)**
     - 🚫 **የተሰረዘ (Cancelled)**
   - Record advance payments and automatically track remaining balance due.
   - Completing an order automatically updates realized income in the financial ledger.

7. **Business Dashboard**:
   - High-level KPIs: Total designs, total production expenses, completed revenue, realized net profit, expected profit from pending orders, loss-making designs, and top performers.
   - **Strict Financial Isolation**: Pending orders are *never* counted as completed revenue until completed or delivered.

8. **Financial Reports & Visual Charts**:
   - Daily, weekly, and monthly summaries.
   - High-resolution visual charts generated via `matplotlib` (rendered with native Ethiopian font support).
   - Instant CSV data export for designs and financial ledgers.

9. **Security, Isolation & Reliability**:
   - Multi-tenant architecture ensuring complete data privacy per business owner.
   - Automated timestamped database backups.
   - Full support for Amharic (primary) and English localization.

---

## 🏗️ Project Architecture

```
tewabu-erp/
├── .env.example             # Template for environment secrets
├── .gitignore               # Ignored files, databases, logs, venv
├── bot.py                   # Telegram bot entrypoint
├── pytest.ini               # Pytest async and path configuration
├── requirements.txt         # Production dependencies
│
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic settings & env manager
│
├── core/
│   ├── __init__.py
│   ├── calculations.py      # Decimal financial calculations & status logic
│   └── constants.py         # Enums, statuses, expense categories
│
├── database/
│   ├── __init__.py
│   ├── engine.py            # Async SQLAlchemy engine (aiosqlite)
│   ├── models.py            # Users, Businesses, Designs, Expenses, Orders, Ledger
│   └── crud.py              # Isolated business data CRUD operations
│
├── localization/
│   ├── __init__.py
│   └── i18n.py              # Amharic (primary) & English translations
│
├── keyboards/
│   ├── __init__.py
│   └── inline.py            # Inline keypads (Main menu, steps, pagination)
│
├── handlers/
│   ├── __init__.py          # Router registry
│   ├── common.py            # /start, /help, /cancel, navigation
│   ├── new_design.py        # 11-step guided design & costing workflow (FSM)
│   ├── cost_calc.py         # Quick cost calculator
│   ├── simulator.py         # Interactive selling price simulator
│   ├── history.py           # Design history, view, search, edit, delete
│   ├── orders.py            # Order management & status transitions
│   ├── dashboard.py         # KPI business dashboard
│   ├── reports.py           # Daily/weekly/monthly reports, CSV & charts
│   └── settings.py          # Profit margin, language, business name, backups
│
├── services/
│   ├── __init__.py
│   ├── chart_service.py     # Matplotlib visual chart generator
│   ├── report_service.py    # Report aggregations & CSV export
│   └── backup_service.py    # SQLite database backup manager
│
├── middlewares/
│   ├── __init__.py
│   └── auth_middleware.py   # Automatic registration & tenant isolation
│
└── tests/
    ├── test_calculations.py # Unit tests for Decimal financial formulas
    ├── test_crud.py         # Database CRUD & tenant isolation tests
    ├── test_reports.py      # Report summary and chart generator tests
    └── test_simulator.py    # Multi-tier price simulation tests
```

---

## 🚀 Quick Setup & Installation

### 1. Clone or Open the Repository
```bash
cd C:\Users\Admin\.gemini\antigravity\scratch\tewabu-erp
```

### 2. Activate Virtual Environment
```bash
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather):
```ini
BOT_TOKEN=7123456789:AAHq_YourSecretBotTokenHere
DATABASE_URL=sqlite+aiosqlite:///tewabu_erp.db
DEFAULT_CURRENCY=ETB
DEFAULT_PROFIT_MARGIN=0.25
DEFAULT_LANGUAGE=am
LOG_LEVEL=INFO
```

### 5. Run the Bot
```bash
python bot.py
```

The database tables will be created automatically on the first run.

---

## 🧪 Running Automated Tests

Run the test suite covering calculation accuracy, async database operations, tenant isolation, and chart rendering:
```bash
python -m pytest
```

All 16 tests will execute and pass:
```
============================= test session starts =============================
collected 16 items

tests\test_calculations.py ........                                      [ 50%]
tests\test_crud.py ....                                                  [ 75%]
tests\test_reports.py ...                                                [ 93%]
tests\test_simulator.py .                                                [100%]

============================= 16 passed in 3.37s ==============================
```

---

## 📱 Telegram Commands & Menu

- `/start` - Start bot, register business, open main menu.
- `/help` - View complete user guide, formula explanations, and color status definitions.
- `/cancel` - Cancel active input or workflow and return to the main menu.

### Main Menu Inline Actions:
- ➕ **አዲስ ዲዛይን (New Design)**: Guided 11-step expense entry and optimal pricing.
- 🧮 **ፈጣን የወጪ ማስያ (Cost Calculator)**: Quick calculations without saving.
- 🎯 **የዋጋ አስመሳይ (Price Simulator)**: Test arbitrary selling prices with instant color indicators.
- 📊 **የንግድ ዳሽቦርድ (Dashboard)**: Revenue, realized profit, pending orders, and top designs.
- 📜 **የዲዛይን ታሪክ (Design History)**: Browse, search, edit, or delete previous designs.
- 📦 **የትዕዛዝ ክትትል (Order Manager)**: Manage customer orders and track payments.
- 📈 **የፋይናንስ ሪፖርት (Reports)**: Daily/weekly/monthly summaries, charts & CSV exports.
- ⚙️ **ቅንብሮች (Settings)**: Change profit margin, toggle language (Amharic/English), rename business, download database backups.
