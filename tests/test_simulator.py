"""
Tests for Price Simulator logic and multi-tier pricing scenarios in Tewabu ERP.
"""

from decimal import Decimal
import pytest
from core.calculations import calculate_design_financials
from core.constants import ProfitStatus

def test_simulator_scenarios_on_habesha_dress():
    """
    Simulation test for a traditional Ethiopian dress:
    Total production expenses = 2,400.00 ETB
    Business target profit margin = 20% (0.20)
    Optimal price = 2400 / (1 - 0.20) = 3,000.00 ETB
    Expected profit at optimal = 600.00 ETB
    """
    total_cost = Decimal("2400.00")
    target_margin = Decimal("0.20")

    # Scenario 1: Tailor quotes 2,000 ETB (Loss)
    sim1 = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=Decimal("2000.00"),
    )
    assert sim1.status == ProfitStatus.LOSS
    assert sim1.loss_amount == Decimal("400.00")
    assert sim1.actual_profit == Decimal("-400.00")

    # Scenario 2: Tailor quotes 2,400 ETB (Break-even)
    sim2 = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=Decimal("2400.00"),
    )
    assert sim2.status == ProfitStatus.BREAK_EVEN
    assert sim2.loss_amount == Decimal("0.00")
    assert sim2.actual_profit == Decimal("0.00")

    # Scenario 3: Tailor quotes 2,700 ETB (Below target margin)
    sim3 = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=Decimal("2700.00"),
    )
    assert sim3.status == ProfitStatus.BELOW_TARGET
    assert sim3.actual_profit == Decimal("300.00")
    # Margin % = 300 / 2700 = 11.11% (< 20%)
    assert sim3.profit_margin_pct == Decimal("11.11")

    # Scenario 4: Tailor quotes 3,000 ETB (Exact Optimal Gold Target)
    sim4 = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=Decimal("3000.00"),
    )
    assert sim4.status == ProfitStatus.OPTIMAL
    assert sim4.actual_profit == Decimal("600.00")
    # Margin % = 600 / 3000 = 20.00%
    assert sim4.profit_margin_pct == Decimal("20.00")

    # Scenario 5: Tailor quotes 3,500 ETB (Above Target Profit)
    sim5 = calculate_design_financials(
        expenses=[total_cost],
        target_margin=target_margin,
        actual_selling_price=Decimal("3500.00"),
    )
    assert sim5.status == ProfitStatus.ABOVE_TARGET
    assert sim5.actual_profit == Decimal("1100.00")
    # Margin % = 1100 / 3500 = 31.43% (> 20%)
    assert sim5.profit_margin_pct == Decimal("31.43")
