"""Adapter-shape tests for GeminiProvider against a mocked google-genai client.
No real API calls are made in unit tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from provider.interface import ProviderError
from provider.models import Message, Role


async def test_send_returns_content_and_token_usage():
    with patch("provider.gemini_provider.genai.Client") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.text = "hello back"
        mock_response.usage_metadata = MagicMock(prompt_token_count=4, candidates_token_count=3)
        mock_response.finish_reason = "STOP"

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from provider.gemini_provider import GeminiProvider

        gemini_provider = GeminiProvider(api_key="test-key")
        result = await gemini_provider.send(
            [Message(role=Role.USER, content="hi")],
            conversation_id=uuid4(),
            session_id=uuid4(),
        )

        assert result.content == "hello back"
        assert result.input_tokens == 4
        assert result.output_tokens == 3


async def test_send_wraps_provider_exceptions():
    with patch("provider.gemini_provider.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("api down"))
        mock_client_cls.return_value = mock_client

        from provider.gemini_provider import GeminiProvider

        gemini_provider = GeminiProvider(api_key="test-key")
        with pytest.raises(ProviderError):
            await gemini_provider.send(
                [Message(role=Role.USER, content="hi")],
                conversation_id=uuid4(),
                session_id=uuid4(),
            )
