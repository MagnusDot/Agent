import os

from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate

from .models import CustomState


def load_prompt(file_path: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(current_dir, os.path.basename(file_path))
    try:
        with open(absolute_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found at: {absolute_path}")


def format_conversation_history(history: list) -> str:
    """Formate l'historique de conversation pour l'inclure dans le prompt"""
    if not history:
        return "Aucun historique de conversation disponible."
    
    formatted_history = []
    for entry in history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        formatted_history.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(formatted_history)


def custom_prompt_modifier(state: CustomState):
    template = Agent_prompt
    prompt_template = PromptTemplate(
        template=template,
        input_variables=[
            "user_info",
            "today_date",
            "conversation_history",
        ],
    )

    user_info = state.get("user_info", "Opérateur")
    today_date = state.get("today_date", "date non disponible")
    conversation_history = state.get("conversation_history", [])
    
    formatted_history = format_conversation_history(conversation_history)

    system_msg = SystemMessage(
        content=prompt_template.format(
            user_info=user_info,
            today_date=today_date,
            conversation_history=formatted_history,
        )
    )

    return [system_msg] + state["messages"]


Agent_prompt = load_prompt("prompt.md")
