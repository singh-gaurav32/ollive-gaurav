"""Chat endpoints - manual/curl-verifiable per Unit 2's scope (no frontend
until Unit 5). SSE streaming for the send-message endpoint.

session_id passed to ChatService is currently the user's own id - a
placeholder until Unit 5 introduces real auth sessions (db.models.Session);
see functional-design/domain-entities.md's note on session_id being a
foreign-key-shaped reference this unit doesn't yet have a real source for.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID

from chat.service import ChatService, ConversationNotFoundError
from db.models import User

from .deps import get_chat_service, get_current_user

router = APIRouter(prefix="/conversations", tags=["chat"])


class SendMessageRequest(BaseModel):
    content: str


@router.post("")
async def start_conversation(
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.start_conversation(user.id)


@router.get("")
async def list_conversations(
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.list_conversations(user.id)


@router.post("/{conversation_id}/resume")
async def resume_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return await chat_service.resume_conversation(conversation_id, user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/cancel")
async def cancel_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        await chat_service.cancel_conversation(conversation_id, user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "cancelling"}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    # Ownership checked here, synchronously, before any streaming starts -
    # send_message() is an async generator and won't run any of its body
    # (including its own ownership check) until first iterated, so a 404
    # can't be raised properly from inside the SSE generator below.
    try:
        await chat_service.get_conversation(conversation_id, user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_generator():
        async for token in chat_service.send_message(
            conversation_id, user.id, body.content, session_id=user.id
        ):
            yield f"event: token\ndata: {json.dumps({'content': token.content})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
