"""
Core constants for Tewabu ERP (Tailor House Cost & Profit Manager).
"""

from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    IN_PRODUCTION = "IN_PRODUCTION"
    COMPLETED = "COMPLETED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class ProfitStatus(str, Enum):
    LOSS = "LOSS"                   # Selling price < total cost (🔴 RED)
    BREAK_EVEN = "BREAK_EVEN"       # Selling price == total cost (⚖️ NEUTRAL)
    BELOW_TARGET = "BELOW_TARGET"   # Total cost < Selling price < Optimal price (🟡 YELLOW/ORANGE)
    OPTIMAL = "OPTIMAL"             # Selling price == Optimal price (🪙 GOLD)
    ABOVE_TARGET = "ABOVE_TARGET"   # Selling price > Optimal price (🟢 ABOVE TARGET)

# The 6 core guided expense fields
STANDARD_EXPENSE_KEYS = [
    "menen_gever",
    "thread",
    "embroidery",
    "sewing",
    "designer",
    "related_expenses",
]

EXPENSE_NAMES_AM = {
    "menen_gever": "መነን & ገቨር",
    "thread": "ክር",
    "embroidery": "ጠላፊ",
    "sewing": "ሰፊ",
    "designer": "ዲዛይነር",
    "related_expenses": "ተያያዥ ወጪ",
}

EXPENSE_NAMES_EN = {
    "menen_gever": "Fabric & Lining (Menen/Gever)",
    "thread": "Thread",
    "embroidery": "Embroidery Craft (Telafe)",
    "sewing": "Tailoring / Sewing (Sefi)",
    "designer": "Designer Fee",
    "related_expenses": "Related / Misc Expenses",
}
