# tax_tool.py
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


# --- 1) Arguments schema for the tool ---
class TaxArgs(BaseModel):
    income: float = Field(..., description="Annual taxable income in AUD")
    has_private_health: bool = Field(..., description="True if user had private hospital cover all year")
    tax_year: Optional[int] = Field(default=2024, description="Financial year for calculation (default 2024–25)")


# --- 2) Core calculation function ---
def calculate_tax(income: float, has_private_health: bool, tax_year: int = 2024) -> dict:
    """
    Calculates Australian individual income tax for a simple MVP scenario:
    - Resident individual
    - One source of income
    - No deductions/offsets (except tax-free threshold)
    - Medicare Levy at 2%
    - MLS waived if has_private_health = True
    """

    # Tax brackets for 2024–25 (can be loaded from JSON in production)
    brackets = [
        (0, 18200, 0.00, 0),           # threshold_start, threshold_end, rate, base_tax
        (18201, 45000, 0.16, 0),
        (45001, 135000, 0.30, 5092),
        (135001, 190000, 0.37, 33592),
        (190001, float("inf"), 0.45, 54092),
    ]

    # Base tax
    base_tax = 0.0
    for start, end, rate, base in brackets:
        if income > start:
            taxable_amount = min(income, end) - start
            if start == 18201:
                base_tax += taxable_amount * rate
            elif start > 18201:
                base_tax = base + (income - start + 1) * rate
                break

    # Medicare levy (full rate, no low-income reduction for MVP)
    medicare_levy = 0.02 * income

    # Medicare Levy Surcharge
    mls = 0.0
    if not has_private_health:
        # MVP simplification: flat 1% MLS if income > $93k (single threshold)
        if income > 93000:
            mls = 0.01 * income

    total_tax = round(base_tax + medicare_levy + mls, 2)

    return {
        "base_tax": round(base_tax, 2),
        "medicare_levy": round(medicare_levy, 2),
        "mls": round(mls, 2),
        "total_tax": total_tax,
        "take_home": round(income - total_tax, 2)
    }


# --- 3) LangChain StructuredTool wrapper ---
calculate_tax_tool = StructuredTool.from_function(
    name="calculate_tax",
    description="Calculate Australian individual income tax for a simple scenario based on 2024–25 ATO rules.",
    func=calculate_tax,
    args_schema=TaxArgs
)
