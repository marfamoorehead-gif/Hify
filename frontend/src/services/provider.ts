import api from "./api";
import type { Result, PageResult } from "@/types/api";

export interface ModelProvider {
  id: string;
  name: string;
  provider_type: string;
  api_base: string;
  is_active: boolean;
  created_at: string;
}

export async function listProviders(page = 1, pageSize = 20) {
  const { data } = await api.get<Result<PageResult<ModelProvider>>>("/api/v1/providers", {
    params: { page, page_size: pageSize },
  });
  return data.data;
}

export async function getProvider(id: string) {
  const { data } = await api.get<Result<ModelProvider>>(`/api/v1/providers/${id}`);
  return data.data;
}
