export const SSE_TIMEOUT = Number(import.meta.env.VITE_SSE_TIMEOUT) || 300000;

export const APP_TYPE_LABELS: Record<string, string> = {
  chatbot: "对话助手",
  agent: "智能代理",
  workflow: "工作流",
} as const;

export const DEFAULT_PAGE_SIZE = 20;
