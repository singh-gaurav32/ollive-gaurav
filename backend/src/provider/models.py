"""Provider-call-boundary models: Message, Token, Role.

LogEvent moved to events/log_event.py - it's a cross-unit contract (Unit 1
publishes it, Unit 3 consumes it), not something owned by this unit alone.
See aidlc-docs/inception/application-design/shared-contracts.md.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str


class Token(BaseModel):
    """A single streamed content fragment from a provider.

    input_tokens/output_tokens are populated only on the chunk(s) where the
    provider actually reports usage (typically the final chunk) - see
    InstrumentedProvider for how these are accumulated into a LogEvent (BR3).
    """

    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
