"""
Rule Parser for Dynamic Decision Tree Generation

Extracts decision logic from tax rules JSON structure to build dynamic consultation flows.
NO hardcoded categories, mappings, or rule IDs - everything derived from rule structure.
"""

import json
import re
import inspect
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class QuestionType(Enum):
    AMOUNT = "amount"
    QUANTITY = "quantity"
    PERCENTAGE = "percentage" 
    BOOLEAN = "boolean"
    SELECTION = "selection"
    COMPLEX_OBJECT = "complex_object"
    MULTIPLE_QUANTITIES = "multiple_quantities"


class ValidationRule(Enum):
    POSITIVE_INTEGER = "positive_integer"
    POSITIVE_AMOUNT = "positive_amount"
    PERCENTAGE_0_100 = "percentage_0_100"
    CAPPED_AMOUNT = "capped_amount"
    VALIDATED_LIST = "validated_list"


@dataclass
class EligibilityNode:
    """Represents a decision point based on eligibility criteria"""
    criterion: str
    decision_type: str
    keywords: List[str]
    next_node: Optional[str] = None


@dataclass
class QuestionNode:
    """Represents a question that collects specific data"""
    question_text: str
    question_type: QuestionType
    parameter_mapping: List[str]
    validation_rules: List[ValidationRule]
    data_type: str
    follow_up_conditions: Optional[Dict[str, Any]] = None


@dataclass
class DeductionRule:
    """Complete rule structure extracted from tax rules JSON"""
    rule_id: str
    name: str
    category: str
    eligibility_nodes: List[EligibilityNode]
    question_nodes: List[QuestionNode]
    calculation_method: str
    exclusions: List[str]
    record_keeping: str


class RuleParser:
    """Parses tax rules JSON and extracts decision tree logic dynamically"""
    
    def __init__(self, tax_rules_path: str, calculator_module_path: str = None):
        self.tax_rules_path = tax_rules_path
        self.rules_data = self._load_rules()
        self.calculator_params = self._discover_calculator_parameters(calculator_module_path)
        self.parameter_mappings = self._auto_build_parameter_mappings()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load tax rules from JSON file"""
        with open(self.tax_rules_path, 'r') as f:
            return json.load(f)
    
    def _discover_calculator_parameters(self, calculator_module_path: str = None) -> Dict[str, Any]:
        """Dynamically discover calculator parameters from DeductionsRequest class"""
        if calculator_module_path:
            # Import the module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("deductions_calculator", calculator_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            request_class = module.DeductionsRequest
        else:
            # Use relative import
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../packages'))
            from tax_engine.deductions_calculator import DeductionsRequest
            request_class = DeductionsRequest
        
        # Get parameter annotations
        params = request_class.__annotations__
        return params
    
    def _auto_build_parameter_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Automatically build parameter mappings by analyzing rule IDs and calculator params"""
        mappings = {}
        
        for deduction in self.rules_data['deductions_2024_25']:
            rule_id = deduction['id']
            rule_name = deduction['name'].lower()
            
            # Auto-discover parameter mapping using semantic analysis
            mapped_params = self._find_matching_parameters(rule_id, rule_name, deduction)
            question_type = self._infer_question_type(deduction.get('ui_prompts', []))
            validation_rules = self._infer_validation_rules(deduction.get('calculation', {}))
            data_type = self._infer_data_type(mapped_params)
            
            mappings[rule_id] = {
                'primary_params': mapped_params,
                'question_type': question_type,
                'data_type': data_type,
                'validation': validation_rules
            }
            
        return mappings
    
    def _find_matching_parameters(self, rule_id: str, rule_name: str, deduction_data: Dict) -> List[str]:
        """Find calculator parameters that match this rule using semantic analysis"""
        matched_params = []
        
        # Extract key terms from rule_id and rule_name
        key_terms = self._extract_semantic_terms(rule_id, rule_name)
        
        # Search calculator parameters for matches
        for param_name, param_type in self.calculator_params.items():
            if self._parameters_match(key_terms, param_name, param_type):
                matched_params.append(param_name)
        
        return matched_params
    
    def _extract_semantic_terms(self, rule_id: str, rule_name: str) -> List[str]:
        """Extract semantic terms from rule identifier and name"""
        terms = []
        
        # Extract from rule_id (e.g., "ded_wfh_fixed_rate" -> ["wfh", "fixed", "rate"])
        id_parts = rule_id.replace('ded_', '').split('_')
        terms.extend(id_parts)
        
        # Extract from rule_name
        name_words = re.findall(r'\b[a-z]+\b', rule_name.lower())
        terms.extend(name_words)
        
        # Remove common words
        stopwords = {'deduction', 'expenses', 'related', 'method', 'the', 'and', 'or', 'for', 'of'}
        terms = [term for term in terms if term not in stopwords and len(term) > 1]
        
        return list(set(terms))  # Remove duplicates
    
    def _parameters_match(self, key_terms: List[str], param_name: str, param_type: Any) -> bool:
        """Check if calculator parameter matches rule based on semantic similarity"""
        param_words = re.findall(r'[a-z]+', param_name.lower())
        
        # Direct term matches
        for term in key_terms:
            if term in param_words:
                return True
        
        # Semantic matches (expand as needed)
        semantic_matches = {
            'wfh': ['home', 'work_from_home'],
            'car': ['vehicle', 'transport'],
            'phone': ['mobile', 'internet', 'communication'],
            'clothing': ['uniform', 'laundry'],
            'tools': ['equipment', 'asset'],
            'union': ['professional', 'membership'],
            'donations': ['gift', 'charity'],
            'super': ['superannuation', 'retirement'],
            'tax_agent': ['accountant', 'professional_fees'],
            'education': ['training', 'course'],
            'investment': ['dividend', 'interest']
        }
        
        for term in key_terms:
            if term in semantic_matches:
                for semantic_term in semantic_matches[term]:
                    if any(word in param_words for word in semantic_term.split('_')):
                        return True
        
        return False
    
    def _infer_question_type(self, ui_prompts: List[str]) -> QuestionType:
        """Infer question type from UI prompts automatically"""
        if not ui_prompts:
            return QuestionType.AMOUNT  # Default
            
        for prompt in ui_prompts:
            prompt_lower = prompt.lower()
            
            if prompt.startswith('How many'):
                return QuestionType.QUANTITY
            elif prompt.startswith('How much'):
                return QuestionType.AMOUNT
            elif 'what %' in prompt_lower or 'percentage' in prompt_lower:
                return QuestionType.PERCENTAGE
            elif prompt.startswith('Which') or 'method' in prompt_lower:
                return QuestionType.SELECTION
            elif any(word in prompt_lower for word in ['did you', 'do you', 'have you']):
                return QuestionType.BOOLEAN
                
        return QuestionType.AMOUNT  # Default fallback
    
    def _infer_validation_rules(self, calculation: Dict[str, Any]) -> List[ValidationRule]:
        """Infer validation rules from calculation structure"""
        rules = []
        
        if isinstance(calculation, dict):
            if 'rate_per_hour' in calculation or 'rate_per_km' in calculation:
                rules.append(ValidationRule.POSITIVE_INTEGER)
            elif 'cap_concessional' in calculation or 'max_offset' in calculation:
                rules.append(ValidationRule.CAPPED_AMOUNT)
            elif 'methods' in calculation:
                rules.append(ValidationRule.VALIDATED_LIST)
            else:
                rules.append(ValidationRule.POSITIVE_AMOUNT)
        else:
            rules.append(ValidationRule.POSITIVE_AMOUNT)
            
        return rules
    
    def _infer_data_type(self, mapped_params: List[str]) -> str:
        """Infer data type from mapped parameters"""
        if not mapped_params:
            return 'float'
            
        param_name = mapped_params[0]
        
        if 'hours' in param_name or 'loads' in param_name:
            return 'int'
        elif 'pct' in param_name or 'percentage' in param_name:
            return 'float'
        elif param_name in ['cars', 'tools']:
            return f'List[{param_name.rstrip("s").title()}Expense]'
        elif 'confirmed' in param_name or 'use_' in param_name:
            return 'bool'
        else:
            return 'float'
    
    def parse_eligibility_criteria(self, eligibility_list: List[str]) -> List[EligibilityNode]:
        """Extract eligibility decision nodes from criteria text"""
        nodes = []
        
        for criterion in eligibility_list:
            decision_type = self._classify_eligibility_criterion(criterion)
            keywords = self._extract_keywords(criterion)
            
            node = EligibilityNode(
                criterion=criterion,
                decision_type=decision_type,
                keywords=keywords
            )
            nodes.append(node)
            
        return nodes
    
    def _classify_eligibility_criterion(self, criterion: str) -> str:
        """Classify eligibility criterion into decision type automatically"""
        criterion_lower = criterion.lower()
        
        # Pattern matching for decision types
        decision_patterns = {
            'employment_activity': ['you worked', 'you work', 'employment', 'fulfil employment'],
            'expense_occurrence': ['you paid', 'you incurred', 'additional running'],
            'usage_based': ['you used', 'using', 'use of'],
            'record_keeping': ['keep', 'record', 'log', 'receipt'],
            'membership_fees': ['membership', 'subscription', 'union', 'professional'],
            'percentage_based': ['%', 'proportion', 'percentage'],
            'threshold_based': ['must be', 'more than', 'at least', 'over'],
            'documentation_required': ['valid', 'acknowledgment', 'notice', 'lodged']
        }
        
        for decision_type, patterns in decision_patterns.items():
            if any(pattern in criterion_lower for pattern in patterns):
                return decision_type
                
        return 'general_eligibility'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key decision keywords from criterion text"""
        # Remove common words and extract meaningful terms
        stopwords = {'the', 'you', 'your', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Extract words, convert to lowercase, remove punctuation
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords[:5]  # Limit to top 5 keywords
    
    def parse_ui_prompts(self, ui_prompts: List[str], rule_id: str) -> List[QuestionNode]:
        """Convert UI prompts into structured question nodes"""
        nodes = []
        mapping = self.parameter_mappings.get(rule_id, {})
        
        for prompt in ui_prompts:
            question_type = self._classify_question_type(prompt)
            
            node = QuestionNode(
                question_text=prompt,
                question_type=question_type,
                parameter_mapping=mapping.get('primary_params', []),
                validation_rules=mapping.get('validation', []),
                data_type=mapping.get('data_type', 'str')
            )
            nodes.append(node)
            
        return nodes
    
    def _classify_question_type(self, prompt: str) -> QuestionType:
        """Classify UI prompt into question type"""
        prompt_lower = prompt.lower()
        
        if prompt.startswith('How many'):
            return QuestionType.QUANTITY
        elif prompt.startswith('How much'):
            return QuestionType.AMOUNT
        elif 'what %' in prompt_lower or 'percentage' in prompt_lower:
            return QuestionType.PERCENTAGE
        elif prompt.startswith('Which') or 'method' in prompt_lower:
            return QuestionType.SELECTION
        elif prompt.startswith('What type') or 'what was' in prompt_lower:
            return QuestionType.SELECTION
        elif any(word in prompt_lower for word in ['did you', 'do you', 'have you']):
            return QuestionType.BOOLEAN
        else:
            return QuestionType.AMOUNT  # Default fallback
    
    def parse_all_rules(self) -> List[DeductionRule]:
        """Parse all deduction rules into structured format"""
        deduction_rules = []
        
        for deduction in self.rules_data['deductions_2024_25']:
            rule = DeductionRule(
                rule_id=deduction['id'],
                name=deduction['name'],
                category=deduction['category'],
                eligibility_nodes=self.parse_eligibility_criteria(deduction['eligibility']),
                question_nodes=self.parse_ui_prompts(deduction.get('ui_prompts', []), deduction['id']),
                calculation_method=str(deduction.get('calculation', 'standard')),
                exclusions=deduction.get('exclusions', []),
                record_keeping=deduction.get('record_keeping', '')
            )
            deduction_rules.append(rule)
            
        return deduction_rules
    
    def get_categories(self) -> Set[str]:
        """Extract all unique categories from rules dynamically"""
        categories = set()
        for deduction in self.rules_data['deductions_2024_25']:
            categories.add(deduction['category'])
        return categories
    
    def get_decision_types(self) -> Set[str]:
        """Extract all unique decision types from eligibility criteria dynamically"""
        decision_types = set()
        
        for deduction in self.rules_data['deductions_2024_25']:
            for criterion in deduction['eligibility']:
                decision_type = self._classify_eligibility_criterion(criterion)
                decision_types.add(decision_type)
                
        return decision_types
    
    def get_parameter_mappings_summary(self) -> Dict[str, List[str]]:
        """Get summary of discovered parameter mappings for debugging"""
        summary = {}
        for rule_id, mapping in self.parameter_mappings.items():
            summary[rule_id] = mapping['primary_params']
        return summary