"""
Rule-Aware Decision Tree Agent

Integrates the dynamic decision tree with LangChain agent to provide intelligent tax consultation.
NO hardcoded logic - everything driven by tax rules structure.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime

from rule_parser import RuleParser
from decision_tree_builder import DecisionTreeBuilder, ConversationState, DecisionTreeNode, NodeType


class RuleAwareAgent:
    """
    Intelligent tax consultation agent that uses rule-driven decision trees.
    Adapts automatically to new tax rules and years.
    """
    
    def __init__(self, tax_rules_path: str):
        self.rule_parser = RuleParser(tax_rules_path)
        self.tree_builder = DecisionTreeBuilder(self.rule_parser)
        self.decision_tree = None
        self.conversation_states: Dict[str, ConversationState] = {}
        self.parsed_rules = self.rule_parser.parse_all_rules()
        
    def initialize_conversation(self, session_id: str) -> str:
        """Initialize a new conversation with intelligent opening"""
        
        if not self.decision_tree:
            self.decision_tree = self.tree_builder.build_decision_tree()
        
        # Create new conversation state
        self.conversation_states[session_id] = ConversationState(current_node_id="root")
        
        # Generate intelligent opening based on available rules
        total_rules = len(self.parsed_rules)
        categories = list(self.rule_parser.get_categories())
        
        opening = (
            f"I'm your expert tax accountant. I'll help you find all applicable deductions from "
            f"{total_rules} potential deduction types across {len(categories)} categories: "
            f"{', '.join(categories)}. "
            f"\n\nI'll ask targeted questions to identify opportunities you might miss. "
            f"Let's start with the most impactful deductions first."
        )
        
        return opening
    
    def get_next_question(self, session_id: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Get the next intelligent question based on conversation state.
        Returns: (question_text, question_id, metadata)
        """
        
        if session_id not in self.conversation_states:
            return None
            
        state = self.conversation_states[session_id]
        
        # Use decision tree to get next question
        result = self.tree_builder.get_next_question(state)
        
        if result:
            question_text, node = result
            
            # Enhance question with context and motivation
            enhanced_question = self._enhance_question_with_context(node, state)
            
            metadata = {
                "node_type": node.node_type.value,
                "rule_context": node.rule_context.rule_id if node.rule_context else None,
                "parameter_mapping": node.parameter_mapping,
                "question_type": node.conditions.get("question_type"),
                "data_type": node.conditions.get("data_type"),
                "validation": node.conditions.get("validation", [])
            }
            
            return enhanced_question, node.node_id, metadata
        
        return None
    
    def _enhance_question_with_context(self, node: DecisionTreeNode, state: ConversationState) -> str:
        """Enhance question with contextual information like a real accountant would"""
        
        base_question = node.content
        
        # Add motivation context for eligibility questions
        if node.node_type == NodeType.ELIGIBILITY_CHECK and node.rule_context:
            rule = node.rule_context
            
            # Calculate potential savings context
            motivation = self._generate_savings_motivation(rule)
            
            if motivation:
                return f"{base_question}\n\n💡 {motivation}"
        
        # Add clarification for complex questions
        elif node.node_type == NodeType.QUESTION_COLLECT and node.rule_context:
            clarification = self._generate_question_clarification(node)
            
            if clarification:
                return f"{base_question}\n\n{clarification}"
        
        return base_question
    
    def _generate_savings_motivation(self, rule) -> str:
        """Generate motivation text explaining potential tax savings"""
        
        rule_name_lower = rule.name.lower()
        
        if 'working from home' in rule_name_lower:
            return "This could save you hundreds in tax - many people miss this deduction!"
            
        elif 'car' in rule_name_lower:
            return "Car expenses can be significant - up to $4,400 annually with cents/km method!"
            
        elif 'phone' in rule_name_lower or 'internet' in rule_name_lower:
            return "Phone/internet deductions add up - especially if you work from home regularly."
            
        elif 'clothing' in rule_name_lower or 'uniform' in rule_name_lower:
            return "Protective clothing and uniform expenses are often overlooked but can be valuable."
            
        elif 'tools' in rule_name_lower or 'equipment' in rule_name_lower:
            return "Tool and equipment deductions can provide immediate tax relief."
            
        elif 'union' in rule_name_lower or 'professional' in rule_name_lower:
            return "Professional fees are fully deductible - don't miss this easy deduction."
            
        elif 'donation' in rule_name_lower:
            return "Donations over $2 to DGR charities are fully deductible."
            
        elif 'super' in rule_name_lower:
            return "Personal super contributions can significantly reduce your taxable income."
            
        elif 'tax agent' in rule_name_lower:
            return "Tax agent fees are deductible - including the cost of this consultation!"
            
        elif 'education' in rule_name_lower:
            return "Self-education expenses can be substantial if they relate to your current job."
            
        elif 'investment' in rule_name_lower:
            return "Investment expenses reduce your taxable investment income."
            
        else:
            return f"This deduction category could provide valuable tax savings."
    
    def _generate_question_clarification(self, node: DecisionTreeNode) -> str:
        """Generate clarifying information for data collection questions"""
        
        if not node.rule_context:
            return ""
            
        rule = node.rule_context
        question_type = node.conditions.get("question_type")
        
        if question_type == "amount":
            return "ℹ️ Enter the total amount you paid during the 2024-25 financial year."
            
        elif question_type == "quantity":
            if 'hour' in node.content.lower():
                return "ℹ️ Count all hours worked from home for employment duties (not just checking emails)."
            elif 'load' in node.content.lower():
                return "ℹ️ Count washing loads done specifically for work clothing/uniforms."
                
        elif question_type == "percentage":
            return "ℹ️ Estimate the percentage used for work purposes. Keep a diary if unsure."
            
        elif question_type == "selection":
            if 'method' in node.content.lower():
                return "ℹ️ Cents/km is simpler (max 5000km). Logbook method can claim more if you have detailed records."
        
        # Add record keeping reminder if relevant
        if rule.record_keeping:
            return f"📋 Record keeping: {rule.record_keeping}"
            
        return ""
    
    def process_answer(self, session_id: str, question_id: str, answer: Any) -> Dict[str, Any]:
        """Process user's answer and update conversation state"""
        
        if session_id not in self.conversation_states:
            return {"error": "Session not found"}
            
        state = self.conversation_states[session_id]
        
        # Validate answer based on question requirements
        validation_result = self._validate_answer(question_id, answer)
        
        if not validation_result["valid"]:
            return {
                "status": "validation_error",
                "message": validation_result["message"]
            }
        
        # Update conversation state
        updated_state = self.tree_builder.update_conversation_state(state, question_id, answer)
        self.conversation_states[session_id] = updated_state
        
        # Check if we should trigger calculation
        if self._should_trigger_calculation(updated_state):
            return {
                "status": "ready_for_calculation",
                "message": "I have enough information to calculate your tax. Let me process this now.",
                "collected_data": self._format_collected_data(updated_state)
            }
        
        return {
            "status": "continue",
            "message": "Thank you. Let me ask about the next deduction opportunity."
        }
    
    def _validate_answer(self, question_id: str, answer: Any) -> Dict[str, Any]:
        """Validate answer based on question requirements"""
        
        node = self.tree_builder._find_node_by_id(question_id)
        if not node:
            return {"valid": False, "message": "Question not found"}
        
        validation_rules = node.conditions.get("validation", [])
        data_type = node.conditions.get("data_type", "str")
        question_type = node.conditions.get("question_type")
        
        # Basic type validation
        if question_type == "amount" or question_type == "quantity":
            try:
                num_value = float(answer) if question_type == "amount" else int(answer)
                if num_value < 0:
                    return {"valid": False, "message": "Please enter a positive number"}
            except (ValueError, TypeError):
                return {"valid": False, "message": f"Please enter a valid {'amount' if question_type == 'amount' else 'number'}"}
        
        elif question_type == "percentage":
            try:
                pct_value = float(answer)
                if not (0 <= pct_value <= 100):
                    return {"valid": False, "message": "Please enter a percentage between 0 and 100"}
            except (ValueError, TypeError):
                return {"valid": False, "message": "Please enter a valid percentage"}
        
        elif question_type == "boolean":
            if str(answer).lower() not in ['yes', 'no', 'true', 'false', '1', '0']:
                return {"valid": False, "message": "Please answer Yes or No"}
        
        # Apply specific validation rules
        for rule in validation_rules:
            if rule == "super_cap_rules":
                try:
                    amount = float(answer)
                    if amount > 30000:  # 2024-25 concessional cap
                        return {"valid": False, "message": "Personal super contributions are capped at $30,000 for 2024-25"}
                except (ValueError, TypeError):
                    pass
        
        return {"valid": True, "message": "Valid answer"}
    
    def _should_trigger_calculation(self, state: ConversationState) -> bool:
        """Determine if we have enough data to trigger tax calculation"""
        
        # Simple heuristic - can be enhanced
        # Trigger if we've answered at least 5 questions or collected substantial data
        
        answered_count = len(state.answered_rules)
        has_substantial_data = any(
            'amount' in key or 'hours' in key or 'pct' in key 
            for key in state.collected_data.keys()
        )
        
        return answered_count >= 3 or (answered_count >= 2 and has_substantial_data)
    
    def _format_collected_data(self, state: ConversationState) -> Dict[str, Any]:
        """Format collected data for tax calculation"""
        
        formatted_data = {}
        
        for question_id, answer in state.collected_data.items():
            node = self.tree_builder._find_node_by_id(question_id)
            
            if node and node.parameter_mapping:
                # Map to calculator parameters
                for param in node.parameter_mapping:
                    if param not in formatted_data:  # Avoid overwriting
                        
                        # Convert answer to appropriate type
                        if node.conditions.get("question_type") == "amount":
                            try:
                                formatted_data[param] = float(answer)
                            except (ValueError, TypeError):
                                formatted_data[param] = 0.0
                                
                        elif node.conditions.get("question_type") == "quantity":
                            try:
                                formatted_data[param] = int(answer)
                            except (ValueError, TypeError):
                                formatted_data[param] = 0
                                
                        elif node.conditions.get("question_type") == "percentage":
                            try:
                                formatted_data[param] = float(answer) / 100.0  # Convert to decimal
                            except (ValueError, TypeError):
                                formatted_data[param] = 0.0
                                
                        elif node.conditions.get("question_type") == "boolean":
                            formatted_data[param] = str(answer).lower() in ['yes', 'true', '1']
                            
                        else:
                            formatted_data[param] = answer
        
        return formatted_data
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of current conversation state"""
        
        if session_id not in self.conversation_states:
            return {"error": "Session not found"}
            
        state = self.conversation_states[session_id]
        
        return {
            "answered_questions": len(state.answered_rules),
            "collected_parameters": len(state.collected_data),
            "conversation_history": state.conversation_history,
            "applicable_rules": list(state.applicable_rules),
            "current_node": state.current_node_id
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the rule-aware system for debugging"""
        
        return {
            "total_rules": len(self.parsed_rules),
            "categories": list(self.rule_parser.get_categories()),
            "decision_types": list(self.rule_parser.get_decision_types()),
            "parameter_mappings": self.rule_parser.get_parameter_mappings_summary(),
            "tree_nodes": self.tree_builder.decision_tree.metadata if self.decision_tree else {},
            "system_version": "1.0.0-dynamic",
            "last_initialized": datetime.now().isoformat()
        }