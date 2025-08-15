# tax_tool.py
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# Import from the tax-engine package
from tax_engine import calculate_tax

# --- Arguments schema for the tool ---
class TaxArgs(BaseModel):
    income: float = Field(..., description="Annual taxable income in AUD")
    has_private_health: bool = Field(..., description="True if user had private hospital cover all year")
    tax_year: Optional[int] = Field(default=2024, description="Financial year for calculation (default 2024–25)")
    filing_status: Literal["single", "family"] = Field(default="single", description="Filing status: 'single' for individual, 'family' for couples/families with combined income")
    num_dependent_children: int = Field(default=0, description="Number of dependent children (for family MLS threshold uplift)")
    combined_family_income_for_mls: Optional[float] = Field(default=None, description="Combined family income for MLS calculation (if filing_status is 'family')")
    # Optional: allow overriding where rule files live (handy in dev)
    rules_dir: Optional[str] = Field(default="packages/tax_rules", description="Directory containing tax_rules_<year>.json")

# --- Wrapper function for the tool ---
def calculate_tax_wrapper(
    income: float,
    has_private_health: bool,
    tax_year: int = 2024,
    rules_dir: str = "packages/tax_rules",
    filing_status: Literal["single", "family"] = "single",
    num_dependent_children: int = 0,
    combined_family_income_for_mls: Optional[float] = None,
):
    """Wrapper function that calls the tax engine with proper path handling."""
    return calculate_tax(
        income=income,
        has_private_health=has_private_health,
        tax_year=tax_year,
        rules_dir=rules_dir,
        filing_status=filing_status,
        num_dependent_children=num_dependent_children,
        combined_family_income_for_mls=combined_family_income_for_mls,
    )

# --- LangChain StructuredTool wrapper ---
calculate_tax_tool = StructuredTool.from_function(
    name="calculate_tax",
    description="Calculate Australian individual income tax using tax_rules_<year>.json (progressive brackets + Medicare levy + optional MLS). IMPORTANT: Always ask user about filing status (single vs family) and family circumstances before using this tool, as MLS thresholds differ significantly between single and family taxpayers.",
    func=calculate_tax_wrapper,
    args_schema=TaxArgs,
)
