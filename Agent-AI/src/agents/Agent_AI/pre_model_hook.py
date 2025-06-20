from langchain_core.messages import trim_messages, HumanMessage, AIMessage
from langchain_core.messages.utils import count_tokens_approximately
import logging

def extract_conversation_history(messages, max_history_entries=10):
    """Extrait l'historique de conversation des messages récents"""
    history = []
    
    # Prendre les derniers messages (excluant le message actuel)
    recent_messages = messages[-max_history_entries-1:-1] if len(messages) > 1 else []
    
    for msg in recent_messages:
        if isinstance(msg, HumanMessage):
            history.append({
                "role": "utilisateur",
                "content": msg.content
            })
        elif isinstance(msg, AIMessage):
            history.append({
                "role": "assistant",
                "content": msg.content
            })
    
    return history


def pre_model_hook(state):
    """
    Hook pré-modèle qui gère la mémoire et l'historique de conversation.
    Maintenant que nous avons un checkpointer, les messages sont automatiquement
    persistés entre les interactions avec le même thread_id.
    """
    
    conversation_history = extract_conversation_history(state.get("messages", []))
    
    logging.info(f"Nombre de messages dans l'historique: {len(state.get('messages', []))}")
    logging.info(f"Historique de conversation extrait: {len(conversation_history)} entrées")
    
    # Mettre à jour le state avec l'historique
    updated_state = {
        "conversation_history": conversation_history
    }

    return updated_state
