# deductions_tool.py
"""
Deductions Tool for LangChain Agent.

This tool allows the agent to validate and calculate tax deductions
based on user input, returning detailed breakdown for the tax calculation.
"""

from langchain.tools import BaseTool
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import json

from services.deductions.deductions_service import deductions_service


class DeductionsInput(BaseModel):
    """Input schema for deductions calculation tool."""
    
    # Basic info
    income: float = Field(description="Taxpayer's annual income")
    year: str = Field(default="2024-25", description="Tax year")
    
    # Working from home
    wfh_hours: Optional[int] = Field(None, description="Hours worked from home")
    wfh_use_fixed_rate: bool = Field(True, description="Use fixed rate method for WFH")
    
    # Car expenses
    cars: Optional[list] = Field(None, description="List of car expense entries")
    
    # Phone & internet
    phone_internet_work_use_pct: Optional[float] = Field(None, description="Work use percentage for phone/internet")
    phone_internet_incidental_claims: bool = Field(False, description="Use incidental claims method")
    
    # Clothing & laundry
    clothing_work_only_loads: Optional[int] = Field(None, description="Number of work-only laundry loads")
    clothing_mixed_loads: Optional[int] = Field(None, description="Number of mixed laundry loads")
    clothing_purchases: Optional[float] = Field(None, description="Cost of work clothing purchases")
    
    # Tools & equipment
    tools: Optional[list] = Field(None, description="List of tool/equipment purchases")
    
    # Donations
    donations_dgr_amount: Optional[float] = Field(None, description="Amount donated to DGR organizations")
    donations_bucket_amount: Optional[float] = Field(None, description="Bucket donation amount")
    donations_is_dgr_confirmed: bool = Field(False, description="DGR status confirmed")
    
    # Union & professional fees
    union_fees: Optional[float] = Field(None, description="Union and professional fees")
    
    # Tax agent fees
    tax_agent_fees: Optional[float] = Field(None, description="Tax agent/accountant fees")
    
    # Personal super contributions
    personal_super_amount: Optional[float] = Field(None, description="Personal super contributions")


class DeductionsTool(BaseTool):
    """Tool for calculating tax deductions."""
    
    name = "calculate_deductions"
    description = """
    Calculate and validate tax deductions for Australian taxpayers (2024-25).
    
    Use this tool when users mention any deductible expenses such as:
    - Working from home expenses
    - Car expenses for work travel
    - Phone/internet for work use
    - Work clothing and laundry
    - Tools and equipment for work
    - Union or professional fees
    - Donations to charity
    - Tax agent fees
    - Personal super contributions
    
    Returns detailed breakdown of claimed vs allowed deductions with explanations.
    """
    
    args_schema = DeductionsInput
    
    def _run(self, **kwargs) -> str:
        """Execute deductions calculation."""
        try:
            # Check if feature is enabled
            if not deductions_service.is_feature_enabled():
                return json.dumps({
                    "error": "Deductions feature is not currently available",
                    "total_allowed": 0,
                    "message": "Please contact support if you need deductions calculated"
                })
            
            # Extract parameters
            income = kwargs.get("income")
            year = kwargs.get("year", "2024-25")
            
            if not income or income <= 0:
                return json.dumps({
                    "error": "Valid income amount is required for deductions calculation",
                    "total_allowed": 0
                })
            
            # Prepare deductions data
            deductions_data = {
                key: value for key, value in kwargs.items() 
                if key not in ["income", "year"] and value is not None
            }
            
            # Use the deductions service
            result = deductions_service.validate_and_calculate_deductions(
                deductions_data, income, year
            )
            
            # Format response for agent
            response = {
                "success": True,
                "total_allowed": result["total_allowed"],
                "line_items": result["line_items"],
                "conflicts": result["conflicts"],
                "warnings": result["warnings"],
                "summary": self._generate_summary(result)
            }
            
            return json.dumps(response, indent=2)
            
        except ValueError as e:
            return json.dumps({
                "error": str(e),
                "total_allowed": 0
            })
        except Exception as e:
            return json.dumps({
                "error": f"Calculation failed: {str(e)}",
                "total_allowed": 0
            })
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of deductions."""
        total = result["total_allowed"]
        items = result["line_items"]
        conflicts = result["conflicts"]
        warnings = result["warnings"]
        
        summary_parts = []
        
        # Total summary
        summary_parts.append(f"Total deductions allowed: ${total:,.2f}")
        
        # Key deductions
        significant_items = [item for item in items if item["allowed"] > 0]
        if significant_items:
            summary_parts.append("\nKey deductions:")
            for item in significant_items[:5]:  # Top 5
                summary_parts.append(f"- {item['name']}: ${item['allowed']:,.2f}")
        
        # Conflicts
        if conflicts:
            summary_parts.append(f"\nConflicts detected: {len(conflicts)}")
            for conflict in conflicts:
                if conflict == "phone_internet_blocked_by_wfh":
                    summary_parts.append("- Phone/internet expenses blocked due to WFH fixed rate method")
        
        # Warnings
        if warnings:
            summary_parts.append(f"\nWarnings: {len(warnings)}")
            for warning in warnings:
                if warning == "personal_super_may_exceed_concessional_cap":
                    summary_parts.append("- Personal super contributions may exceed $30,000 concessional cap")
        
        return "\n".join(summary_parts)


# Export the tool instance
deductions_tool = DeductionsTool()