from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from schema import AgentInfo

from agents.Agent_AI.Agent_AI import Agent_AI


@dataclass
class Agent:
    description: str
    graph: CompiledStateGraph


agents: dict[str, Agent] = {
    "Agent-AI": Agent(
        description="An AI agent that can help users",
        graph=Agent_AI,
    ),
}


def get_agent(agent_id: str) -> CompiledStateGraph:
    return agents[agent_id].graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description) for agent_id, agent in agents.items()
    ]
