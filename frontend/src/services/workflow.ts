import api from "./api";
import type { Result, PageResult } from "@/types/api";
import type { Workflow, WorkflowCreateRequest } from "@/types/workflow";

export async function listWorkflows(page = 1, pageSize = 20) {
  const { data } = await api.get<Result<PageResult<Workflow>>>("/api/v1/workflows", {
    params: { page, page_size: pageSize },
  });
  return data.data;
}

export async function getWorkflow(id: string) {
  const { data } = await api.get<Result<Workflow>>(`/api/v1/workflows/${id}`);
  return data.data;
}

export async function createWorkflow(body: WorkflowCreateRequest) {
  const { data } = await api.post<Result<Workflow>>("/api/v1/workflows", body);
  return data.data;
}

export async function updateWorkflow(id: string, body: Partial<WorkflowCreateRequest>) {
  const { data } = await api.put<Result<Workflow>>(`/api/v1/workflows/${id}`, body);
  return data.data;
}

export async function deleteWorkflow(id: string) {
  await api.delete(`/api/v1/workflows/${id}`);
}
