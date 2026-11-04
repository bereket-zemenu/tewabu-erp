"""
Financial Calculation Engine for Tewabu ERP.
Uses Python decimal.Decimal for all monetary calculations to ensure absolute financial precision.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Any, Optional
from core.constants import ProfitStatus

TWO_PLACES = Decimal("0.01")

def to_decimal(value: Any) -> Decimal:
    """Safely convert float, int, str or Decimal to Decimal."""
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal("0.00")
    try:
        # Strip currency strings, commas and spaces
        cleaned = str(value).replace(",", "").replace(" ", "").replace("ETB", "").replace("ብር", "")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid monetary value: {value}")

def round_money(amount: Decimal) -> Decimal:
    """Round a Decimal amount to two decimal places using ROUND_HALF_UP."""
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def format_currency(amount: Decimal | float | int | str, currency: str = "ETB", lang: str = "am") -> str:
    """
    Format a Decimal monetary value with thousand separators and 2 decimal places.
    Example: 1,250.00 ETB or 1,250.00 ብር
    """
    dec = round_money(to_decimal(amount))
    symbol = "ብር" if lang == "am" else currency
    return f"{dec:,.2f} {symbol}"

def validate_margin(margin: Decimal | float | str) -> Decimal:
    """
    Validate target profit margin.
    Accepts decimal fraction (e.g. 0.25) or percentage string (e.g. '25' or '25%').
    Returns Decimal fraction between 0 and 0.9999 (0 <= margin < 1).
    """
    str_val = str(margin).replace("%", "").strip()
    dec = to_decimal(str_val)
    # If entered as whole percentage like 25, convert to 0.25
    if dec >= 1:
        dec = dec / Decimal("100")
    
    if dec < Decimal("0"):
        raise ValueError("Profit margin cannot be negative (መቶኛ ከዜሮ በታች ሊሆን አይችልም).")
    if dec >= Decimal("1"):
        raise ValueError("Profit margin must be less than 100% (መቶኛ ከ100% በታች መሆን አለበት).")
    
    return dec

class CalculationResult:
    def __init__(
        self,
        total_cost: Decimal,
        break_even_price: Decimal,
        optimal_price: Decimal,
        target_margin: Decimal,
        actual_selling_price: Optional[Decimal] = None,
        actual_profit: Optional[Decimal] = None,
        profit_margin_pct: Optional[Decimal] = None,
        loss_amount: Decimal = Decimal("0.00"),
        status: Optional[ProfitStatus] = None,
    ):
        self.total_cost = round_money(total_cost)
        self.break_even_price = round_money(break_even_price)
        self.optimal_price = round_money(optimal_price)
        self.target_margin = target_margin
        self.actual_selling_price = round_money(actual_selling_price) if actual_selling_price is not None else None
        self.actual_profit = round_money(actual_profit) if actual_profit is not None else None
        self.profit_margin_pct = round_money(profit_margin_pct) if profit_margin_pct is not None else None
        self.loss_amount = round_money(loss_amount)
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cost": self.total_cost,
            "break_even_price": self.break_even_price,
            "optimal_price": self.optimal_price,
            "target_margin": self.target_margin,
            "actual_selling_price": self.actual_selling_price,
            "actual_profit": self.actual_profit,
            "profit_margin_pct": self.profit_margin_pct,
            "loss_amount": self.loss_amount,
            "status": self.status.value if self.status else None,
        }

def calculate_design_financials(
    expenses: Dict[str, Any] | list[Any],
    target_margin: Decimal | float | str = Decimal("0.25"),
    actual_selling_price: Optional[Decimal | float | str] = None,
) -> CalculationResult:
    """
    Perform complete financial calculations for clothing design.
    
    Formula:
    - Total Cost = Sum of all expenses.
    - Break-even Price = Total Cost.
    - Optimal Price = Total Cost / (1 - Target Profit Margin).
    - Actual Profit = Actual Selling Price - Total Cost.
    - Loss Amount = Total Cost - Actual Selling Price (if selling < total cost).
    - Profit Margin % = (Actual Profit / Actual Selling Price) * 100 (if selling price > 0).
    """
    valid_margin = validate_margin(target_margin)
    
    # Calculate total cost from dict or list
    if isinstance(expenses, dict):
        total_cost = sum((to_decimal(v) for v in expenses.values()), Decimal("0.00"))
    else:
        total_cost = sum((to_decimal(v) for v in expenses), Decimal("0.00"))
    
    if total_cost < Decimal("0.00"):
        raise ValueError("Total production expenses cannot be negative.")
        
    break_even_price = total_cost
    
    # Optimal Price formula: Total Cost / (1 - Target Profit Margin)
    one_minus_margin = Decimal("1.00") - valid_margin
    if one_minus_margin > Decimal("0.00"):
        optimal_price = total_cost / one_minus_margin
    else:
        optimal_price = total_cost

    actual_selling_dec: Optional[Decimal] = None
    actual_profit_dec: Optional[Decimal] = None
    profit_margin_pct_dec: Optional[Decimal] = None
    loss_amount = Decimal("0.00")
    status: Optional[ProfitStatus] = None

    if actual_selling_price is not None:
        actual_selling_dec = to_decimal(actual_selling_price)
        if actual_selling_dec < Decimal("0.00"):
            raise ValueError("Selling price cannot be negative.")
            
        actual_profit_dec = actual_selling_dec - total_cost
        
        if actual_selling_dec > Decimal("0.00"):
            profit_margin_pct_dec = (actual_profit_dec / actual_selling_dec) * Decimal("100")
        else:
            profit_margin_pct_dec = Decimal("0.00")
            
        # Determine status and color codes
        if actual_selling_dec < total_cost:
            status = ProfitStatus.LOSS
            loss_amount = total_cost - actual_selling_dec
        elif actual_selling_dec == total_cost:
            status = ProfitStatus.BREAK_EVEN
        elif round_money(actual_selling_dec) == round_money(optimal_price):
            status = ProfitStatus.OPTIMAL
        elif actual_selling_dec > optimal_price:
            status = ProfitStatus.ABOVE_TARGET
        else:
            # Between break even and optimal
            status = ProfitStatus.BELOW_TARGET

    return CalculationResult(
        total_cost=total_cost,
        break_even_price=break_even_price,
        optimal_price=optimal_price,
        target_margin=valid_margin,
        actual_selling_price=actual_selling_dec,
        actual_profit=actual_profit_dec,
        profit_margin_pct=profit_margin_pct_dec,
        loss_amount=loss_amount,
        status=status,
    )
