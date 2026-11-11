from typing import Protocol, TypeVar, runtime_checkable

import openai
from pydantic import BaseModel

from .exception import SummaryUnavailableError
import logging

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, system: str, user: str, response_model: type[T]) -> T: ...


class OpenAIClient:
    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        self._client = openai.OpenAI(api_key=api_key, timeout=timeout, max_retries=2)
        self._model = model

    def complete(self, system: str, user: str, response_model: type[T]) -> T:
        try:
            response = self._client.responses.parse(
                model=self._model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                text_format=response_model,
            )
        except openai.OpenAIError as e:
            raise SummaryUnavailableError from e

        if response.output_parsed is None:
            raise SummaryUnavailableError
        return response.output_parsed
