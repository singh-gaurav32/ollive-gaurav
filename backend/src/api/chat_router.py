"""Chat endpoints. SSE streaming for the send-message endpoint.

session_id passed to ChatService is now the real auth session id (Unit 5),
retiring Unit 2's user.id-as-session_id placeholder (BR4).
"""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat.service import ChatService, ConversationNotFoundError

from .deps import AuthContext, get_auth_context, get_chat_service

router = APIRouter(prefix="/conversations", tags=["chat"])


class SendMessageRequest(BaseModel):
    content: str


@router.post("")
async def start_conversation(
    auth: AuthContext = Depends(get_auth_context),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.start_conversation(auth.user.id)


@router.get("")
async def list_conversations(
    auth: AuthContext = Depends(get_auth_context),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.list_conversations(auth.user.id)


@router.post("/{conversation_id}/resume")
async def resume_conversation(
    conversation_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return await chat_service.resume_conversation(conversation_id, auth.user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/cancel")
async def cancel_conversation(
    conversation_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        await chat_service.cancel_conversation(conversation_id, auth.user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "cancelling"}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    auth: AuthContext = Depends(get_auth_context),
    chat_service: ChatService = Depends(get_chat_service),
):
    # Ownership checked here, synchronously, before any streaming starts -
    # send_message() is an async generator and won't run any of its body
    # (including its own ownership check) until first iterated, so a 404
    # can't be raised properly from inside the SSE generator below.
    try:
        await chat_service.get_conversation(conversation_id, auth.user.id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_generator():
        async for token in chat_service.send_message(
            conversation_id, auth.user.id, body.content, session_id=auth.session_id
        ):
            yield f"event: token\ndata: {json.dumps({'content': token.content})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
