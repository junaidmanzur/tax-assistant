# tax_tool.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# --- 1) Arguments schema for the tool ---
class TaxArgs(BaseModel):
    income: float = Field(..., description="Annual taxable income in AUD")
    has_private_health: bool = Field(..., description="True if user had private hospital cover all year")
    tax_year: Optional[int] = Field(default=2024, description="Financial year for calculation (default 2024–25)")
    # Optional: allow overriding where rule files live (handy in dev)
    rules_dir: Optional[str] = Field(default="rules", description="Directory containing tax_rules_<year>.json")

# --- 2) Core calculation helpers ---
def load_tax_rules(tax_year: int, rules_dir: str | Path = "rules") -> Dict[str, Any]:
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

def calculate_mls(income: float, has_private_health: bool, mls_cfg: Optional[Dict[str, Any]]) -> float:
    if not mls_cfg:
        return 0.0
    if has_private_health and mls_cfg.get("private_health_exempt", True):
        return 0.0
    for tier in sorted(mls_cfg.get("tiers", []), key=lambda x: float(x["min_income"])):
        t_min = float(tier["min_income"])
        t_max = float(tier["max_income"]) if tier.get("max_income") is not None else float("inf")
        if t_min <= income <= t_max:
            return income * float(tier.get("rate", 0.0))
    return 0.0

# ---- Orchestrator ----
def calculate_tax(
    income: float,
    has_private_health: bool,
    tax_year: int = 2024,
    rules_dir: str | Path = "rules",
) -> Dict[str, float]:
    """
    Calculate Australian individual income tax for the given year by loading
    rules from 'tax_rules_<year>.json' in rules_dir, applying progressive
    brackets, Medicare levy, and MLS (if applicable).
    """
    rules = load_tax_rules(tax_year, rules_dir)
    base_tax = calculate_income_tax(income, rules["marginal_tax_rates"])
    medicare_levy = calculate_medicare_levy(income, rules["medicare_levy"])
    mls = calculate_mls(income, has_private_health, rules.get("medicare_levy_surcharge"))
    total_tax = round(base_tax + medicare_levy + mls, 2)
    return {
        "base_tax": round(base_tax, 2),
        "medicare_levy": round(medicare_levy, 2),
        "mls": round(mls, 2),
        "total_tax": total_tax,
        "take_home": round(income - total_tax, 2),
    }

# --- 3) LangChain StructuredTool wrapper ---
calculate_tax_tool = StructuredTool.from_function(
    name="calculate_tax",
    description="Calculate Australian individual income tax using tax_rules_<year>.json (progressive brackets + Medicare levy + optional MLS).",
    func=calculate_tax,
    args_schema=TaxArgs,
)
