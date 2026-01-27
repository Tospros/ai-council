from typing import Dict, Any, Optional, List
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio

from app.config import get_settings, INJECTION_SYSTEM_PROMPT


class LLMService:
    """Service for interacting with LLM models via LangChain."""

    def __init__(self):
        self.settings = get_settings()
        self._attacker_models: Dict[str, ChatOllama] = {}
        self._target_model: Optional[ChatOllama] = None
        self._initialize_models()

    def _initialize_models(self) -> None:
        """Initialize all configured LLM models."""
        # Initialize attacker models
        attacker_configs = [
            ("llama", self.settings.attacker_model_1),
            ("gemma", self.settings.attacker_model_2),
        ]

        for name, model_name in attacker_configs:
            self._attacker_models[name] = ChatOllama(
                model=model_name,
                base_url=self.settings.ollama_base_url,
                timeout=self.settings.llm_timeout,
            )

        # Initialize target model
        self._target_model = ChatOllama(
            model=self.settings.target_model_name,
            base_url=self.settings.ollama_base_url,
            timeout=self.settings.llm_timeout,
        )

    def get_attacker_model(self, model_key: str) -> Optional[ChatOllama]:
        """Get a specific attacker model by its key."""
        return self._attacker_models.get(model_key)

    def get_target_model(self) -> ChatOllama:
        """Get the target model."""
        return self._target_model

    @property
    def available_attacker_models(self) -> List[str]:
        """Get list of available attacker model keys."""
        return list(self._attacker_models.keys())

    @property
    def target_model_name(self) -> str:
        """Get the target model name."""
        return self.settings.target_model_name

    async def query_attacker_model(
        self,
        model_key: str,
        prompt: str,
    ) -> str:
        """
        Query a specific attacker model with the injection system prompt.

        Args:
            model_key: The key of the attacker model (llama, deepseek, gemma)
            prompt: The user's prompt

        Returns:
            The model's injection attempt as a string
        """
        model = self._attacker_models.get(model_key)
        if not model:
            raise ValueError(f"Attacker model '{model_key}' not found. Available: {self.available_attacker_models}")

        try:
            messages = [
                SystemMessage(content=INJECTION_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]

            response = await model.ainvoke(messages)
            return response.content
        except asyncio.TimeoutError:
            return f"Timeout after {self.settings.llm_timeout}s"
        except Exception as e:
            return f"Error: {str(e)}"

    async def query_target_model(
        self,
        prompt: str,
    ) -> str:
        """
        Query the target model with a prompt (no system prompt).

        Args:
            prompt: The prompt to send (typically an injection attempt)

        Returns:
            The target model's response as a string
        """
        try:
            messages = [HumanMessage(content=prompt)]
            response = await self._target_model.ainvoke(messages)
            return response.content
        except asyncio.TimeoutError:
            return f"Timeout after {self.settings.llm_timeout}s"
        except Exception as e:
            return f"Error: {str(e)}"

    async def query_all_attackers(
        self,
        prompt: str,
    ) -> Dict[str, str]:
        """
        Query all attacker models in parallel with the injection system prompt.

        Args:
            prompt: The user's prompt

        Returns:
            Dictionary mapping attacker model keys to their injection attempts
        """
        tasks = {
            model_key: self.query_attacker_model(model_key, prompt)
            for model_key in self._attacker_models.keys()
        }

        results = {}
        for model_key, task in tasks.items():
            try:
                results[model_key] = await task
            except Exception as e:
                results[model_key] = f"Error: {str(e)}"

        return results

    async def run_injection_workflow(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Run the complete injection workflow:
        1. Query all attacker models to generate injection attempts
        2. Send each injection attempt to the target model
        3. Return both injection attempts and target responses

        Args:
            prompt: The user's prompt

        Returns:
            Dictionary with injection_attempts and target_responses
        """
        # Step 1: Query all attackers in parallel
        attacker_tasks = [
            self.query_attacker_model(model_key, prompt)
            for model_key in self._attacker_models.keys()
        ]
        attacker_keys = list(self._attacker_models.keys())

        injection_attempts = {}
        attacker_results = await asyncio.gather(*attacker_tasks, return_exceptions=True)
        for key, result in zip(attacker_keys, attacker_results):
            if isinstance(result, Exception):
                injection_attempts[key] = f"Error: {str(result)}"
            else:
                injection_attempts[key] = result

        # Step 2: Query target model with each injection attempt in parallel
        target_tasks = [
            self.query_target_model(injection_attempts[key])
            for key in attacker_keys
        ]

        target_responses = {}
        target_results = await asyncio.gather(*target_tasks, return_exceptions=True)
        for key, result in zip(attacker_keys, target_results):
            if isinstance(result, Exception):
                target_responses[key] = f"Error: {str(result)}"
            else:
                target_responses[key] = result

        return {
            "injection_attempts": injection_attempts,
            "target_responses": target_responses,
        }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
