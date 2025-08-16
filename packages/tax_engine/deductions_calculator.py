# deductions_calculator.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Union
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class CarExpense:
    """Car expense entry for deductions calculation."""
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


@dataclass
class ToolExpense:
    """Tool/equipment expense entry for deductions calculation."""
    cost: float
    work_use_pct: float


@dataclass
class DeductionsRequest:
    """Request model for deductions calculation."""
    year: str = "2024-25"
    # Working from home
    wfh_hours: Optional[int] = None
    wfh_use_fixed_rate: bool = True
    
    # Car expenses
    cars: List[CarExpense] = field(default_factory=list)
    
    # Phone & internet
    phone_internet_work_use_pct: Optional[float] = None
    phone_internet_incidental_claims: bool = False
    
    # Clothing & laundry
    clothing_work_only_loads: Optional[int] = None
    clothing_mixed_loads: Optional[int] = None
    clothing_purchases: Optional[float] = None
    
    # Tools & equipment
    tools: List[ToolExpense] = field(default_factory=list)
    
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


@dataclass
class DeductionLineItem:
    """Individual deduction line item result."""
    id: str
    category: str
    name: str
    claimed: float
    allowed: float
    reason: Optional[str] = None
    note: Optional[str] = None


@dataclass
class EngineFlags:
    """Engine flags for conflicts and warnings."""
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DeductionsResult:
    """Result model for deductions calculation."""
    total_allowed: float
    line_items: List[DeductionLineItem]
    engine_flags: EngineFlags


def load_deductions_rules(tax_year: int, rules_dir: str | Path = "packages/tax_rules") -> List[Dict[str, Any]]:
    """
    Load deductions rules from the tax rules file.
    Returns the deductions_2024_25 section.
    """
    filename = f"tax_rules_{tax_year}.json"
    path = Path(rules_dir) / filename
    
    if not path.exists():
        raise FileNotFoundError(f"Tax rules file not found: {path}")
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON rules file {path}: {e}") from e
    
    deductions_key = f"deductions_{tax_year}_25"
    if deductions_key not in data:
        raise KeyError(f"Rules file {path} missing required key: '{deductions_key}'")
    
    return data[deductions_key]


def find_deduction_rule(rules: List[Dict[str, Any]], deduction_id: str) -> Optional[Dict[str, Any]]:
    """Find a specific deduction rule by ID."""
    for rule in rules:
        if rule.get("id") == deduction_id:
            return rule
    return None


def round_currency(amount: Union[float, Decimal, int]) -> float:
    """Round currency amount to 2 decimal places using banker's rounding."""
    if isinstance(amount, (float, int)):
        amount = Decimal(str(amount))
    return float(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate_wfh_deduction(
    wfh_hours: Optional[int],
    use_fixed_rate: bool,
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate working from home deduction."""
    rule = find_deduction_rule(rules, "ded_wfh_fixed_rate")
    if not rule:
        raise ValueError("WFH fixed rate rule not found in tax rules")
    
    if not wfh_hours or wfh_hours <= 0:
        return DeductionLineItem(
            id="ded_wfh_fixed_rate",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No hours claimed"
        )
    
    if not use_fixed_rate:
        return DeductionLineItem(
            id="ded_wfh_fixed_rate",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            reason="Fixed rate method not selected"
        )
    
    rate_per_hour = float(rule["calculation"]["rate_per_hour"])
    claimed_amount = wfh_hours * rate_per_hour
    
    return DeductionLineItem(
        id="ded_wfh_fixed_rate",
        category="work-related",
        name=rule["name"],
        claimed=round_currency(claimed_amount),
        allowed=round_currency(claimed_amount),
        note=f"{wfh_hours} hours × ${rate_per_hour}/hour"
    )


def calculate_car_deductions(
    cars: List[CarExpense],
    rules: List[Dict[str, Any]]
) -> List[DeductionLineItem]:
    """Calculate car expense deductions."""
    rule = find_deduction_rule(rules, "ded_car_expenses")
    if not rule:
        raise ValueError("Car expenses rule not found in tax rules")
    
    line_items = []
    
    for i, car in enumerate(cars):
        if car.method == "cents_per_km":
            cents_method = None
            for method in rule["calculation"]["methods"]:
                if method["name"] == "Cents per kilometre":
                    cents_method = method
                    break
            
            if not cents_method:
                raise ValueError("Cents per km method not found in rules")
            
            if not car.kms or car.kms <= 0:
                line_items.append(DeductionLineItem(
                    id=f"ded_car_expenses_{car.id}",
                    category="work-related",
                    name=f"{rule['name']} - {car.id}",
                    claimed=0.0,
                    allowed=0.0,
                    note="No kilometres claimed"
                ))
                continue
            
            rate_per_km = float(cents_method["rate_per_km"])
            max_km = int(cents_method["max_km"])
            
            kms_allowed = min(car.kms, max_km)
            claimed_amount = car.kms * rate_per_km
            allowed_amount = kms_allowed * rate_per_km
            
            reason = None
            if car.kms > max_km:
                reason = f"Limited to {max_km} km maximum"
            
            line_items.append(DeductionLineItem(
                id=f"ded_car_expenses_{car.id}",
                category="work-related",
                name=f"{rule['name']} - {car.id}",
                claimed=round_currency(claimed_amount),
                allowed=round_currency(allowed_amount),
                reason=reason,
                note=f"{kms_allowed} km × ${rate_per_km}/km (cents per km method)"
            ))
        
        elif car.method == "logbook":
            if not car.work_use_pct or car.work_use_pct <= 0:
                line_items.append(DeductionLineItem(
                    id=f"ded_car_expenses_{car.id}",
                    category="work-related",
                    name=f"{rule['name']} - {car.id}",
                    claimed=0.0,
                    allowed=0.0,
                    note="No work use percentage provided"
                ))
                continue
            
            work_pct = min(car.work_use_pct, 100.0) / 100.0
            
            total_actual_costs = sum(filter(None, [
                car.fuel or 0,
                car.servicing or 0,
                car.insurance or 0,
                car.interest_or_lease or 0,
                car.depreciation or 0
            ]))
            
            if total_actual_costs <= 0:
                line_items.append(DeductionLineItem(
                    id=f"ded_car_expenses_{car.id}",
                    category="work-related",
                    name=f"{rule['name']} - {car.id}",
                    claimed=0.0,
                    allowed=0.0,
                    note="No actual costs provided for logbook method"
                ))
                continue
            
            allowed_amount = total_actual_costs * work_pct
            
            line_items.append(DeductionLineItem(
                id=f"ded_car_expenses_{car.id}",
                category="work-related",
                name=f"{rule['name']} - {car.id}",
                claimed=round_currency(total_actual_costs),
                allowed=round_currency(allowed_amount),
                note=f"${total_actual_costs:.2f} × {work_pct*100:.1f}% work use (logbook method)"
            ))
    
    return line_items


def calculate_phone_internet_deduction(
    work_use_pct: Optional[float],
    incidental_claims: bool,
    wfh_hours: Optional[int],
    wfh_use_fixed_rate: bool,
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate phone & internet deduction."""
    rule = find_deduction_rule(rules, "ded_mobile_internet")
    if not rule:
        raise ValueError("Mobile internet rule not found in tax rules")
    
    # Check for WFH conflict
    if wfh_hours and wfh_hours > 0 and wfh_use_fixed_rate:
        return DeductionLineItem(
            id="ded_mobile_internet",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            reason="Excluded due to WFH fixed-rate for same hours"
        )
    
    if incidental_claims:
        # Simplified incidental method
        incidental_threshold = float(rule["calculation"]["simplified"]["incidental_threshold"])
        return DeductionLineItem(
            id="ded_mobile_internet",
            category="work-related",
            name=rule["name"],
            claimed=incidental_threshold,
            allowed=incidental_threshold,
            note="Incidental use claim (simplified method)"
        )
    
    if not work_use_pct or work_use_pct <= 0:
        return DeductionLineItem(
            id="ded_mobile_internet",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No work use percentage provided"
        )
    
    # For detailed method, we need actual bill amounts
    # Since we don't have bill amounts in the request, we'll note this requirement
    return DeductionLineItem(
        id="ded_mobile_internet",
        category="work-related",
        name=rule["name"],
        claimed=0.0,
        allowed=0.0,
        note=f"{work_use_pct}% work use specified - actual bill amounts needed for calculation"
    )


def calculate_clothing_laundry_deduction(
    work_only_loads: Optional[int],
    mixed_loads: Optional[int],
    purchases: Optional[float],
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate clothing & laundry deduction."""
    rule = find_deduction_rule(rules, "ded_clothing_laundry")
    if not rule:
        raise ValueError("Clothing laundry rule not found in tax rules")
    
    work_only_rate = float(rule["calculation"]["laundry_per_load_work_only"])
    mixed_rate = float(rule["calculation"]["laundry_per_load_mixed"])
    
    laundry_amount = 0.0
    laundry_notes = []
    
    if work_only_loads and work_only_loads > 0:
        work_only_amount = work_only_loads * work_only_rate
        laundry_amount += work_only_amount
        laundry_notes.append(f"{work_only_loads} work-only loads × ${work_only_rate}")
    
    if mixed_loads and mixed_loads > 0:
        mixed_amount = mixed_loads * mixed_rate
        laundry_amount += mixed_amount
        laundry_notes.append(f"{mixed_loads} mixed loads × ${mixed_rate}")
    
    purchase_amount = purchases or 0.0
    total_claimed = laundry_amount + purchase_amount
    
    note_parts = []
    if laundry_notes:
        note_parts.append(f"Laundry: {', '.join(laundry_notes)}")
    if purchase_amount > 0:
        note_parts.append(f"Purchases: ${purchase_amount:.2f}")
    
    if total_claimed <= 0:
        return DeductionLineItem(
            id="ded_clothing_laundry",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No clothing or laundry expenses claimed"
        )
    
    return DeductionLineItem(
        id="ded_clothing_laundry",
        category="work-related",
        name=rule["name"],
        claimed=round_currency(total_claimed),
        allowed=round_currency(total_claimed),
        note="; ".join(note_parts) if note_parts else None
    )


def calculate_tools_deductions(
    tools: List[ToolExpense],
    rules: List[Dict[str, Any]]
) -> List[DeductionLineItem]:
    """Calculate tools & equipment deductions."""
    rule = find_deduction_rule(rules, "ded_tools_equipment")
    if not rule:
        raise ValueError("Tools equipment rule not found in tax rules")
    
    immediate_threshold = float(rule["calculation"]["immediate_deduction_threshold"])
    line_items = []
    
    for i, tool in enumerate(tools):
        if tool.cost <= 0 or tool.work_use_pct <= 0:
            line_items.append(DeductionLineItem(
                id=f"ded_tools_equipment_{i}",
                category="work-related",
                name=f"{rule['name']} - Item {i+1}",
                claimed=0.0,
                allowed=0.0,
                note="Invalid cost or work use percentage"
            ))
            continue
        
        work_portion = tool.cost * (min(tool.work_use_pct, 100.0) / 100.0)
        
        if tool.cost <= immediate_threshold:
            # Immediate deduction allowed
            line_items.append(DeductionLineItem(
                id=f"ded_tools_equipment_{i}",
                category="work-related",
                name=f"{rule['name']} - Item {i+1}",
                claimed=round_currency(work_portion),
                allowed=round_currency(work_portion),
                note=f"${tool.cost:.2f} × {tool.work_use_pct:.1f}% work use (immediate deduction ≤$300)"
            ))
        else:
            # Above threshold - requires depreciation
            line_items.append(DeductionLineItem(
                id=f"ded_tools_equipment_{i}",
                category="work-related",
                name=f"{rule['name']} - Item {i+1}",
                claimed=round_currency(work_portion),
                allowed=0.0,
                reason=f"Asset >${immediate_threshold} requires depreciation calculation"
            ))
    
    return line_items


def calculate_union_fees_deduction(
    union_fees: Optional[float],
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate union fees deduction."""
    rule = find_deduction_rule(rules, "ded_union_fees")
    if not rule:
        raise ValueError("Union fees rule not found in tax rules")
    
    if not union_fees or union_fees <= 0:
        return DeductionLineItem(
            id="ded_union_fees",
            category="work-related",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No union fees claimed"
        )
    
    return DeductionLineItem(
        id="ded_union_fees",
        category="work-related",
        name=rule["name"],
        claimed=round_currency(union_fees),
        allowed=round_currency(union_fees),
        note="Full amount allowed"
    )


def calculate_donations_deduction(
    dgr_amount: Optional[float],
    bucket_amount: Optional[float],
    is_dgr_confirmed: bool,
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate donations deduction."""
    rule = find_deduction_rule(rules, "ded_donations")
    if not rule:
        raise ValueError("Donations rule not found in tax rules")
    
    bucket_limit = float(rule["calculation"]["bucket_donation_limit_no_receipt"])
    total_claimed = 0.0
    total_allowed = 0.0
    notes = []
    
    if dgr_amount and dgr_amount >= 2.0:  # Minimum $2 per eligibility
        if is_dgr_confirmed:
            total_claimed += dgr_amount
            total_allowed += dgr_amount
            notes.append(f"DGR donations: ${dgr_amount:.2f}")
        else:
            total_claimed += dgr_amount
            notes.append(f"DGR donations: ${dgr_amount:.2f} (DGR status not confirmed)")
    
    if bucket_amount and bucket_amount > 0:
        bucket_allowed = min(bucket_amount, bucket_limit)
        total_claimed += bucket_amount
        total_allowed += bucket_allowed
        if bucket_amount <= bucket_limit:
            notes.append(f"Bucket donations: ${bucket_amount:.2f}")
        else:
            notes.append(f"Bucket donations: ${bucket_amount:.2f} (limited to ${bucket_limit:.2f})")
    
    if total_claimed <= 0:
        return DeductionLineItem(
            id="ded_donations",
            category="personal",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No donations claimed"
        )
    
    return DeductionLineItem(
        id="ded_donations",
        category="personal",
        name=rule["name"],
        claimed=round_currency(total_claimed),
        allowed=round_currency(total_allowed),
        note="; ".join(notes) if notes else None
    )


def calculate_tax_agent_fees_deduction(
    tax_agent_fees: Optional[float],
    rules: List[Dict[str, Any]]
) -> DeductionLineItem:
    """Calculate tax agent fees deduction."""
    rule = find_deduction_rule(rules, "ded_tax_agent_fees")
    if not rule:
        raise ValueError("Tax agent fees rule not found in tax rules")
    
    if not tax_agent_fees or tax_agent_fees <= 0:
        return DeductionLineItem(
            id="ded_tax_agent_fees",
            category="personal",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No tax agent fees claimed"
        )
    
    return DeductionLineItem(
        id="ded_tax_agent_fees",
        category="personal",
        name=rule["name"],
        claimed=round_currency(tax_agent_fees),
        allowed=round_currency(tax_agent_fees),
        note="Full amount allowed"
    )


def calculate_personal_super_deduction(
    personal_super_amount: Optional[float],
    rules: List[Dict[str, Any]]
) -> tuple[DeductionLineItem, List[str]]:
    """Calculate personal super contributions deduction and return warnings."""
    rule = find_deduction_rule(rules, "ded_super_contributions")
    if not rule:
        raise ValueError("Super contributions rule not found in tax rules")
    
    warnings = []
    
    if not personal_super_amount or personal_super_amount <= 0:
        return (DeductionLineItem(
            id="ded_super_contributions",
            category="personal",
            name=rule["name"],
            claimed=0.0,
            allowed=0.0,
            note="No personal super contributions claimed"
        ), warnings)
    
    concessional_cap = float(rule["calculation"]["cap_concessional"])
    
    if personal_super_amount > concessional_cap:
        warnings.append(f"personal_super_may_exceed_concessional_cap")
    
    return (DeductionLineItem(
        id="ded_super_contributions",
        category="personal",
        name=rule["name"],
        claimed=round_currency(personal_super_amount),
        allowed=round_currency(personal_super_amount),
        note=f"Amount claimed (warning if >$30,000 concessional cap)"
    ), warnings)


def validate_and_calculate_deductions(
    request: DeductionsRequest,
    income: float,
    year: str = "2024-25"
) -> DeductionsResult:
    """
    Main function to validate and calculate all deductions.
    Returns detailed ledger and engine flags.
    """
    if year != "2024-25":
        raise ValueError(f"Unsupported tax year: {year}")
    
    # Load rules
    rules = load_deductions_rules(2024)
    
    line_items = []
    conflicts = []
    warnings = []
    
    # Calculate WFH deduction
    wfh_item = calculate_wfh_deduction(
        request.wfh_hours,
        request.wfh_use_fixed_rate,
        rules
    )
    line_items.append(wfh_item)
    
    # Calculate car deductions
    car_items = calculate_car_deductions(request.cars, rules)
    line_items.extend(car_items)
    
    # Calculate phone & internet deduction
    phone_item = calculate_phone_internet_deduction(
        request.phone_internet_work_use_pct,
        request.phone_internet_incidental_claims,
        request.wfh_hours,
        request.wfh_use_fixed_rate,
        rules
    )
    line_items.append(phone_item)
    
    # Track conflicts
    if (request.wfh_hours and request.wfh_hours > 0 and request.wfh_use_fixed_rate and
        (request.phone_internet_work_use_pct or request.phone_internet_incidental_claims)):
        conflicts.append("phone_internet_blocked_by_wfh")
    
    # Calculate clothing & laundry deduction
    clothing_item = calculate_clothing_laundry_deduction(
        request.clothing_work_only_loads,
        request.clothing_mixed_loads,
        request.clothing_purchases,
        rules
    )
    line_items.append(clothing_item)
    
    # Calculate tools deductions
    tools_items = calculate_tools_deductions(request.tools, rules)
    line_items.extend(tools_items)
    
    # Calculate union fees deduction
    union_item = calculate_union_fees_deduction(request.union_fees, rules)
    line_items.append(union_item)
    
    # Calculate donations deduction
    donations_item = calculate_donations_deduction(
        request.donations_dgr_amount,
        request.donations_bucket_amount,
        request.donations_is_dgr_confirmed,
        rules
    )
    line_items.append(donations_item)
    
    # Calculate tax agent fees deduction
    tax_agent_item = calculate_tax_agent_fees_deduction(request.tax_agent_fees, rules)
    line_items.append(tax_agent_item)
    
    # Calculate personal super deduction
    super_item, super_warnings = calculate_personal_super_deduction(
        request.personal_super_amount,
        rules
    )
    line_items.append(super_item)
    warnings.extend(super_warnings)
    
    # Calculate total allowed deductions
    total_allowed = sum(item.allowed for item in line_items)
    
    return DeductionsResult(
        total_allowed=round_currency(total_allowed),
        line_items=line_items,
        engine_flags=EngineFlags(
            conflicts=conflicts,
            warnings=warnings
        )
    )