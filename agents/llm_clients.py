"""
LangChain LLM clients for Ollama models.
"""
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .config import get_attacker_models, get_target_model, JAILBREAK_SYSTEM_PROMPT


def create_attacker_llm(model_config: dict) -> Ollama:
    """Create an Ollama LLM instance for an attacker model."""
    return Ollama(
        model=model_config["name"],
        base_url=model_config["config"].base_url,
        temperature=0.8,
        num_ctx=2048,
    )


def create_target_llm() -> Ollama:
    """Create an Ollama LLM instance for the target model."""
    target = get_target_model()
    return Ollama(
        model=target["name"],
        base_url=target["config"].base_url,
        temperature=0.7,
        num_ctx=2048,
    )


def create_jailbreak_chain(llm: Ollama):
    """Create a chain for generating jailbreak prompts."""
    prompt_template = PromptTemplate(
        input_variables=["original_prompt"],
        template=f"""{JAILBREAK_SYSTEM_PROMPT}

Original prompt: {{original_prompt}}

Rephrased prompt:"""
    )
    return prompt_template | llm | StrOutputParser()


def create_target_chain(llm: Ollama):
    """Create a chain for the target model response."""
    prompt_template = PromptTemplate(
        input_variables=["prompt"],
        template="{prompt}"
    )
    return prompt_template | llm | StrOutputParser()


class AttackerAgent:
    """Agent wrapper for attacker LLM."""

    def __init__(self, model_config: dict):
        self.model_config = model_config
        self.name = model_config["name"]
        self.llm = create_attacker_llm(model_config)
        self.chain = create_jailbreak_chain(self.llm)

    async def generate_jailbreak(self, original_prompt: str) -> str:
        """Generate a jailbreak prompt."""
        try:
            result = await self.chain.ainvoke({"original_prompt": original_prompt})
            return result.strip()
        except Exception as e:
            return f"[Error generating jailbreak: {str(e)}]"


class TargetAgent:
    """Agent wrapper for target LLM."""

    def __init__(self):
        target = get_target_model()
        self.name = target["name"]
        self.llm = create_target_llm()
        self.chain = create_target_chain(self.llm)

    async def respond(self, prompt: str) -> str:
        """Get response from target model."""
        try:
            result = await self.chain.ainvoke({"prompt": prompt})
            return result.strip()
        except Exception as e:
            return f"[Error getting response: {str(e)}]"


def get_all_attackers() -> list[AttackerAgent]:
    """Get all attacker agents."""
    return [AttackerAgent(config) for config in get_attacker_models()]


def get_target() -> TargetAgent:
    """Get target agent."""
    return TargetAgent()
