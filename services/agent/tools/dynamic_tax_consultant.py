"""
Dynamic Tax Consultant Tool

LangChain tool that integrates the rule-aware decision tree system.
Provides intelligent tax consultation without any hardcoded logic.
"""

from langchain.tools import BaseTool
from typing import Dict, Any, Optional
import json
import sys
import os

# Add the decision tree module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../decision_tree'))

from rule_aware_agent import RuleAwareAgent


class DynamicTaxConsultantTool(BaseTool):
    """Tool for intelligent tax consultation using rule-driven decision trees"""
    
    name: str = "dynamic_tax_consultant"
    description: str = """
    Intelligent tax consultation tool that asks targeted questions like a real tax accountant.
    
    Use this tool to:
    - Start a new tax consultation session
    - Get the next expert question based on user's situation
    - Process user answers and validate responses
    - Determine when enough data is collected for calculation
    
    The tool automatically adapts to tax rules and asks relevant questions without any hardcoded logic.
    
    Input should be a JSON string with:
    - action: "start_session" | "get_question" | "process_answer" | "get_status"
    - session_id: unique identifier for this conversation
    - question_id: (for process_answer) the ID of the question being answered
    - answer: (for process_answer) the user's response
    """
    
    def __init__(self):
        super().__init__()
        # Initialize with current tax rules
        tax_rules_path = os.path.join(os.path.dirname(__file__), '../../../packages/tax_rules/tax_rules_2024.json')
        self.agent = RuleAwareAgent(tax_rules_path)
    
    def _run(self, tool_input: str) -> str:
        try:
            # Parse input
            input_data = json.loads(tool_input)
            action = input_data.get("action")
            session_id = input_data.get("session_id", "default")
            
            if action == "start_session":
                return self._start_session(session_id)
                
            elif action == "get_question":
                return self._get_next_question(session_id)
                
            elif action == "process_answer":
                question_id = input_data.get("question_id")
                answer = input_data.get("answer")
                return self._process_answer(session_id, question_id, answer)
                
            elif action == "get_status":
                return self._get_status(session_id)
                
            elif action == "get_system_info":
                return self._get_system_info()
                
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
                
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"})
        except Exception as e:
            return json.dumps({"error": f"Tool error: {str(e)}"})
    
    def _start_session(self, session_id: str) -> str:
        """Start a new consultation session"""
        try:
            opening_message = self.agent.initialize_conversation(session_id)
            
            return json.dumps({
                "status": "session_started",
                "session_id": session_id,
                "message": opening_message,
                "next_action": "get_question"
            })
            
        except Exception as e:
            return json.dumps({"error": f"Failed to start session: {str(e)}"})
    
    def _get_next_question(self, session_id: str) -> str:
        """Get the next intelligent question"""
        try:
            result = self.agent.get_next_question(session_id)
            
            if result:
                question_text, question_id, metadata = result
                
                return json.dumps({
                    "status": "question_ready",
                    "question": question_text,
                    "question_id": question_id,
                    "metadata": metadata,
                    "instructions": "Please ask this question to the user and wait for their response."
                })
            else:
                return json.dumps({
                    "status": "no_more_questions",
                    "message": "I have enough information to calculate your tax now."
                })
                
        except Exception as e:
            return json.dumps({"error": f"Failed to get question: {str(e)}"})
    
    def _process_answer(self, session_id: str, question_id: str, answer: Any) -> str:
        """Process user's answer"""
        try:
            result = self.agent.process_answer(session_id, question_id, answer)
            
            if result["status"] == "validation_error":
                return json.dumps({
                    "status": "validation_error",
                    "message": result["message"],
                    "instructions": "Please ask the user to provide a valid answer to the same question."
                })
                
            elif result["status"] == "ready_for_calculation":
                return json.dumps({
                    "status": "ready_for_calculation",
                    "message": result["message"],
                    "collected_data": result["collected_data"],
                    "instructions": "Use the calculate_tax tool with the collected_data to compute the tax."
                })
                
            else:  # continue
                return json.dumps({
                    "status": "continue",
                    "message": result["message"],
                    "instructions": "Get the next question using get_question action."
                })
                
        except Exception as e:
            return json.dumps({"error": f"Failed to process answer: {str(e)}"})
    
    def _get_status(self, session_id: str) -> str:
        """Get current conversation status"""
        try:
            summary = self.agent.get_conversation_summary(session_id)
            
            return json.dumps({
                "status": "status_retrieved",
                "summary": summary
            })
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get status: {str(e)}"})
    
    def _get_system_info(self) -> str:
        """Get system information for debugging"""
        try:
            info = self.agent.get_system_info()
            
            return json.dumps({
                "status": "system_info_retrieved",
                "system_info": info
            })
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get system info: {str(e)}"})
    
    async def _arun(self, tool_input: str) -> str:
        """Async version - delegate to sync implementation"""
        return self._run(tool_input)


# Example usage for testing
if __name__ == "__main__":
    tool = DynamicTaxConsultantTool()
    
    # Test starting a session
    start_result = tool._run(json.dumps({
        "action": "start_session",
        "session_id": "test123"
    }))
    
    print("=== START SESSION ===")
    print(start_result)
    
    # Test getting first question
    question_result = tool._run(json.dumps({
        "action": "get_question",
        "session_id": "test123"
    }))
    
    print("\n=== FIRST QUESTION ===")
    print(question_result)
    
    # Test system info
    info_result = tool._run(json.dumps({
        "action": "get_system_info"
    }))
    
    print("\n=== SYSTEM INFO ===")
    print(info_result)