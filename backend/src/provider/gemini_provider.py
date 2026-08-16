"""GeminiProvider: concrete LLMProvider adapter for the Gemini API (v1, the only
provider implemented - see requirements.md Q4). No chat-handling or logging
code should reference the google-genai SDK directly outside this module.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from google import genai

from .interface import LLMProvider, ProviderError, ProviderResponse
from .models import Message, Role, Token

_ROLE_MAP = {Role.USER: "user", Role.ASSISTANT: "model", Role.SYSTEM: "user"}


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-flash-latest") -> None:
        self._client = genai.Client(api_key=api_key)
        self.model = model

    def _to_genai_contents(self, messages: list[Message]) -> list[dict]:
        # NOTE: Gemini's contents API has no first-class "system" role;
        # system messages are folded into a user turn here as a v1
        # simplification (a future refinement could use system_instruction).
        return [{"role": _ROLE_MAP[m.role], "parts": [{"text": m.content}]} for m in messages]

    async def send(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> ProviderResponse:
        # conversation_id/session_id are part of the shared interface contract
        # (see interface.py) but unused by this provider - Gemini's API has no
        # concept of them.
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=self._to_genai_contents(messages),
            )
        except Exception as exc:  # noqa: BLE001 - normalize any provider error
            raise ProviderError(str(exc), provider="gemini", original=exc) from exc

        usage = getattr(response, "usage_metadata", None)
        return ProviderResponse(
            content=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
            output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
            raw={"finish_reason": getattr(response, "finish_reason", None)},
        )

    async def stream(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> AsyncIterator[Token]:
        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=self.model,
                contents=self._to_genai_contents(messages),
            )
            async for chunk in stream:
                usage = getattr(chunk, "usage_metadata", None)
                yield Token(
                    content=chunk.text or "",
                    input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
                    output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
                )
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(str(exc), provider="gemini", original=exc) from exc
