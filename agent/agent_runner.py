import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from agent.tools.tax_tool import calculate_tax

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found.")

# Create the agent
memory = MemorySaver()
model = init_chat_model("gpt-4o-mini", model_provider="openai")
tools = [calculate_tax]
agent = create_react_agent(model, tools, checkpointer=memory)

# Use the agent
# config = {"configurable": {"thread_id": "abc123"}}

# system_message =  {
#     "role": "system", 
#     "content": "You are an Australian tax assistant. Always use the calculate_tax tool."
# }


# input_message = {
#     "role": "user",
#     "content": "I earn 120,000 + super before tax and have private health insurance. How much tax do I owe for the 2024 financial year?",
# }
# for step in agent.stream(
#     {"messages": [system_message, input_message]}, config, stream_mode="values"
# ):
#     step["messages"][-1].pretty_print()