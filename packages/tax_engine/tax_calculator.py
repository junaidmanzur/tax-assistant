# tax_calculator.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

def load_tax_rules(tax_year: int, rules_dir: str | Path = "../tax_rules") -> Dict[str, Any]:
    """
    Load tax rules from a file named tax_rules_<year>.json (e.g., tax_rules_2024.json).
    Raises a helpful error if not present or malformed.
    """
    filename = f"tax_rules_{tax_year}.json"
    path = Path(rules_dir) / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Tax rules file not found: {path}. "
            f"Expected a file named 'tax_rules_{tax_year}.json' in '{rules_dir}'."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON rules file {path}: {e}") from e

    # minimal structure checks
    for key in ("marginal_tax_rates", "medicare_levy"):
        if key not in data:
            raise KeyError(f"Rules file {path} missing required key: '{key}'")
    return data

def calculate_income_tax(income: float, brackets: List[Dict[str, Any]]) -> float:
    if income <= 0:
        return 0.0
    tax = 0.0
    for b in sorted(brackets, key=lambda x: float(x["min_income"])):
        start = float(b["min_income"])
        end = float(b["max_income"]) if b.get("max_income") is not None else float("inf")
        rate = float(b["rate"])
        if income <= start:
            break
        taxable_amount = max(0.0, min(income, end) - start)
        tax += taxable_amount * rate
        if income <= end:
            break
    return tax

def calculate_medicare_levy(income: float, medicare_cfg: Dict[str, Any]) -> float:
    rate = float(medicare_cfg.get("rate", 0.02))
    return max(0.0, income * rate)

def get_mls_rate_single(income: float, rules: Dict[str, Any]) -> float:
    """Get MLS rate for single taxpayer."""
    mls_cfg = rules.get("medicare_levy_surcharge", {})
    tiers = mls_cfg.get("single_tiers", mls_cfg.get("tiers", []))
    
    for tier in sorted(tiers, key=lambda x: float(x["min_income"])):
        t_min = float(tier["min_income"])
        t_max = float(tier["max_income"]) if tier.get("max_income") is not None else float("inf")
        if t_min <= income <= t_max:
            return float(tier.get("rate", 0.0))
    return 0.0

def get_mls_rate_family(combined_income: float, dependents: int, rules: Dict[str, Any]) -> float:
    """Get MLS rate for family taxpayer with dependent child uplift."""
    mls_cfg = rules.get("medicare_levy_surcharge", {})
    family_tiers = mls_cfg.get("family_tiers", [])
    child_increment = float(mls_cfg.get("family_dependent_child_increment", 1500))
    
    # Calculate uplift: $1,500 per dependent child after the first
    uplift = max(dependents - 1, 0) * child_increment
    
    for tier in sorted(family_tiers, key=lambda x: float(x["min_income"])):
        t_min = float(tier["min_income"]) + uplift
        t_max_raw = tier.get("max_income")
        t_max = float(t_max_raw) + uplift if t_max_raw is not None else float("inf")
        
        if t_min <= combined_income <= t_max:
            return float(tier.get("rate", 0.0))
    return 0.0

def calculate_mls_base(income_for_mls: float, rate: float) -> float:
    """Calculate MLS amount based on income and rate."""
    return max(0.0, income_for_mls * rate)

def calculate_mls(
    income: float,
    has_private_health: bool,
    mls_cfg: Optional[Dict[str, Any]],
    filing_status: Literal["single", "family"] = "single",
    num_dependent_children: int = 0,
    combined_family_income_for_mls: Optional[float] = None
) -> float:
    """Calculate Medicare Levy Surcharge for single or family taxpayers."""
    if not mls_cfg:
        return 0.0
    if has_private_health and mls_cfg.get("private_health_exempt", True):
        return 0.0
    
    if filing_status == "single":
        rate = get_mls_rate_single(income, {"medicare_levy_surcharge": mls_cfg})
        return calculate_mls_base(income, rate)
    else:  # family
        if combined_family_income_for_mls is None:
            combined_family_income_for_mls = income
        rate = get_mls_rate_family(
            combined_family_income_for_mls, 
            num_dependent_children, 
            {"medicare_levy_surcharge": mls_cfg}
        )
        return calculate_mls_base(income, rate)

def calculate_tax(
    income: float,
    has_private_health: bool,
    tax_year: int = 2024,
    rules_dir: str | Path = "../tax_rules",
    filing_status: Literal["single", "family"] = "single",
    num_dependent_children: int = 0,
    combined_family_income_for_mls: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate Australian individual income tax for the given year by loading
    rules from 'tax_rules_<year>.json' in rules_dir, applying progressive
    brackets, Medicare levy, and MLS (if applicable).
    """
    rules = load_tax_rules(tax_year, rules_dir)
    base_tax = calculate_income_tax(income, rules["marginal_tax_rates"])
    medicare_levy = calculate_medicare_levy(income, rules["medicare_levy"])
    mls = calculate_mls(
        income, 
        has_private_health, 
        rules.get("medicare_levy_surcharge"),
        filing_status,
        num_dependent_children,
        combined_family_income_for_mls
    )
    total_tax = round(base_tax + medicare_levy + mls, 2)
    return {
        "base_tax": round(base_tax, 2),
        "medicare_levy": round(medicare_levy, 2),
        "mls": round(mls, 2),
        "total_tax": total_tax,
        "take_home": round(income - total_tax, 2),
    }