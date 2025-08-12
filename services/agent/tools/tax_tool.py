# tax_tool.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# Import from the tax-engine package
from tax_engine import calculate_tax

# --- Arguments schema for the tool ---
class TaxArgs(BaseModel):
    income: float = Field(..., description="Annual taxable income in AUD")
    has_private_health: bool = Field(..., description="True if user had private hospital cover all year")
    tax_year: Optional[int] = Field(default=2024, description="Financial year for calculation (default 2024–25)")
    # Optional: allow overriding where rule files live (handy in dev)
    rules_dir: Optional[str] = Field(default="packages/tax_rules", description="Directory containing tax_rules_<year>.json")

# --- Wrapper function for the tool ---
def calculate_tax_wrapper(
    income: float,
    has_private_health: bool,
    tax_year: int = 2024,
    rules_dir: str = "packages/tax_rules",
):
    """Wrapper function that calls the tax engine with proper path handling."""
    return calculate_tax(income, has_private_health, tax_year, rules_dir)

# --- LangChain StructuredTool wrapper ---
calculate_tax_tool = StructuredTool.from_function(
    name="calculate_tax",
    description="Calculate Australian individual income tax using tax_rules_<year>.json (progressive brackets + Medicare levy + optional MLS).",
    func=calculate_tax_wrapper,
    args_schema=TaxArgs,
)
