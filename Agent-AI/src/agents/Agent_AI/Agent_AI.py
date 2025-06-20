from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from agents.Agent_AI.prompt.models import CustomState
from agents.Agent_AI.prompt.utils import custom_prompt_modifier
from tools import get_weather, Add, Sous, Multiple, Divide
from .model import model
from .pre_model_hook import pre_model_hook

checkpointer = InMemorySaver()

Agent_AI = create_react_agent(
    state_schema=CustomState,
    name="Agent_AI",
    prompt=custom_prompt_modifier,
    model=model,
    tools=[
        get_weather,
        Add,
        Sous,
        Multiple,
        Divide
    ],
    pre_model_hook=pre_model_hook,
    checkpointer=checkpointer, 
)
