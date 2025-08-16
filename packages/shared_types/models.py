from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field

DEFAULT_THREAD = "default-thread"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(...)
    content: str = Field(...)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    thread_id: Optional[str] = Field(default=DEFAULT_THREAD)
    # Optional: pass extra config if you want
    config: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    output: str
    messages: List[Dict[str, Any]]


# Deductions models
class CarExpenseModel(BaseModel):
    """Car expense entry for API requests."""
    id: str
    method: Literal['cents_per_km', 'logbook']
    kms: Optional[int] = None
    work_use_pct: Optional[float] = None
    # Actual costs for logbook method
    fuel: Optional[float] = None
    servicing: Optional[float] = None
    insurance: Optional[float] = None
    interest_or_lease: Optional[float] = None
    depreciation: Optional[float] = None


class ToolExpenseModel(BaseModel):
    """Tool/equipment expense entry for API requests."""
    cost: float
    work_use_pct: float


class DeductionsRequestModel(BaseModel):
    """API request model for deductions calculation."""
    year: str = Field(default="2024-25")
    income: float
    
    # Working from home
    wfh_hours: Optional[int] = None
    wfh_use_fixed_rate: bool = True
    
    # Car expenses
    cars: List[CarExpenseModel] = Field(default_factory=list)
    
    # Phone & internet
    phone_internet_work_use_pct: Optional[float] = None
    phone_internet_incidental_claims: bool = False
    
    # Clothing & laundry
    clothing_work_only_loads: Optional[int] = None
    clothing_mixed_loads: Optional[int] = None
    clothing_purchases: Optional[float] = None
    
    # Tools & equipment
    tools: List[ToolExpenseModel] = Field(default_factory=list)
    
    # Donations
    donations_dgr_amount: Optional[float] = None
    donations_bucket_amount: Optional[float] = None
    donations_is_dgr_confirmed: bool = False
    
    # Union & professional fees
    union_fees: Optional[float] = None
    
    # Tax agent fees
    tax_agent_fees: Optional[float] = None
    
    # Personal super contributions
    personal_super_amount: Optional[float] = None


class DeductionLineItemModel(BaseModel):
    """Individual deduction line item result."""
    id: str
    category: str
    name: str
    claimed: float
    allowed: float
    reason: Optional[str] = None
    note: Optional[str] = None


class DeductionsValidationFlags(BaseModel):
    """Validation flags for deductions conflicts and warnings."""
    conflicts: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DeductionsPreviewResponse(BaseModel):
    """Response model for deductions preview endpoint."""
    total_allowed: float
    line_items: List[DeductionLineItemModel]
    engine_flags: DeductionsValidationFlags


class TaxCalculationWithDeductionsRequest(BaseModel):
    """Extended tax calculation request with deductions."""
    income: float
    has_private_health: bool = True
    filing_status: Literal["single", "family"] = "single"
    num_dependent_children: int = 0
    combined_family_income_for_mls: Optional[float] = None
    
    # Deductions (optional)
    deductions: Optional[DeductionsRequestModel] = None


class TaxCalculationWithDeductionsResponse(BaseModel):
    """Extended tax calculation response with deductions breakdown."""
    # Original tax calculation fields
    base_tax: float
    medicare_levy: float
    mls: float
    lito: float
    total_tax: float
    take_home: float
    
    # Deductions fields (when applicable)
    gross_income: float
    total_deductions: Optional[float] = None
    taxable_income: float
    deductions_breakdown: Optional[DeductionsPreviewResponse] = None