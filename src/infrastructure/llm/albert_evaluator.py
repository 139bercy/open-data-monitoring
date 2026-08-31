"""Albert (DINUM / Etalab) implementation of LLM metadata evaluator."""

import os

from openai import OpenAI

from infrastructure.llm.openai_evaluator import OpenAIEvaluator

DEFAULT_ALBERT_BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
DEFAULT_ALBERT_MODEL = "AgentPublic/albert-light-rag-1.1"


class AlbertEvaluator(OpenAIEvaluator):
    """Albert API (DINUM / Etalab) metadata quality evaluator."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize Albert evaluator.

        Args:
            api_key: Albert API key (defaults to ALBERT_API_KEY env var)
            model_name: Albert model to use (defaults to ALBERT_MODEL_NAME or AgentPublic/albert-light-rag-1.1)
            base_url: Albert API base URL (defaults to ALBERT_API_BASE_URL or https://albert.api.etalab.gouv.fr/v1)
        """
        self.api_key = api_key or os.getenv("ALBERT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ALBERT_API_KEY must be set. Request your key from DINUM/Etalab (Albert API: https://albert.etalab.gouv.fr)"
            )

        self.base_url = (
            base_url or os.getenv("ALBERT_API_BASE_URL") or os.getenv("ALBERT_BASE_URL") or DEFAULT_ALBERT_BASE_URL
        )
        self.model_name = model_name or os.getenv("ALBERT_MODEL_NAME") or DEFAULT_ALBERT_MODEL

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
