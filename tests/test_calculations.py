"""
Unit tests for Financial Calculations in Tewabu ERP.
"""

from decimal import Decimal
import pytest
from core.calculations import (
    calculate_design_financials,
    validate_margin,
    round_money,
    format_currency,
)
from core.constants import ProfitStatus

def test_round_money_and_decimal_precision():
    # Test strict decimal arithmetic without IEEE 754 floating point issues
    d1 = Decimal("10.055")
    assert round_money(d1) == Decimal("10.06")
    
    val = sum([Decimal("0.1"), Decimal("0.2"), Decimal("0.3")])
    assert val == Decimal("0.6")

def test_validate_margin():
    # Test percentage conversions and valid ranges
    assert validate_margin("25%") == Decimal("0.25")
    assert validate_margin("25") == Decimal("0.25")
    assert validate_margin(0.30) == Decimal("0.30")
    assert validate_margin(Decimal("0.0")) == Decimal("0.00")
    
    # Boundary / invalid margins
    with pytest.raises(ValueError):
        validate_margin("-5")
    with pytest.raises(ValueError):
        validate_margin("100")
    with pytest.raises(ValueError):
        validate_margin("100%")
    with pytest.raises(ValueError):
        validate_margin("150")

def test_optimal_selling_price_formula():
    """
    Test standard Ethiopian tailoring expense case:
    Fabric/Menen: 500 ETB
    Thread: 50 ETB
    Embroidery: 300 ETB
    Sewing: 200 ETB
    Designer: 100 ETB
    Related: 50 ETB
    Total Cost = 1,200 ETB.
    Target Margin = 20% (0.20)
    Optimal Price = 1,200 / (1 - 0.20) = 1,200 / 0.80 = 1,500.00 ETB.
    """
    expenses = {
        "menen": "500",
        "thread": "50",
        "embroidery": "300",
        "sewing": "200",
        "designer": "100",
        "related": "50",
    }
    res = calculate_design_financials(expenses=expenses, target_margin="20%")
    assert res.total_cost == Decimal("1200.00")
    assert res.break_even_price == Decimal("1200.00")
    assert res.optimal_price == Decimal("1500.00")

def test_profit_status_loss():
    # Selling price below cost => LOSS (RED)
    expenses = [Decimal("1000.00")]
    res = calculate_design_financials(expenses=expenses, target_margin="25%", actual_selling_price="800.00")
    assert res.status == ProfitStatus.LOSS
    assert res.loss_amount == Decimal("200.00")
    assert res.actual_profit == Decimal("-200.00")

def test_profit_status_break_even():
    # Selling price equals cost => BREAK EVEN (NEUTRAL)
    expenses = [Decimal("1000.00")]
    res = calculate_design_financials(expenses=expenses, target_margin="25%", actual_selling_price="1000.00")
    assert res.status == ProfitStatus.BREAK_EVEN
    assert res.loss_amount == Decimal("0.00")
    assert res.actual_profit == Decimal("0.00")

def test_profit_status_optimal():
    # Selling price equals optimal price => OPTIMAL (GOLD)
    # 750 / (1 - 0.25) = 1000
    expenses = [Decimal("750.00")]
    res = calculate_design_financials(expenses=expenses, target_margin="25%", actual_selling_price="1000.00")
    assert res.status == ProfitStatus.OPTIMAL
    assert res.actual_profit == Decimal("250.00")
    assert res.profit_margin_pct == Decimal("25.00")

def test_profit_status_above_target():
    # Selling price above optimal price => ABOVE TARGET (YELLOW/GREEN)
    expenses = [Decimal("750.00")]
    res = calculate_design_financials(expenses=expenses, target_margin="25%", actual_selling_price="1200.00")
    assert res.status == ProfitStatus.ABOVE_TARGET
    assert res.actual_profit == Decimal("450.00")

def test_format_currency():
    assert "1,250.00 ብር" in format_currency("1250", lang="am")
    assert "1,250.00 ETB" in format_currency("1250", lang="en")
