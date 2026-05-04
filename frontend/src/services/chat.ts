import api from "./api";
import type { Result, PageResult } from "@/types/api";
import type { Conversation } from "@/types/chat";

export async function listConversations(appId: string, page = 1, pageSize = 20) {
  const { data } = await api.get<Result<PageResult<Conversation>>>(
    `/api/v1/apps/${appId}/conversations`,
    { params: { page, page_size: pageSize } }
  );
  return data.data;
}

export async function getConversation(appId: string, conversationId: string) {
  const { data } = await api.get<Result<Conversation>>(
    `/api/v1/apps/${appId}/conversations/${conversationId}`
  );
  return data.data;
}
