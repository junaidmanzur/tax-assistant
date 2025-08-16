# tax_tool.py
from __future__ import annotations
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
import json

# Import from the tax-engine package
from tax_engine import calculate_tax
from services.deductions.deductions_service import deductions_service

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
    # Deductions support
    deductions_data: Optional[str] = Field(default=None, description="JSON string of deductions data from deductions tool (use calculate_deductions tool first)")

# --- Wrapper function for the tool ---
def calculate_tax_wrapper(
    income: float,
    has_private_health: bool,
    tax_year: int = 2024,
    rules_dir: str = "packages/tax_rules",
    filing_status: Literal["single", "family"] = "single",
    num_dependent_children: int = 0,
    combined_family_income_for_mls: Optional[float] = None,
    deductions_data: Optional[str] = None,
):
    """Wrapper function that calls the tax engine with optional deductions."""
    
    # Start with gross income
    gross_income = income
    total_deductions = 0.0
    deductions_breakdown = None
    
    # Process deductions if provided
    if deductions_data:
        try:
            # Parse deductions data from JSON
            deductions_result = json.loads(deductions_data)
            if deductions_result.get("success"):
                total_deductions = deductions_result.get("total_allowed", 0.0)
                deductions_breakdown = {
                    "total_allowed": total_deductions,
                    "line_items": deductions_result.get("line_items", []),
                    "conflicts": deductions_result.get("conflicts", []),
                    "warnings": deductions_result.get("warnings", [])
                }
        except (json.JSONDecodeError, KeyError) as e:
            # If deductions data is invalid, proceed without deductions
            total_deductions = 0.0
    
    # Calculate taxable income after deductions
    taxable_income = max(0.0, gross_income - total_deductions)
    
    # Calculate tax on taxable income
    tax_result = calculate_tax(
        income=taxable_income,
        has_private_health=has_private_health,
        tax_year=tax_year,
        rules_dir=rules_dir,
        filing_status=filing_status,
        num_dependent_children=num_dependent_children,
        combined_family_income_for_mls=combined_family_income_for_mls,
    )
    
    # Enhanced result with deductions information
    enhanced_result = {
        "gross_income": gross_income,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "base_tax": tax_result["base_tax"],
        "medicare_levy": tax_result["medicare_levy"],
        "mls": tax_result["mls"],
        "lito": tax_result["lito"],
        "total_tax": tax_result["total_tax"],
        "take_home": tax_result["take_home"],
    }
    
    # Add deductions breakdown if available
    if deductions_breakdown:
        enhanced_result["deductions_breakdown"] = deductions_breakdown
    
    return enhanced_result

# --- LangChain StructuredTool wrapper ---
calculate_tax_tool = StructuredTool.from_function(
    name="calculate_tax",
    description="Calculate Australian individual income tax using tax_rules_<year>.json (progressive brackets + Medicare levy + optional MLS). IMPORTANT: Always ask user about filing status (single vs family) and family circumstances before using this tool, as MLS thresholds differ significantly between single and family taxpayers. If user mentioned deductions, use calculate_deductions tool first, then pass the result as deductions_data parameter to this tool.",
    func=calculate_tax_wrapper,
    args_schema=TaxArgs,
)
