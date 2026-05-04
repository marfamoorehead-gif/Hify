import { create } from "zustand";
import type { Message } from "@/types/chat";

interface ChatState {
  messages: Message[];
  conversationId: string | null;
  isSending: boolean;

  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, delta: string) => void;
  setConversationId: (id: string | null) => void;
  setIsSending: (isSending: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  conversationId: null,
  isSending: false,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (messageId, delta) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, content: msg.content + delta } : msg
      ),
    })),

  setConversationId: (id) => set({ conversationId: id }),
  setIsSending: (isSending) => set({ isSending }),
  clearMessages: () => set({ messages: [], conversationId: null }),
}));
