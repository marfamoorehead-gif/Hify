/**
 * 全局类型声明参考
 *
 * 对应规范：docs/frontend/architecture.md — TypeScript 类型规范
 */

// 后端统一响应格式（对应 backend/hify/shared/schemas.py Result）
export interface Result<T> {
  code: number;
  message: string;
  data: T;
}

// 分页响应（对应 backend/hify/shared/schemas.py PageResult）
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 分页请求参数
export interface PageRequest {
  page?: number;
  page_size?: number;
}

// 应用类型枚举
export type AppType = "chatbot" | "agent" | "workflow";

// 应用实体
export interface App {
  id: string;
  name: string;
  description: string;
  type: AppType;
  model_provider_id: string;
  model_name: string;
  created_at: string;
  updated_at: string;
}

// 创建应用请求
export type AppCreateRequest = Pick<App, "name" | "description" | "type" | "model_provider_id" | "model_name">;

// 对话消息角色
export type MessageRole = "user" | "assistant" | "system";

// 对话消息
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

// 对话
export interface Conversation {
  id: string;
  app_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

// 工作流节点类型
export type NodeType = "llm" | "knowledge" | "http" | "code" | "condition" | "template" | "variable";

// 工作流实体
export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

// 模型提供商
export interface ModelProvider {
  id: string;
  name: string;
  provider_type: string;
  api_base: string;
  is_active: boolean;
  created_at: string;
}
