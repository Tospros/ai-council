from typing import TypedDict, Dict, List, Optional
from langgraph.graph import StateGraph, END
import asyncio

from app.llm.service import LLMService, get_llm_service


class InjectionState(TypedDict):
    """State for the injection testing graph."""
    user_prompt: str
    injection_attempts: Dict[str, str]
    target_responses: Dict[str, str]
    errors: List[str]


class InjectionGraph:
    """
    LangGraph-based workflow for prompt injection testing.

    This graph orchestrates:
    1. Parallel queries to attacker models to generate injection attempts
    2. Parallel queries to target model with each injection attempt
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(InjectionState)

        # Add nodes
        workflow.add_node("query_attackers", self._query_attackers)
        workflow.add_node("query_target", self._query_target)
        workflow.add_node("collect_results", self._collect_results)

        # Set entry point
        workflow.set_entry_point("query_attackers")

        # Add edges
        workflow.add_edge("query_attackers", "query_target")
        workflow.add_edge("query_target", "collect_results")
        workflow.add_edge("collect_results", END)

        return workflow.compile()

    async def _query_attackers(self, state: InjectionState) -> InjectionState:
        """Query all attacker models in parallel to generate injection attempts."""
        attacker_keys = self.llm_service.available_attacker_models
        tasks = [
            self.llm_service.query_attacker_model(key, state["user_prompt"])
            for key in attacker_keys
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for key, result in zip(attacker_keys, results):
            if isinstance(result, Exception):
                state["injection_attempts"][key] = f"Error: {str(result)}"
                state["errors"].append(f"attacker_{key}: {str(result)}")
            else:
                state["injection_attempts"][key] = result

        return state

    async def _query_target(self, state: InjectionState) -> InjectionState:
        """Query target model with each injection attempt in parallel."""
        attacker_keys = list(state["injection_attempts"].keys())
        tasks = [
            self.llm_service.query_target_model(state["injection_attempts"][key])
            for key in attacker_keys
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for key, result in zip(attacker_keys, results):
            if isinstance(result, Exception):
                state["target_responses"][key] = f"Error: {str(result)}"
                state["errors"].append(f"target_{key}: {str(result)}")
            else:
                state["target_responses"][key] = result

        return state

    async def _collect_results(self, state: InjectionState) -> InjectionState:
        """Collect and finalize results."""
        return state

    async def run(self, prompt: str) -> Dict[str, Dict[str, str]]:
        """
        Run the injection workflow.

        Args:
            prompt: The user's prompt

        Returns:
            Dictionary with injection_attempts and target_responses
        """
        initial_state: InjectionState = {
            "user_prompt": prompt,
            "injection_attempts": {},
            "target_responses": {},
            "errors": []
        }

        # Use direct service method for better performance
        result = await self.llm_service.run_injection_workflow(prompt)
        return result

    async def run_with_graph(self, prompt: str) -> InjectionState:
        """
        Run the full graph workflow (for debugging/visualization).

        Args:
            prompt: The user's prompt

        Returns:
            The final state with all responses
        """
        initial_state: InjectionState = {
            "user_prompt": prompt,
            "injection_attempts": {},
            "target_responses": {},
            "errors": []
        }

        result = await self.graph.ainvoke(initial_state)
        return result


def create_injection_graph(llm_service: Optional[LLMService] = None) -> InjectionGraph:
    """
    Create an injection graph instance.

    Args:
        llm_service: Optional LLM service instance

    Returns:
        An injection graph instance
    """
    return InjectionGraph(llm_service)
