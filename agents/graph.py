"""
LangGraph workflow for orchestrating jailbreak testing.
"""
from typing import TypedDict, Annotated, List
from dataclasses import dataclass
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .llm_clients import get_all_attackers, get_target, AttackerAgent, TargetAgent
from .config import ATTACKER_MODELS, TARGET_MODEL


@dataclass
class JailbreakResult:
    """Result of a single jailbreak attempt."""
    attacker_model: str
    jailbreak_prompt: str
    target_response: str


class JailbreakState(TypedDict):
    """State for the jailbreak workflow."""
    original_prompt: str
    jailbreak_prompts: dict[str, str]  # model_name -> jailbreak_prompt
    target_responses: dict[str, str]   # model_name -> response
    results: List[JailbreakResult]
    error: str | None


async def generate_jailbreaks_node(state: JailbreakState) -> JailbreakState:
    """Node: Generate jailbreak prompts from all attacker models in parallel."""
    original_prompt = state["original_prompt"]
    attackers = get_all_attackers()

    async def generate_single(attacker: AttackerAgent) -> tuple[str, str]:
        prompt = await attacker.generate_jailbreak(original_prompt)
        return attacker.name, prompt

    # Run all attackers in parallel
    tasks = [generate_single(attacker) for attacker in attackers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jailbreak_prompts = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        model_name, prompt = result
        jailbreak_prompts[model_name] = prompt

    return {
        **state,
        "jailbreak_prompts": jailbreak_prompts
    }


async def test_target_node(state: JailbreakState) -> JailbreakState:
    """Node: Test all jailbreak prompts against the target model."""
    target = get_target()
    jailbreak_prompts = state["jailbreak_prompts"]

    async def test_single(model_name: str, prompt: str) -> tuple[str, str]:
        response = await target.respond(prompt)
        return model_name, response

    # Test all jailbreak prompts in parallel
    tasks = [
        test_single(model_name, prompt)
        for model_name, prompt in jailbreak_prompts.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    target_responses = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        model_name, response = result
        target_responses[model_name] = response

    return {
        **state,
        "target_responses": target_responses
    }


def compile_results_node(state: JailbreakState) -> JailbreakState:
    """Node: Compile final results."""
    jailbreak_prompts = state["jailbreak_prompts"]
    target_responses = state["target_responses"]

    results = []
    for model_name in jailbreak_prompts:
        results.append(JailbreakResult(
            attacker_model=model_name,
            jailbreak_prompt=jailbreak_prompts.get(model_name, ""),
            target_response=target_responses.get(model_name, "")
        ))

    return {
        **state,
        "results": results
    }


def create_jailbreak_graph() -> StateGraph:
    """Create the LangGraph workflow for jailbreak testing."""

    # Define the graph
    workflow = StateGraph(JailbreakState)

    # Add nodes
    workflow.add_node("generate_jailbreaks", generate_jailbreaks_node)
    workflow.add_node("test_target", test_target_node)
    workflow.add_node("compile_results", compile_results_node)

    # Define edges
    workflow.set_entry_point("generate_jailbreaks")
    workflow.add_edge("generate_jailbreaks", "test_target")
    workflow.add_edge("test_target", "compile_results")
    workflow.add_edge("compile_results", END)

    return workflow.compile()


class JailbreakOrchestrator:
    """Main orchestrator for running jailbreak tests."""

    def __init__(self):
        self.graph = create_jailbreak_graph()

    async def run(self, original_prompt: str) -> List[JailbreakResult]:
        """Run a full jailbreak test with all attacker models."""
        initial_state: JailbreakState = {
            "original_prompt": original_prompt,
            "jailbreak_prompts": {},
            "target_responses": {},
            "results": [],
            "error": None
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        return final_state.get("results", [])


# Singleton instance
_orchestrator = None


def get_orchestrator() -> JailbreakOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = JailbreakOrchestrator()
    return _orchestrator
