# test_deductions_calculator.py
import pytest
from decimal import Decimal
from pathlib import Path
import tempfile
import json

from deductions_calculator import (
    DeductionsRequest,
    CarExpense,
    ToolExpense,
    validate_and_calculate_deductions,
    calculate_wfh_deduction,
    calculate_car_deductions,
    calculate_phone_internet_deduction,
    calculate_clothing_laundry_deduction,
    calculate_tools_deductions,
    calculate_union_fees_deduction,
    calculate_donations_deduction,
    calculate_tax_agent_fees_deduction,
    calculate_personal_super_deduction,
    load_deductions_rules,
    find_deduction_rule,
    round_currency
)


@pytest.fixture
def sample_rules():
    """Sample rules data for testing."""
    return [
        {
            "id": "ded_wfh_fixed_rate",
            "name": "Working from home – fixed rate method",
            "category": "work-related",
            "calculation": {"rate_per_hour": 0.70}
        },
        {
            "id": "ded_car_expenses",
            "name": "Work-related car expenses",
            "category": "work-related",
            "calculation": {
                "methods": [
                    {
                        "name": "Cents per kilometre",
                        "rate_per_km": 0.88,
                        "max_km": 5000
                    },
                    {
                        "name": "Logbook",
                        "logbook_period_weeks": 12
                    }
                ]
            }
        },
        {
            "id": "ded_mobile_internet",
            "name": "Mobile phone and internet (work use)",
            "category": "work-related",
            "calculation": {
                "simplified": {"incidental_threshold": 50}
            }
        },
        {
            "id": "ded_clothing_laundry",
            "name": "Protective and occupation-specific clothing & laundry",
            "category": "work-related",
            "calculation": {
                "laundry_per_load_work_only": 1.00,
                "laundry_per_load_mixed": 0.50
            }
        },
        {
            "id": "ded_tools_equipment",
            "name": "Tools, equipment and other assets",
            "category": "work-related",
            "calculation": {"immediate_deduction_threshold": 300}
        },
        {
            "id": "ded_union_fees",
            "name": "Union fees and professional subscriptions",
            "category": "work-related",
            "calculation": "Full amount paid"
        },
        {
            "id": "ded_donations",
            "name": "Gifts and donations",
            "category": "personal",
            "calculation": {"bucket_donation_limit_no_receipt": 10}
        },
        {
            "id": "ded_tax_agent_fees",
            "name": "Cost of managing tax affairs",
            "category": "personal",
            "calculation": "Full amount"
        },
        {
            "id": "ded_super_contributions",
            "name": "Personal super contributions (deductible)",
            "category": "personal",
            "calculation": {"cap_concessional": 30000}
        }
    ]


@pytest.fixture
def temp_rules_file(sample_rules):
    """Create temporary rules file for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        rules_data = {
            "tax_year": "2024-25",
            "deductions_2024_25": sample_rules
        }
        
        rules_file = Path(temp_dir) / "tax_rules_2024.json"
        rules_file.write_text(json.dumps(rules_data))
        
        yield temp_dir


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_round_currency(self):
        """Test currency rounding function."""
        assert round_currency(123.456) == 123.46
        assert round_currency(123.454) == 123.45
        assert round_currency(123.455) == 123.46  # Banker's rounding
        assert round_currency(Decimal("123.456")) == 123.46
        assert round_currency(0) == 0.0
    
    def test_find_deduction_rule(self, sample_rules):
        """Test finding deduction rules."""
        rule = find_deduction_rule(sample_rules, "ded_wfh_fixed_rate")
        assert rule is not None
        assert rule["id"] == "ded_wfh_fixed_rate"
        
        rule = find_deduction_rule(sample_rules, "nonexistent")
        assert rule is None


class TestLoadDeductionsRules:
    """Test rules loading functionality."""
    
    def test_load_deductions_rules_success(self, temp_rules_file):
        """Test successful loading of deduction rules."""
        rules = load_deductions_rules(2024, temp_rules_file)
        assert len(rules) == 9
        assert rules[0]["id"] == "ded_wfh_fixed_rate"
    
    def test_load_deductions_rules_missing_file(self):
        """Test error when rules file is missing."""
        with pytest.raises(FileNotFoundError, match="Tax rules file not found"):
            load_deductions_rules(2024, "/nonexistent/path")
    
    def test_load_deductions_rules_missing_key(self, temp_rules_file):
        """Test error when deductions key is missing."""
        # Create rules file without deductions_2024_25 key
        rules_data = {"tax_year": "2024-25"}
        rules_file = Path(temp_rules_file) / "tax_rules_2025.json"
        rules_file.write_text(json.dumps(rules_data))
        
        with pytest.raises(KeyError, match="missing required key: 'deductions_2025_25'"):
            load_deductions_rules(2025, temp_rules_file)


class TestWFHDeduction:
    """Test working from home deduction calculations."""
    
    def test_wfh_valid_calculation(self, sample_rules):
        """Test valid WFH calculation."""
        result = calculate_wfh_deduction(400, True, sample_rules)
        assert result.id == "ded_wfh_fixed_rate"
        assert result.claimed == 280.0  # 400 * 0.70
        assert result.allowed == 280.0
        assert "400 hours" in result.note
    
    def test_wfh_no_hours(self, sample_rules):
        """Test WFH with no hours."""
        result = calculate_wfh_deduction(0, True, sample_rules)
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert result.note == "No hours claimed"
    
    def test_wfh_fixed_rate_not_selected(self, sample_rules):
        """Test WFH when fixed rate not selected."""
        result = calculate_wfh_deduction(400, False, sample_rules)
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert result.reason == "Fixed rate method not selected"
    
    def test_wfh_missing_rule(self):
        """Test WFH calculation with missing rule."""
        with pytest.raises(ValueError, match="WFH fixed rate rule not found"):
            calculate_wfh_deduction(400, True, [])


class TestCarDeductions:
    """Test car expense deduction calculations."""
    
    def test_car_cents_per_km_valid(self, sample_rules):
        """Test valid cents per km calculation."""
        cars = [CarExpense(id="car1", method="cents_per_km", kms=3000)]
        results = calculate_car_deductions(cars, sample_rules)
        
        assert len(results) == 1
        result = results[0]
        assert result.claimed == 2640.0  # 3000 * 0.88
        assert result.allowed == 2640.0
        assert "cents per km method" in result.note
    
    def test_car_cents_per_km_over_limit(self, sample_rules):
        """Test cents per km calculation over 5000km limit."""
        cars = [CarExpense(id="car1", method="cents_per_km", kms=6000)]
        results = calculate_car_deductions(cars, sample_rules)
        
        result = results[0]
        assert result.claimed == 5280.0  # 6000 * 0.88
        assert result.allowed == 4400.0  # 5000 * 0.88
        assert "Limited to 5000 km maximum" in result.reason
    
    def test_car_logbook_valid(self, sample_rules):
        """Test valid logbook calculation."""
        cars = [CarExpense(
            id="car1",
            method="logbook",
            work_use_pct=30.0,
            fuel=1000.0,
            servicing=500.0,
            insurance=800.0
        )]
        results = calculate_car_deductions(cars, sample_rules)
        
        result = results[0]
        total_costs = 2300.0  # 1000 + 500 + 800
        expected_allowed = total_costs * 0.30  # 690.0
        assert result.claimed == total_costs
        assert result.allowed == expected_allowed
        assert "logbook method" in result.note
    
    def test_car_no_kms(self, sample_rules):
        """Test car deduction with no kilometres."""
        cars = [CarExpense(id="car1", method="cents_per_km", kms=0)]
        results = calculate_car_deductions(cars, sample_rules)
        
        result = results[0]
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert result.note == "No kilometres claimed"


class TestPhoneInternetDeduction:
    """Test phone & internet deduction calculations."""
    
    def test_phone_internet_blocked_by_wfh(self, sample_rules):
        """Test phone internet blocked by WFH fixed rate."""
        result = calculate_phone_internet_deduction(30.0, False, 400, True, sample_rules)
        
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert "Excluded due to WFH fixed-rate" in result.reason
    
    def test_phone_internet_incidental_claims(self, sample_rules):
        """Test phone internet incidental claims."""
        result = calculate_phone_internet_deduction(None, True, 0, False, sample_rules)
        
        assert result.claimed == 50.0
        assert result.allowed == 50.0
        assert "Incidental use claim" in result.note
    
    def test_phone_internet_work_percentage(self, sample_rules):
        """Test phone internet with work percentage."""
        result = calculate_phone_internet_deduction(30.0, False, 0, False, sample_rules)
        
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert "30.0% work use specified" in result.note


class TestClothingLaundryDeduction:
    """Test clothing & laundry deduction calculations."""
    
    def test_clothing_laundry_valid(self, sample_rules):
        """Test valid clothing & laundry calculation."""
        result = calculate_clothing_laundry_deduction(20, 10, 100.0, sample_rules)
        
        expected = (20 * 1.0) + (10 * 0.5) + 100.0  # 20 + 5 + 100 = 125
        assert result.claimed == 125.0
        assert result.allowed == 125.0
        assert "20 work-only loads" in result.note
        assert "10 mixed loads" in result.note
        assert "Purchases: $100.00" in result.note
    
    def test_clothing_laundry_no_expenses(self, sample_rules):
        """Test clothing & laundry with no expenses."""
        result = calculate_clothing_laundry_deduction(0, 0, 0, sample_rules)
        
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert result.note == "No clothing or laundry expenses claimed"


class TestToolsDeductions:
    """Test tools & equipment deduction calculations."""
    
    def test_tools_under_threshold(self, sample_rules):
        """Test tools under $300 threshold."""
        tools = [ToolExpense(cost=250.0, work_use_pct=80.0)]
        results = calculate_tools_deductions(tools, sample_rules)
        
        result = results[0]
        expected = 250.0 * 0.8  # 200.0
        assert result.claimed == expected
        assert result.allowed == expected
        assert "immediate deduction ≤$300" in result.note
    
    def test_tools_over_threshold(self, sample_rules):
        """Test tools over $300 threshold."""
        tools = [ToolExpense(cost=500.0, work_use_pct=80.0)]
        results = calculate_tools_deductions(tools, sample_rules)
        
        result = results[0]
        expected_claimed = 500.0 * 0.8  # 400.0
        assert result.claimed == expected_claimed
        assert result.allowed == 0.0
        assert "requires depreciation calculation" in result.reason
    
    def test_tools_invalid_input(self, sample_rules):
        """Test tools with invalid input."""
        tools = [ToolExpense(cost=0, work_use_pct=80.0)]
        results = calculate_tools_deductions(tools, sample_rules)
        
        result = results[0]
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert "Invalid cost or work use percentage" in result.note


class TestUnionFeesDeduction:
    """Test union fees deduction calculations."""
    
    def test_union_fees_valid(self, sample_rules):
        """Test valid union fees calculation."""
        result = calculate_union_fees_deduction(120.0, sample_rules)
        
        assert result.claimed == 120.0
        assert result.allowed == 120.0
        assert result.note == "Full amount allowed"
    
    def test_union_fees_none(self, sample_rules):
        """Test union fees with no amount."""
        result = calculate_union_fees_deduction(0, sample_rules)
        
        assert result.claimed == 0.0
        assert result.allowed == 0.0
        assert result.note == "No union fees claimed"


class TestDonationsDeduction:
    """Test donations deduction calculations."""
    
    def test_donations_dgr_confirmed(self, sample_rules):
        """Test DGR donations when confirmed."""
        result = calculate_donations_deduction(200.0, 5.0, True, sample_rules)
        
        assert result.claimed == 205.0
        assert result.allowed == 205.0
        assert "DGR donations: $200.00" in result.note
        assert "Bucket donations: $5.00" in result.note
    
    def test_donations_dgr_not_confirmed(self, sample_rules):
        """Test DGR donations when not confirmed."""
        result = calculate_donations_deduction(200.0, 0, False, sample_rules)
        
        assert result.claimed == 200.0
        assert result.allowed == 0.0
        assert "DGR status not confirmed" in result.note
    
    def test_donations_bucket_over_limit(self, sample_rules):
        """Test bucket donations over limit."""
        result = calculate_donations_deduction(0, 15.0, False, sample_rules)
        
        assert result.claimed == 15.0
        assert result.allowed == 10.0  # Limited to $10
        assert "limited to $10.00" in result.note


class TestTaxAgentFeesDeduction:
    """Test tax agent fees deduction calculations."""
    
    def test_tax_agent_fees_valid(self, sample_rules):
        """Test valid tax agent fees calculation."""
        result = calculate_tax_agent_fees_deduction(180.0, sample_rules)
        
        assert result.claimed == 180.0
        assert result.allowed == 180.0
        assert result.note == "Full amount allowed"


class TestPersonalSuperDeduction:
    """Test personal super contributions deduction calculations."""
    
    def test_personal_super_under_cap(self, sample_rules):
        """Test personal super under concessional cap."""
        result, warnings = calculate_personal_super_deduction(25000.0, sample_rules)
        
        assert result.claimed == 25000.0
        assert result.allowed == 25000.0
        assert len(warnings) == 0
    
    def test_personal_super_over_cap(self, sample_rules):
        """Test personal super over concessional cap."""
        result, warnings = calculate_personal_super_deduction(35000.0, sample_rules)
        
        assert result.claimed == 35000.0
        assert result.allowed == 35000.0
        assert len(warnings) == 1
        assert "personal_super_may_exceed_concessional_cap" in warnings


class TestFullDeductionsCalculation:
    """Test full deductions calculation integration."""
    
    def test_empty_request(self, temp_rules_file):
        """Test calculation with empty request."""
        request = DeductionsRequest()
        # Mock the rules loading to use our temp rules
        import deductions_calculator
        original_load = deductions_calculator.load_deductions_rules
        deductions_calculator.load_deductions_rules = lambda year: load_deductions_rules(year, temp_rules_file)
        
        try:
            result = validate_and_calculate_deductions(request, 85000.0, "2024-25")
        finally:
            deductions_calculator.load_deductions_rules = original_load
        
        assert result.total_allowed == 0.0
        # Should have 7 individual deduction items (cars and tools are lists, so 0 when empty)
        assert len(result.line_items) == 7
        assert len(result.engine_flags.conflicts) == 0
        assert len(result.engine_flags.warnings) == 0
    
    def test_wfh_phone_conflict(self, temp_rules_file):
        """Test WFH and phone internet conflict."""
        request = DeductionsRequest(
            wfh_hours=400,
            wfh_use_fixed_rate=True,
            phone_internet_work_use_pct=30.0
        )
        # Mock the rules loading to use our temp rules
        import deductions_calculator
        original_load = deductions_calculator.load_deductions_rules
        deductions_calculator.load_deductions_rules = lambda year: load_deductions_rules(year, temp_rules_file)
        
        try:
            result = validate_and_calculate_deductions(request, 85000.0, "2024-25")
        finally:
            deductions_calculator.load_deductions_rules = original_load
        
        # Should have WFH allowed but phone blocked
        wfh_item = next(item for item in result.line_items if item.id == "ded_wfh_fixed_rate")
        phone_item = next(item for item in result.line_items if item.id == "ded_mobile_internet")
        
        assert wfh_item.allowed == 280.0  # 400 * 0.70
        assert phone_item.allowed == 0.0
        assert "phone_internet_blocked_by_wfh" in result.engine_flags.conflicts
    
    def test_comprehensive_deductions(self, temp_rules_file):
        """Test comprehensive deductions calculation."""
        request = DeductionsRequest(
            wfh_hours=200,
            wfh_use_fixed_rate=True,
            cars=[CarExpense(id="car1", method="cents_per_km", kms=3000)],
            clothing_work_only_loads=20,
            clothing_mixed_loads=10,
            tools=[ToolExpense(cost=250.0, work_use_pct=80.0)],
            donations_dgr_amount=200.0,
            donations_is_dgr_confirmed=True,
            union_fees=120.0,
            tax_agent_fees=180.0,
            personal_super_amount=25000.0
        )
        
        # Mock the rules loading to use our temp rules
        import deductions_calculator
        original_load = deductions_calculator.load_deductions_rules
        deductions_calculator.load_deductions_rules = lambda year: load_deductions_rules(year, temp_rules_file)
        
        try:
            result = validate_and_calculate_deductions(request, 85000.0, "2024-25")
        finally:
            deductions_calculator.load_deductions_rules = original_load
        
        # Calculate expected total
        expected_total = (
            140.0 +    # WFH: 200 * 0.70
            2640.0 +   # Car: 3000 * 0.88
            25.0 +     # Clothing: (20 * 1.0) + (10 * 0.5)
            200.0 +    # Tools: 250 * 0.8
            200.0 +    # Donations
            120.0 +    # Union fees
            180.0 +    # Tax agent fees
            25000.0    # Personal super
        )
        
        assert result.total_allowed == expected_total
        assert len(result.engine_flags.conflicts) == 0
        assert len(result.engine_flags.warnings) == 0
    
    def test_unsupported_year(self, temp_rules_file):
        """Test calculation with unsupported year."""
        request = DeductionsRequest()
        
        with pytest.raises(ValueError, match="Unsupported tax year: 2023-24"):
            validate_and_calculate_deductions(request, 85000.0, "2023-24")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])