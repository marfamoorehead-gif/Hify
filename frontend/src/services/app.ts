/*
 * @Author: 汪培良 rick_wang@yunquna.com
 * @Date: 2026-05-04 12:03:39
 * @LastEditors: 汪培良 rick_wang@yunquna.com
 * @LastEditTime: 2026-05-04 18:55:30
 * @FilePath: /Hify/frontend/src/services/app.ts
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import api from "./api";
import type { Result, PageResult } from "@/types/api";
import type { App, AppCreateRequest } from "@/types/app";

export async function getHealth(){
  const { data } = await api.get<Result<App>>(`/health`);
   return data.data;
}

export async function listApps(page = 1, pageSize = 20) {
  const { data } = await api.get<Result<PageResult<App>>>("/api/v1/apps", {
    params: { page, page_size: pageSize },
  });
  return data.data;
}

export async function getApp(id: string) {
  const { data } = await api.get<Result<App>>(`/api/v1/apps/${id}`);
  return data.data;
}

export async function createApp(body: AppCreateRequest) {
  const { data } = await api.post<Result<App>>("/api/v1/apps", body);
  return data.data;
}

export async function updateApp(id: string, body: Partial<AppCreateRequest>) {
  const { data } = await api.put<Result<App>>(`/api/v1/apps/${id}`, body);
  return data.data;
}

export async function deleteApp(id: string) {
  await api.delete(`/api/v1/apps/${id}`);
}
