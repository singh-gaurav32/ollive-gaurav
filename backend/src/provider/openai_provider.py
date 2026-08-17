"""OpenAIProvider: second concrete LLMProvider adapter, added to demonstrate
the provider-agnostic design actually works - zero changes to chat logic,
ingestion, the dashboard, or the frontend were needed to add this. No
chat-handling or logging code should reference the openai SDK directly
outside this module (mirrors GeminiProvider's boundary).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from openai import AsyncOpenAI

from .interface import LLMProvider, ProviderError, ProviderResponse
from .models import Message, Role, Token

_ROLE_MAP = {Role.USER: "user", Role.ASSISTANT: "assistant", Role.SYSTEM: "system"}

DEFAULT_MAX_OUTPUT_TOKENS = 2048


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self._max_output_tokens = max_output_tokens

    def _to_openai_messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": _ROLE_MAP[m.role], "content": m.content} for m in messages]

    async def send(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> ProviderResponse:
        # conversation_id/session_id are part of the shared interface contract
        # (see interface.py) but unused by this provider - OpenAI's API has no
        # concept of them.
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=self._to_openai_messages(messages),
                max_completion_tokens=self._max_output_tokens,
            )
        except Exception as exc:  # noqa: BLE001 - normalize any provider error
            raise ProviderError(str(exc), provider="openai", original=exc) from exc

        usage = response.usage
        return ProviderResponse(
            content=response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            raw={"finish_reason": response.choices[0].finish_reason},
        )

    async def stream(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> AsyncIterator[Token]:
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=self._to_openai_messages(messages),
                max_completion_tokens=self._max_output_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            async for chunk in stream:
                # Usage arrives on a final chunk with no choices (stream_options
                # opt-in behavior) - guard against IndexError on that chunk.
                content = chunk.choices[0].delta.content or "" if chunk.choices else ""
                usage = chunk.usage
                yield Token(
                    content=content,
                    input_tokens=usage.prompt_tokens if usage else None,
                    output_tokens=usage.completion_tokens if usage else None,
                )
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(str(exc), provider="openai", original=exc) from exc
