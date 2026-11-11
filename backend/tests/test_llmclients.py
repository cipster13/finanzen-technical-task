from types import SimpleNamespace

import httpx2
import openai
import pytest
from pydantic import BaseModel

import app.llmclients as llmclients
from app.exception import ServiceUnavailableError, SummaryUnavailableError
from app.llmclients import LLMClient, OpenAIClient


class Answer(BaseModel):
    text: str


REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/responses")


def status_error(cls: type[openai.APIStatusError], code: int) -> openai.APIStatusError:
    return cls("error", response=httpx2.Response(code, request=REQUEST), body=None)


class FakeResponses:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return SimpleNamespace(output_parsed=self._result)


@pytest.fixture
def fake_openai(monkeypatch):
    state = {"init": None, "responses": None}

    def setup(result=None, error=None):
        responses = FakeResponses(result=result, error=error)
        state["responses"] = responses

        class FakeOpenAI:
            def __init__(self, **kwargs):
                state["init"] = kwargs
                self.responses = responses

        monkeypatch.setattr(llmclients.openai, "OpenAI", FakeOpenAI)
        return state

    return setup


def create_client() -> OpenAIClient:
    return OpenAIClient(api_key="test-key", model="test-model", timeout=12.0)


class TestOpenAIClientSuccess:
    def test_satisfies_the_protocol(self, fake_openai):
        fake_openai()

        assert isinstance(create_client(), LLMClient)

    def test_creates_sdk_client_with_key_timeout_and_retries(self, fake_openai):
        state = fake_openai()

        create_client()

        assert state["init"] == {"api_key": "test-key", "timeout": 12.0, "max_retries": 2}

    def test_returns_the_parsed_object(self, fake_openai):
        fake_openai(result=Answer(text="hello"))

        result = create_client().complete("system", "user", Answer)

        assert result == Answer(text="hello")

    def test_sends_model_messages_and_response_format(self, fake_openai):
        state = fake_openai(result=Answer(text="hello"))

        create_client().complete("be brief", "summarize this", Answer)

        [call] = state["responses"].calls
        assert call["model"] == "test-model"
        assert call["input"] == [
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "summarize this"},
        ]
        assert call["text_format"] is Answer


class TestOpenAIClientErrors:
    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(openai.APIConnectionError(request=REQUEST), id="connection"),
            pytest.param(openai.APITimeoutError(request=REQUEST), id="timeout"),
            pytest.param(status_error(openai.AuthenticationError, 401), id="bad-key"),
            pytest.param(status_error(openai.RateLimitError, 429), id="rate-limit"),
            pytest.param(status_error(openai.InternalServerError, 500), id="server"),
        ],
    )
    def test_openai_errors_become_summary_unavailable(self, fake_openai, error):
        fake_openai(error=error)

        with pytest.raises(SummaryUnavailableError) as exc_info:
            create_client().complete("system", "user", Answer)

        assert exc_info.value.__cause__ is error

    def test_missing_parsed_output_raises_summary_unavailable(self, fake_openai):
        fake_openai(result=None)

        with pytest.raises(SummaryUnavailableError):
            create_client().complete("system", "user", Answer)

    def test_is_a_service_unavailable_error_with_status_503(self, fake_openai):
        fake_openai(error=openai.APIConnectionError(request=REQUEST))

        with pytest.raises(ServiceUnavailableError) as exc_info:
            create_client().complete("system", "user", Answer)

        assert exc_info.value.status_code == 503

    def test_non_openai_errors_are_not_hidden(self, fake_openai):
        fake_openai(error=ValueError("bug in our code"))

        with pytest.raises(ValueError, match="bug in our code"):
            create_client().complete("system", "user", Answer)
