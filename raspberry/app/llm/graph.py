from typing import TypedDict, Annotated, Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import asyncio

from app.llm.service import LLMService, get_llm_service


class CouncilState(TypedDict):
    """State for the AI Council graph."""
    prompt: str
    system_prompt: Optional[str]
    responses: Dict[str, str]
    aggregated_response: Optional[str]
    errors: List[str]


class CouncilGraph:
    """
    LangGraph-based workflow for querying multiple LLM models in the AI Council.
    
    This graph orchestrates parallel queries to multiple LLM models and can
    optionally aggregate their responses.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Define the graph
        workflow = StateGraph(CouncilState)
        
        # Add nodes
        workflow.add_node("query_llama", self._query_llama)
        workflow.add_node("query_mistral", self._query_mistral)
        workflow.add_node("query_gemma", self._query_gemma)
        workflow.add_node("collect_responses", self._collect_responses)
        
        # Set entry point - we'll use a fan-out pattern
        workflow.set_entry_point("query_llama")
        
        # Add edges for parallel execution simulation
        # In practice, all models will be queried, then responses collected
        workflow.add_edge("query_llama", "query_mistral")
        workflow.add_edge("query_mistral", "query_gemma")
        workflow.add_edge("query_gemma", "collect_responses")
        workflow.add_edge("collect_responses", END)
        
        return workflow.compile()
    
    async def _query_llama(self, state: CouncilState) -> CouncilState:
        """Query the Llama model."""
        try:
            response = await self.llm_service.query_model(
                "llama", 
                state["prompt"],
                state.get("system_prompt")
            )
            state["responses"]["llama"] = response
        except Exception as e:
            state["responses"]["llama"] = f"Błąd: {str(e)}"
            state["errors"].append(f"llama: {str(e)}")
        return state
    
    async def _query_mistral(self, state: CouncilState) -> CouncilState:
        """Query the Mistral model."""
        try:
            response = await self.llm_service.query_model(
                "mistral",
                state["prompt"],
                state.get("system_prompt")
            )
            state["responses"]["mistral"] = response
        except Exception as e:
            state["responses"]["mistral"] = f"Błąd: {str(e)}"
            state["errors"].append(f"mistral: {str(e)}")
        return state
    
    async def _query_gemma(self, state: CouncilState) -> CouncilState:
        """Query the Gemma model."""
        try:
            response = await self.llm_service.query_model(
                "gemma",
                state["prompt"],
                state.get("system_prompt")
            )
            state["responses"]["gemma"] = response
        except Exception as e:
            state["responses"]["gemma"] = f"Błąd: {str(e)}"
            state["errors"].append(f"gemma: {str(e)}")
        return state
    
    async def _collect_responses(self, state: CouncilState) -> CouncilState:
        """Collect and optionally process all responses."""
        # This node can be extended to aggregate or analyze responses
        return state
    
    async def run(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Run the council workflow to query all models.
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Dictionary mapping model names to their responses
        """
        initial_state: CouncilState = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "responses": {},
            "aggregated_response": None,
            "errors": []
        }
        
        # For better performance, we'll use the direct parallel approach
        # instead of the sequential graph for the main use case
        responses = await self.llm_service.query_all_models(prompt, system_prompt)
        return responses
    
    async def run_with_graph(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> CouncilState:
        """
        Run the full graph workflow (sequential but can be extended).
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            The final state with all responses
        """
        initial_state: CouncilState = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "responses": {},
            "aggregated_response": None,
            "errors": []
        }
        
        result = await self.graph.ainvoke(initial_state)
        return result


class ParallelCouncilGraph:
    """
    A more advanced LangGraph implementation using parallel execution.
    This version queries all models truly in parallel using asyncio.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build a graph with parallel model queries."""
        
        workflow = StateGraph(CouncilState)
        
        # Add nodes
        workflow.add_node("query_all_parallel", self._query_all_parallel)
        workflow.add_node("post_process", self._post_process)
        
        # Set entry point
        workflow.set_entry_point("query_all_parallel")
        
        # Add edges
        workflow.add_edge("query_all_parallel", "post_process")
        workflow.add_edge("post_process", END)
        
        return workflow.compile()
    
    async def _query_all_parallel(self, state: CouncilState) -> CouncilState:
        """Query all models in parallel."""
        responses = await self.llm_service.query_all_models(
            state["prompt"],
            state.get("system_prompt")
        )
        state["responses"] = responses
        return state
    
    async def _post_process(self, state: CouncilState) -> CouncilState:
        """Post-process the responses (can be extended for aggregation)."""
        # Example: Could aggregate responses, extract common themes, etc.
        return state
    
    async def run(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Run the parallel council workflow.
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Dictionary mapping model names to their responses
        """
        initial_state: CouncilState = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "responses": {},
            "aggregated_response": None,
            "errors": []
        }
        
        result = await self.graph.ainvoke(initial_state)
        return result["responses"]


# Factory function for creating council graphs
def create_council_graph(parallel: bool = True) -> CouncilGraph | ParallelCouncilGraph:
    """
    Create a council graph instance.
    
    Args:
        parallel: Whether to use parallel execution (recommended)
        
    Returns:
        A council graph instance
    """
    if parallel:
        return ParallelCouncilGraph()
    return CouncilGraph()
