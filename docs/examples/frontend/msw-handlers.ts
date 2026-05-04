/**
 * MSW (Mock Service Worker) 请求处理参考
 *
 * 对应规范：docs/testing/frontend-testing.md
 *
 * 用法：
 *   import { handlers } from "@/test/msw-handlers";
 *   server.use(...handlers);
 */
import { http, HttpResponse } from "msw";

// ---- 通用响应构造 ----

function success<T>(data: T) {
  return HttpResponse.json({ code: 200, message: "ok", data });
}

function error(message: string, status = 400) {
  return HttpResponse.json({ code: status * 100, message }, { status });
}

// ---- 应用相关 Mock ----

export const appHandlers = [
  http.get("/api/v1/apps", ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") || 1);
    const pageSize = Number(url.searchParams.get("page_size") || 20);

    return success({
      items: [
        {
          id: "app-1",
          name: "测试助手",
          description: "用于测试的对话助手",
          type: "chatbot",
          model_provider_id: "provider-1",
          model_name: "glm-4",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
      page,
      page_size: pageSize,
    });
  }),

  http.post("/api/v1/apps", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;

    if (!body.name) {
      return error("应用名称不能为空", 400);
    }

    return success({
      id: "app-new",
      name: body.name,
      description: body.description || "",
      type: body.type,
      model_provider_id: body.model_provider_id,
      model_name: body.model_name || "glm-4",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }),

  http.get("/api/v1/apps/:id", ({ params }) => {
    if (params.id === "not-found") {
      return error("应用不存在", 404);
    }

    return success({
      id: params.id,
      name: "测试助手",
      description: "用于测试",
      type: "chatbot",
      model_provider_id: "provider-1",
      model_name: "glm-4",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
  }),
];

// ---- 知识库相关 Mock ----

export const knowledgeHandlers = [
  http.get("/api/v1/knowledge", () => {
    return success({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });
  }),
];

// ---- 模型提供商 Mock ----

export const providerHandlers = [
  http.get("/api/v1/providers", () => {
    return success({
      items: [
        {
          id: "provider-1",
          name: "智谱 GLM",
          provider_type: "openai_compatible",
          api_base: "https://open.bigmodel.cn/api/paas/v4",
          is_active: true,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });
  }),
];

// ---- 全部 handlers（供 msw-server.ts 使用） ----

export const handlers = [
  ...appHandlers,
  ...knowledgeHandlers,
  ...providerHandlers,
];
