from langgraph.prebuilt.chat_agent_executor import AgentState
from typing import List, Dict


class CustomState(AgentState):
    user_info: str
    today_date: str
    conversation_history: List[Dict[str, str]]
