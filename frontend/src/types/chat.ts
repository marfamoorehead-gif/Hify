export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  app_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}
