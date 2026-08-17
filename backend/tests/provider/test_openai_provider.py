"""Adapter-shape tests for OpenAIProvider against a mocked openai client.
No real API calls are made in unit tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from provider.interface import ProviderError
from provider.models import Message, Role


async def test_send_returns_content_and_token_usage():
    with patch("provider.openai_provider.AsyncOpenAI") as mock_client_cls:
        mock_message = MagicMock()
        mock_message.content = "hello back"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(prompt_tokens=4, completion_tokens=3)

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from provider.openai_provider import OpenAIProvider

        openai_provider = OpenAIProvider(api_key="test-key")
        result = await openai_provider.send(
            [Message(role=Role.USER, content="hi")],
            conversation_id=uuid4(),
            session_id=uuid4(),
        )

        assert result.content == "hello back"
        assert result.input_tokens == 4
        assert result.output_tokens == 3


async def test_send_wraps_provider_exceptions():
    with patch("provider.openai_provider.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("api down"))
        mock_client_cls.return_value = mock_client

        from provider.openai_provider import OpenAIProvider

        openai_provider = OpenAIProvider(api_key="test-key")
        with pytest.raises(ProviderError):
            await openai_provider.send(
                [Message(role=Role.USER, content="hi")],
                conversation_id=uuid4(),
                session_id=uuid4(),
            )
