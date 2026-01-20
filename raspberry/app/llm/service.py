from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio

from app.config import get_settings


class LLMService:
    """Service for interacting with LLM models via LangChain."""
    
    def __init__(self):
        self.settings = get_settings()
        self._models: Dict[str, ChatOllama] = {}
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize all configured LLM models."""
        model_configs = [
            ("llama", self.settings.model_name_1),
            ("mistral", self.settings.model_name_2),
            ("gemma", self.settings.model_name_3),
        ]
        
        for name, model_name in model_configs:
            self._models[name] = ChatOllama(
                model=model_name,
                base_url=self.settings.ollama_base_url,
                timeout=self.settings.llm_timeout,
            )
    
    def get_model(self, model_key: str) -> Optional[ChatOllama]:
        """Get a specific model by its key."""
        return self._models.get(model_key)
    
    @property
    def available_models(self) -> list[str]:
        """Get list of available model keys."""
        return list(self._models.keys())
    
    async def query_model(
        self, 
        model_key: str, 
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Query a specific model with a prompt.
        
        Args:
            model_key: The key of the model to query (llama, mistral, gemma)
            prompt: The user's prompt
            system_prompt: Optional system prompt to set context
            
        Returns:
            The model's response as a string
        """
        model = self._models.get(model_key)
        if not model:
            raise ValueError(f"Model '{model_key}' not found. Available: {self.available_models}")
        
        try:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            response = await model.ainvoke(messages)
            return response.content
        except asyncio.TimeoutError:
            return f"Timeout po {self.settings.llm_timeout}s"
        except Exception as e:
            return f"Błąd: {str(e)}"
    
    async def query_all_models(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Query all available models in parallel.
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt to set context
            
        Returns:
            Dictionary mapping model keys to their responses
        """
        tasks = [
            self.query_model(model_key, prompt, system_prompt)
            for model_key in self._models.keys()
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for model_key, response in zip(self._models.keys(), responses):
            if isinstance(response, Exception):
                result[model_key] = f"Błąd: {str(response)}"
            else:
                result[model_key] = response
        
        return result
    
    async def query_with_chain(
        self,
        model_key: str,
        prompt: str,
        template: Optional[str] = None
    ) -> str:
        """
        Query a model using a LangChain chain with optional template.
        
        Args:
            model_key: The key of the model to query
            prompt: The user's prompt (used as {input} in template)
            template: Optional prompt template with {input} placeholder
            
        Returns:
            The model's response as a string
        """
        model = self._models.get(model_key)
        if not model:
            raise ValueError(f"Model '{model_key}' not found. Available: {self.available_models}")
        
        try:
            if template:
                prompt_template = ChatPromptTemplate.from_template(template)
                chain = prompt_template | model | StrOutputParser()
                response = await chain.ainvoke({"input": prompt})
            else:
                chain = model | StrOutputParser()
                response = await chain.ainvoke(prompt)
            
            return response
        except asyncio.TimeoutError:
            return f"Timeout po {self.settings.llm_timeout}s"
        except Exception as e:
            return f"Błąd: {str(e)}"


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
