"""
Chart generation service using Matplotlib for Tewabu ERP.
Generates high-resolution visual charts for financial summaries and expense breakdowns.
"""

from pathlib import Path
from typing import Dict, Any, List
from decimal import Decimal
import io
import matplotlib
matplotlib.use("Agg")  # Non-interactive background renderer
import matplotlib.pyplot as plt

# Prefer Windows built-in Ethiopian fonts (Nyala, Ebrima) so Ge'ez renders natively
plt.rcParams["font.sans-serif"] = ["Nyala", "Ebrima", "Segoe UI Historic", "DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False

def generate_expenses_pie_chart(expenses_breakdown: List[Dict[str, Any]], title: str = "የወጪ ክፍፍል (Expenses Breakdown)") -> bytes:
    """
    Generate a pie chart of expense items and return PNG bytes.
    Uses safe bilingual labels to prevent glyph fallback issues.
    """
    labels = []
    values = []

    label_map = {
        "menen_gever": "Fabric/Lining (መነን)",
        "thread": "Thread (ክር)",
        "embroidery": "Embroidery (ጠላፊ)",
        "sewing": "Sewing (ሰፊ)",
        "designer": "Designer (ዲዛይነር)",
        "related_expenses": "Related/Misc (ተያያዥ)",
    }

    for item in expenses_breakdown:
        amt = float(item["amount"])
        if amt > 0:
            key = item.get("category_key", "")
            lbl = label_map.get(key, item.get("category_name", "Extra"))
            labels.append(lbl)
            values.append(amt)

    if not values:
        # Default empty chart
        labels = ["No expenses recorded"]
        values = [1]

    plt.figure(figsize=(7, 6), dpi=150)
    colors = ["#4A90E2", "#50E3C2", "#F5A623", "#E94E77", "#9013FE", "#B8E986", "#D0021B"]
    
    wedges, texts, autotexts = plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%" if sum(values) > 1 else "",
        startangle=140,
        colors=colors[:len(values)],
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),  # Donut chart
        pctdistance=0.75,
    )
    
    for at in autotexts:
        at.set_color("black")
        at.set_fontsize(9)
        at.set_weight("bold")

    plt.title(title, fontsize=13, fontweight="bold", pad=20)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.getvalue()

def generate_financial_bar_chart(
    revenue: Decimal,
    costs: Decimal,
    profit: Decimal,
    title: str = "የፋይናንስ ሁኔታ (Financial Performance - ETB)",
) -> bytes:
    """
    Generate a bar chart comparing Revenue, Costs, and Net Profit in ETB.
    """
    categories = ["Revenue (ገቢ)", "Total Costs (ወጪ)", "Net Profit (ትርፍ)"]
    amounts = [float(revenue), float(costs), float(profit)]
    colors = ["#2ECC71", "#E74C3C", "#F39C12" if profit >= 0 else "#C0392B"]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    bars = ax.bar(categories, amounts, color=colors, width=0.55, edgecolor="black", linewidth=0.8)

    ax.set_ylabel("Amount in ETB (ብር)", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Add numeric labels on top of bars
    for bar in bars:
        height = bar.get_height()
        va = "bottom" if height >= 0 else "top"
        ax.annotate(
            f"{height:,.2f} ETB",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4 if height >= 0 else -12),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.getvalue()
