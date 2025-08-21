# deductions_service.py
"""
Deductions Service - Business logic layer for tax deductions.

This service handles:
- Deductions validation and calculation
- Business rule enforcement
- Data transformation between formats
- Feature flag management
- Future: external integrations, caching, audit trails
"""

import os
from typing import Dict, Any, Optional
from packages.tax_engine.deductions_calculator import (
    DeductionsRequest as DeductionsRequestInternal,
    CarExpense as CarExpenseInternal,
    ToolExpense as ToolExpenseInternal,
    validate_and_calculate_deductions,
    DeductionsResult
)


class DeductionsService:
    """Service class for handling deductions business logic."""
    
    def __init__(self):
        self.feature_enabled = self._check_feature_flag()
    
    def _check_feature_flag(self) -> bool:
        """Check if deductions feature is enabled via runtime flag."""
        return os.getenv("ENABLE_DEDUCTIONS_FEATURE", "true").lower() == "true"
    
    def is_feature_enabled(self) -> bool:
        """Public method to check feature status."""
        # Refresh from environment on each check for runtime updates
        self.feature_enabled = self._check_feature_flag()
        return self.feature_enabled
    
    def set_feature_enabled(self, enabled: bool) -> bool:
        """Dynamically enable/disable the feature at runtime."""
        self.feature_enabled = enabled
        # Optionally persist to environment for this process
        os.environ["ENABLE_DEDUCTIONS_FEATURE"] = str(enabled).lower()
        return self.feature_enabled
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Get detailed feature status information."""
        return {
            "enabled": self.is_feature_enabled(),
            "env_var": os.getenv("ENABLE_DEDUCTIONS_FEATURE", "true"),
            "source": "environment_variable",
            "can_toggle": True
        }
    
    def validate_and_calculate_deductions(
        self,
        deductions_data: Dict[str, Any],
        income: float,
        year: str = "2024-25"
    ) -> Dict[str, Any]:
        """
        Main service method for deductions calculation.
        
        Args:
            deductions_data: Dictionary containing deduction inputs
            income: Taxpayer's income
            year: Tax year
            
        Returns:
            Dictionary with calculation results and metadata
        """
        if not self.feature_enabled:
            raise ValueError("Deductions feature is not enabled")
        
        # Convert input data to internal format
        internal_request = self._convert_to_internal_request(deductions_data, income, year)
        
        # Perform calculation using the tax engine
        result = validate_and_calculate_deductions(internal_request, income, year)
        
        # Convert result to service format
        return self._convert_result_to_service_format(result)
    
    def _convert_to_internal_request(
        self, 
        data: Dict[str, Any], 
        income: float, 
        year: str
    ) -> DeductionsRequestInternal:
        """Convert service input to internal calculator format."""
        
        # Convert cars data
        cars = []
        if "cars" in data and data["cars"]:
            for car_data in data["cars"]:
                cars.append(CarExpenseInternal(
                    id=car_data.get("id", ""),
                    method=car_data.get("method", "cents_per_km"),
                    kms=car_data.get("kms"),
                    work_use_pct=car_data.get("work_use_pct"),
                    fuel=car_data.get("fuel"),
                    servicing=car_data.get("servicing"),
                    insurance=car_data.get("insurance"),
                    interest_or_lease=car_data.get("interest_or_lease"),
                    depreciation=car_data.get("depreciation")
                ))
        
        # Convert tools data
        tools = []
        if "tools" in data and data["tools"]:
            for tool_data in data["tools"]:
                tools.append(ToolExpenseInternal(
                    cost=tool_data.get("cost", 0),
                    work_use_pct=tool_data.get("work_use_pct", 0)
                ))
        
        return DeductionsRequestInternal(
            year=year,
            wfh_hours=data.get("wfh_hours"),
            wfh_use_fixed_rate=data.get("wfh_use_fixed_rate", True),
            cars=cars,
            phone_internet_work_use_pct=data.get("phone_internet_work_use_pct"),
            phone_internet_incidental_claims=data.get("phone_internet_incidental_claims", False),
            clothing_work_only_loads=data.get("clothing_work_only_loads"),
            clothing_mixed_loads=data.get("clothing_mixed_loads"),
            clothing_purchases=data.get("clothing_purchases"),
            tools=tools,
            donations_dgr_amount=data.get("donations_dgr_amount"),
            donations_bucket_amount=data.get("donations_bucket_amount"),
            donations_is_dgr_confirmed=data.get("donations_is_dgr_confirmed", False),
            union_fees=data.get("union_fees"),
            tax_agent_fees=data.get("tax_agent_fees"),
            personal_super_amount=data.get("personal_super_amount")
        )
    
    def _convert_result_to_service_format(self, result: DeductionsResult) -> Dict[str, Any]:
        """Convert internal calculator result to service format."""
        
        line_items = []
        for item in result.line_items:
            line_items.append({
                "id": item.id,
                "category": item.category,
                "name": item.name,
                "claimed": item.claimed,
                "allowed": item.allowed,
                "reason": item.reason,
                "note": item.note
            })
        
        return {
            "total_allowed": result.total_allowed,
            "line_items": line_items,
            "conflicts": result.engine_flags.conflicts,
            "warnings": result.engine_flags.warnings,
            "feature_enabled": self.feature_enabled,
            "calculation_year": "2024-25"
        }
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Get current feature status and metadata."""
        return {
            "enabled": self.feature_enabled,
            "version": "2024-25",
            "supported_deductions": [
                "working_from_home_fixed_rate",
                "car_expenses",
                "phone_internet", 
                "clothing_laundry",
                "tools_equipment",
                "union_fees",
                "donations",
                "tax_agent_fees",
                "personal_super_contributions"
            ]
        }


# Global service instance
deductions_service = DeductionsService()