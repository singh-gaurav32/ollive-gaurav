// Hand-mirrored from the backend's pydantic models (db/models.py,
// db/log_repository.py) - NFR Requirements Q2: manual, not generated.
// Kept in sync by hand; drift is an accepted risk at this project's scale.

export interface User {
  id: string;
  username: string;
  created_at: string;
}

export type ConversationState = "active" | "cancelled";

export interface Conversation {
  id: string;
  user_id: string;
  state: ConversationState;
  created_at: string;
  updated_at: string;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: ChatMessage[];
}

export interface MetricBucket {
  bucket_start: string;
  bucket_end: string;
  request_count: number;
  error_count: number;
  p50_latency_ms: number | null;
  p95_latency_ms: number | null;
}
