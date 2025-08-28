"""
Dynamic Decision Tree Builder

Builds consultation decision trees automatically from parsed tax rules.
Creates intelligent flow based on eligibility criteria and question dependencies.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from rule_parser import RuleParser, DeductionRule, EligibilityNode, QuestionNode, QuestionType


class NodeType(Enum):
    ROOT = "root"
    CATEGORY_FILTER = "category_filter"
    ELIGIBILITY_CHECK = "eligibility_check"
    QUESTION_COLLECT = "question_collect"
    CALCULATION_TRIGGER = "calculation_trigger"
    RESULT = "result"


@dataclass
class DecisionTreeNode:
    """A node in the decision tree"""
    node_id: str
    node_type: NodeType
    content: str  # Question text or instruction
    conditions: Dict[str, Any] = field(default_factory=dict)
    children: List['DecisionTreeNode'] = field(default_factory=list)
    rule_context: Optional[DeductionRule] = None
    parameter_mapping: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Tracks current position and collected data in decision tree"""
    current_node_id: str
    collected_data: Dict[str, Any] = field(default_factory=dict)
    answered_rules: Set[str] = field(default_factory=set)
    applicable_rules: Set[str] = field(default_factory=set)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)


class DecisionTreeBuilder:
    """Builds dynamic decision trees from parsed tax rules"""
    
    def __init__(self, rule_parser: RuleParser):
        self.rule_parser = rule_parser
        self.rules = rule_parser.parse_all_rules()
        self.decision_tree = None
        
    def build_decision_tree(self) -> DecisionTreeNode:
        """Build the complete decision tree from rules"""
        
        # Create root node
        root = DecisionTreeNode(
            node_id="root",
            node_type=NodeType.ROOT,
            content="Let's explore your tax deduction opportunities. I'll ask targeted questions to maximize your tax savings.",
            metadata={"total_rules": len(self.rules)}
        )
        
        # Build category-based branches
        categories = self.rule_parser.get_categories()
        for category in sorted(categories):
            category_node = self._build_category_branch(category)
            root.children.append(category_node)
            
        # Add calculation trigger node
        calc_node = DecisionTreeNode(
            node_id="calculate_tax",
            node_type=NodeType.CALCULATION_TRIGGER,
            content="Based on your responses, I'll now calculate your tax deductions and total tax liability.",
            metadata={"triggers_calculation": True}
        )
        root.children.append(calc_node)
        
        self.decision_tree = root
        return root
    
    def _build_category_branch(self, category: str) -> DecisionTreeNode:
        """Build decision branch for a specific category"""
        
        category_rules = [rule for rule in self.rules if rule.category == category]
        
        # Create category filter node
        category_node = DecisionTreeNode(
            node_id=f"category_{category.replace('-', '_')}",
            node_type=NodeType.CATEGORY_FILTER,
            content=f"Let me check your {category} deduction opportunities.",
            metadata={"category": category, "rule_count": len(category_rules)}
        )
        
        # Build rule-specific branches within this category
        for rule in category_rules:
            rule_branch = self._build_rule_branch(rule)
            category_node.children.append(rule_branch)
            
        return category_node
    
    def _build_rule_branch(self, rule: DeductionRule) -> DecisionTreeNode:
        """Build decision branch for a specific tax rule"""
        
        # Create eligibility check nodes
        eligibility_chain = self._build_eligibility_chain(rule)
        
        # Create question collection nodes
        question_chain = self._build_question_chain(rule)
        
        # Connect eligibility to questions
        if eligibility_chain and question_chain:
            eligibility_chain[-1].children.append(question_chain[0])
        
        # Return the root of this rule's branch
        return eligibility_chain[0] if eligibility_chain else question_chain[0] if question_chain else None
    
    def _build_eligibility_chain(self, rule: DeductionRule) -> List[DecisionTreeNode]:
        """Build chain of eligibility check nodes for a rule"""
        
        chain = []
        
        for i, eligibility_node in enumerate(rule.eligibility_nodes):
            # Convert eligibility criteria to questions
            eligibility_question = self._convert_eligibility_to_question(eligibility_node, rule)
            
            node = DecisionTreeNode(
                node_id=f"{rule.rule_id}_eligibility_{i}",
                node_type=NodeType.ELIGIBILITY_CHECK,
                content=eligibility_question,
                rule_context=rule,
                conditions={"decision_type": eligibility_node.decision_type},
                metadata={
                    "original_criterion": eligibility_node.criterion,
                    "keywords": eligibility_node.keywords
                }
            )
            
            if chain:
                chain[-1].children.append(node)
            
            chain.append(node)
            
        return chain
    
    def _convert_eligibility_to_question(self, eligibility_node: EligibilityNode, rule: DeductionRule) -> str:
        """Convert eligibility criteria into a targeted question"""
        
        decision_type = eligibility_node.decision_type
        criterion = eligibility_node.criterion.lower()
        
        # Generate smart questions based on decision type
        if decision_type == 'employment_activity':
            if 'work from home' in criterion or 'home' in criterion:
                return "Do you work from home for your employment duties (not just checking emails occasionally)?"
            elif 'car' in criterion or 'travel' in criterion:
                return "Do you use your personal car for work-related travel (excluding regular commuting)?"
            else:
                return f"Do you engage in the work activity described: {eligibility_node.criterion}?"
                
        elif decision_type == 'expense_occurrence':
            if 'additional running' in criterion:
                return "Did you incur additional running expenses due to working from home?"
            elif 'paid' in criterion:
                return f"Did you pay for expenses related to: {rule.name}?"
            else:
                return f"Did you incur the following expense: {eligibility_node.criterion}?"
                
        elif decision_type == 'usage_based':
            return f"Did you use your own equipment/resources for work purposes as described: {eligibility_node.criterion}?"
            
        elif decision_type == 'record_keeping':
            return f"Do you have the required records as described: {eligibility_node.criterion}?"
            
        elif decision_type == 'membership_fees':
            return f"Are you a member of the organization described: {eligibility_node.criterion}?"
            
        elif decision_type == 'percentage_based':
            return f"Can you determine the work-related percentage as described: {eligibility_node.criterion}?"
            
        elif decision_type == 'threshold_based':
            return f"Do you meet the threshold requirement: {eligibility_node.criterion}?"
            
        elif decision_type == 'documentation_required':
            return f"Do you have the required documentation: {eligibility_node.criterion}?"
            
        else:
            # Generic fallback
            return f"Do you meet this requirement: {eligibility_node.criterion}?"
    
    def _build_question_chain(self, rule: DeductionRule) -> List[DecisionTreeNode]:
        """Build chain of data collection questions for a rule"""
        
        chain = []
        
        for i, question_node in enumerate(rule.question_nodes):
            node = DecisionTreeNode(
                node_id=f"{rule.rule_id}_question_{i}",
                node_type=NodeType.QUESTION_COLLECT,
                content=self._refine_question_text(question_node, rule),
                rule_context=rule,
                parameter_mapping=question_node.parameter_mapping,
                conditions={
                    "question_type": question_node.question_type.value,
                    "data_type": question_node.data_type,
                    "validation": [v.value for v in question_node.validation_rules]
                },
                metadata={
                    "original_prompt": question_node.question_text,
                    "parameter_mapping": question_node.parameter_mapping
                }
            )
            
            if chain:
                chain[-1].children.append(node)
                
            chain.append(node)
            
        return chain
    
    def _refine_question_text(self, question_node: QuestionNode, rule: DeductionRule) -> str:
        """Refine question text to be more specific and expert-like"""
        
        original = question_node.question_text
        question_type = question_node.question_type
        
        # Make questions more specific and professional
        if question_type == QuestionType.QUANTITY:
            if 'hours' in original.lower():
                return "How many hours did you work from home during the 2024-25 tax year?"
            elif 'loads' in original.lower():
                if 'work-only' in original.lower():
                    return "How many loads of work-only washing did you do?"
                else:
                    return "How many loads of mixed-use washing did you do?"
            else:
                return original
                
        elif question_type == QuestionType.AMOUNT:
            rule_name_lower = rule.name.lower()
            if 'union' in rule_name_lower:
                return "What was your total union or professional association membership fees for 2024-25?"
            elif 'tax agent' in rule_name_lower:
                return "How much did you pay in tax agent or accountant fees for managing your tax affairs?"
            elif 'donation' in rule_name_lower:
                return "What was your total amount donated to registered DGR charities?"
            elif 'super' in rule_name_lower:
                return "How much did you contribute personally to superannuation (after-tax contributions)?"
            else:
                return f"What amount did you spend on {rule.name.lower()}?"
                
        elif question_type == QuestionType.PERCENTAGE:
            return "What percentage of your phone/internet usage was for work purposes?"
            
        elif question_type == QuestionType.SELECTION:
            if 'method' in original.lower():
                return "Which car expense method do you want to use: cents per kilometre or logbook method?"
            else:
                return original
                
        else:
            return original
    
    def get_next_question(self, conversation_state: ConversationState) -> Optional[Tuple[str, DecisionTreeNode]]:
        """Get the next question based on current conversation state"""
        
        if not self.decision_tree:
            self.build_decision_tree()
            
        current_node = self._find_node_by_id(conversation_state.current_node_id)
        if not current_node:
            return None
            
        # Find next unanswered question
        next_node = self._find_next_applicable_question(current_node, conversation_state)
        
        if next_node:
            return next_node.content, next_node
        else:
            # No more questions - trigger calculation
            calc_node = self._find_node_by_id("calculate_tax")
            if calc_node:
                return calc_node.content, calc_node
                
        return None
    
    def _find_node_by_id(self, node_id: str) -> Optional[DecisionTreeNode]:
        """Find a node by its ID in the tree"""
        if not self.decision_tree:
            return None
            
        def search_tree(node: DecisionTreeNode) -> Optional[DecisionTreeNode]:
            if node.node_id == node_id:
                return node
            for child in node.children:
                result = search_tree(child)
                if result:
                    return result
            return None
            
        return search_tree(self.decision_tree)
    
    def _find_next_applicable_question(self, current_node: DecisionTreeNode, 
                                     conversation_state: ConversationState) -> Optional[DecisionTreeNode]:
        """Find the next applicable question based on conversation state"""
        
        # Simple traversal for now - can be enhanced with smarter logic
        def search_for_unanswered(node: DecisionTreeNode) -> Optional[DecisionTreeNode]:
            if (node.node_type == NodeType.ELIGIBILITY_CHECK or 
                node.node_type == NodeType.QUESTION_COLLECT):
                if node.node_id not in conversation_state.answered_rules:
                    return node
                    
            for child in node.children:
                result = search_for_unanswered(child)
                if result:
                    return result
                    
            return None
            
        return search_for_unanswered(self.decision_tree)
    
    def update_conversation_state(self, conversation_state: ConversationState, 
                                node_id: str, answer: Any) -> ConversationState:
        """Update conversation state with new answer"""
        
        conversation_state.answered_rules.add(node_id)
        conversation_state.collected_data[node_id] = answer
        conversation_state.current_node_id = node_id
        
        # Add to conversation history
        conversation_state.conversation_history.append({
            "node_id": node_id,
            "answer": str(answer)
        })
        
        return conversation_state
    
    def export_tree_structure(self) -> Dict[str, Any]:
        """Export tree structure for debugging/visualization"""
        if not self.decision_tree:
            self.build_decision_tree()
            
        def export_node(node: DecisionTreeNode) -> Dict[str, Any]:
            return {
                "node_id": node.node_id,
                "node_type": node.node_type.value,
                "content": node.content,
                "children_count": len(node.children),
                "children": [export_node(child) for child in node.children],
                "metadata": node.metadata
            }
            
        return export_node(self.decision_tree)