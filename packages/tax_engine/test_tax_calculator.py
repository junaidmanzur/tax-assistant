"""
Unit tests for tax_calculator.py focusing on family MLS scenarios.
Tests the 2024-25 Australian tax year with Medicare Levy Surcharge family thresholds.
"""
import pytest
from pathlib import Path
from .tax_calculator import calculate_tax, get_mls_rate_family, get_mls_rate_single, calculate_mls_base

# Test data directory
TEST_RULES_DIR = Path(__file__).parent.parent / "tax_rules"


class TestSingleMLS:
    """Test MLS calculations for single taxpayers."""
    
    def test_single_no_cover_income_150000(self):
        """Single, no cover, income 150,000 -> rate 1.25% -> MLS = 1,875."""
        result = calculate_tax(
            income=150000,
            has_private_health=False,
            filing_status="single",
            rules_dir=str(TEST_RULES_DIR)
        )
        expected_mls = 150000 * 0.0125
        assert result["mls"] == round(expected_mls, 2)
        assert result["mls"] == 1875.0

    def test_single_with_cover_income_150000(self):
        """Single with private health cover -> MLS = 0 regardless of income."""
        result = calculate_tax(
            income=150000,
            has_private_health=True,
            filing_status="single",
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0

    def test_single_below_threshold(self):
        """Single, income below MLS threshold -> MLS = 0."""
        result = calculate_tax(
            income=90000,
            has_private_health=False,
            filing_status="single",
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0


class TestFamilyMLS:
    """Test MLS calculations for family taxpayers."""
    
    def test_family_0_dependents_combined_193500_no_cover(self):
        """Family, 0 dependents, combined 193,500, no cover -> below 194,000 -> MLS 0."""
        result = calculate_tax(
            income=80000,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=0,
            combined_family_income_for_mls=193500,
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0

    def test_family_2_dependents_combined_195000_no_cover(self):
        """
        Family, 2 dependents, combined 195,000, no cover:
        Effective base threshold = 194,000 + 1,500 (one child after first) = 195,500
        Combined < 195,500 => MLS 0.
        """
        result = calculate_tax(
            income=80000,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=2,
            combined_family_income_for_mls=195000,
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0

    def test_family_1_dependent_combined_220000_no_cover(self):
        """
        Family, 1 dependent, combined 220,000, no cover:
        Base threshold: 194,000
        No uplift (1 child, no additional uplift)
        Falls in tier 1 (194,001-226,000) at 1.0% rate
        Individual MLS calculated on individual income portion
        """
        individual_income = 100000
        result = calculate_tax(
            income=individual_income,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=1,
            combined_family_income_for_mls=220000,
            rules_dir=str(TEST_RULES_DIR)
        )
        # Rate should be 1.0% based on family income tier
        expected_mls = individual_income * 0.01
        assert result["mls"] == round(expected_mls, 2)
        assert result["mls"] == 1000.0

    def test_family_1_dependent_combined_310000_no_cover(self):
        """
        Family, 1 dependent, combined 310,000, no cover:
        Falls in highest tier (302,001+) at 1.5% rate
        """
        individual_income = 150000
        result = calculate_tax(
            income=individual_income,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=1,
            combined_family_income_for_mls=310000,
            rules_dir=str(TEST_RULES_DIR)
        )
        # Rate should be 1.5% based on family income tier
        expected_mls = individual_income * 0.015
        assert result["mls"] == round(expected_mls, 2)
        assert result["mls"] == 2250.0

    def test_family_3_dependents_combined_230000_no_cover(self):
        """
        Family, 3 dependents, combined 230,000, no cover:
        Base threshold: 194,000
        Child uplift: (3-1) * 1,500 = 3,000
        Effective threshold for tier 1: 194,000 + 3,000 = 197,000
        Tier boundaries become: 197,000 / 229,000 / 305,000
        Combined income 230,000 falls in tier 2 (229,001-305,000) at 1.25%
        """
        individual_income = 120000
        result = calculate_tax(
            income=individual_income,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=3,
            combined_family_income_for_mls=230000,
            rules_dir=str(TEST_RULES_DIR)
        )
        # Rate should be 1.25% based on adjusted family income tiers
        expected_mls = individual_income * 0.0125
        assert result["mls"] == round(expected_mls, 2)
        assert result["mls"] == 1500.0

    def test_family_with_coverage_high_income(self):
        """Family with coverage -> MLS 0 regardless of income."""
        result = calculate_tax(
            income=150000,
            has_private_health=True,
            filing_status="family",
            num_dependent_children=2,
            combined_family_income_for_mls=350000,
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0


class TestHelperFunctions:
    """Test individual helper functions for MLS rate calculations."""
    
    def test_get_mls_rate_single(self):
        """Test single MLS rate calculation."""
        from .tax_calculator import load_tax_rules
        rules = load_tax_rules(2024, TEST_RULES_DIR)
        
        # Test each tier
        assert get_mls_rate_single(90000, rules) == 0.0  # Below threshold
        assert get_mls_rate_single(100000, rules) == 0.01  # Tier 1
        assert get_mls_rate_single(120000, rules) == 0.0125  # Tier 2
        assert get_mls_rate_single(160000, rules) == 0.015  # Tier 3

    def test_get_mls_rate_family_no_children(self):
        """Test family MLS rate calculation with no children."""
        from .tax_calculator import load_tax_rules
        rules = load_tax_rules(2024, TEST_RULES_DIR)
        
        # Test each tier with no uplift
        assert get_mls_rate_family(190000, 0, rules) == 0.0  # Below threshold
        assert get_mls_rate_family(200000, 0, rules) == 0.01  # Tier 1
        assert get_mls_rate_family(250000, 0, rules) == 0.0125  # Tier 2
        assert get_mls_rate_family(310000, 0, rules) == 0.015  # Tier 3

    def test_get_mls_rate_family_with_children(self):
        """Test family MLS rate calculation with child uplift."""
        from .tax_calculator import load_tax_rules
        rules = load_tax_rules(2024, TEST_RULES_DIR)
        
        # With 2 children (1 child uplift = 1,500)
        # Thresholds become: 195,500 / 227,500 / 303,500
        assert get_mls_rate_family(195000, 2, rules) == 0.0  # Below adjusted threshold
        assert get_mls_rate_family(200000, 2, rules) == 0.01  # Adjusted tier 1
        assert get_mls_rate_family(250000, 2, rules) == 0.0125  # Adjusted tier 2
        assert get_mls_rate_family(310000, 2, rules) == 0.015  # Adjusted tier 3

    def test_calculate_mls_base(self):
        """Test MLS base calculation."""
        assert calculate_mls_base(100000, 0.01) == 1000.0
        assert calculate_mls_base(100000, 0.0125) == 1250.0
        assert calculate_mls_base(100000, 0.015) == 1500.0
        assert calculate_mls_base(100000, 0.0) == 0.0


class TestIntegrationScenarios:
    """Test complete tax calculation scenarios."""
    
    def test_complete_family_scenario(self):
        """Test complete tax calculation for a family scenario."""
        result = calculate_tax(
            income=80000,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=2,
            combined_family_income_for_mls=220000,
            rules_dir=str(TEST_RULES_DIR)
        )
        
        # Verify all components are present
        assert "base_tax" in result
        assert "medicare_levy" in result
        assert "mls" in result
        assert "total_tax" in result
        assert "take_home" in result
        
        # Verify MLS calculation (should be 1.0% rate based on family income)
        expected_mls = 80000 * 0.01
        assert result["mls"] == expected_mls
        
        # Verify total tax calculation
        expected_total = result["base_tax"] + result["medicare_levy"] + result["mls"]
        assert result["total_tax"] == expected_total
        
        # Verify take home calculation
        expected_take_home = 80000 - result["total_tax"]
        assert result["take_home"] == expected_take_home

    def test_edge_case_exactly_at_threshold(self):
        """Test calculations exactly at threshold boundaries."""
        # Family with exactly $194,000 combined income, no children
        result = calculate_tax(
            income=100000,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=0,
            combined_family_income_for_mls=194000,
            rules_dir=str(TEST_RULES_DIR)
        )
        assert result["mls"] == 0.0  # Exactly at threshold, no MLS
        
        # Family with exactly $194,001 combined income, no children
        result = calculate_tax(
            income=100000,
            has_private_health=False,
            filing_status="family",
            num_dependent_children=0,
            combined_family_income_for_mls=194001,
            rules_dir=str(TEST_RULES_DIR)
        )
        expected_mls = 100000 * 0.01  # First tier, 1.0%
        assert result["mls"] == expected_mls


if __name__ == "__main__":
    pytest.main([__file__])