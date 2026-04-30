# 前端路由设计

> 详细内容请参考 CLAUDE.md 第 1.7 节

## URL 路径规范

RESTful 风格，资源名用复数、小写、连字符分隔。

```
/                           → 首页（应用列表）
/apps                       → 应用列表（同首页）
/apps/new                   → 创建应用
/apps/:id                   → 应用详情（Chatbot / Agent 配置页）
/apps/:id/edit              → 编辑应用
/chat                       → 对话页面（带默认应用）
/chat/:appId                → 指定应用的对话页
/chat/:appId/:conversationId → 指定对话的历史页
/knowledge                  → 知识库列表
/knowledge/new              → 创建知识库
/knowledge/:id              → 知识库详情（文档管理）
/workflows                  → 工作流列表
/workflows/new              → 创建工作流
/workflows/:id              → 工作流编辑器
/workflows/:id/run          → 工作流执行历史
/settings                   → 系统设置（Provider、模型）
/settings/providers         → Provider 管理
/login                      → 登录页（V1 可选，V2 加权限）
*                           → 404 页面
```

## 路由配置示例

```typescript
// router/index.tsx
import { createBrowserRouter } from "react-router-dom";
import Layout from "@/components/Layout";
import AppList from "@/pages/apps/AppList";
import AppCreate from "@/pages/apps/AppCreate";
import AppDetail from "@/pages/apps/AppDetail";
import ChatPage from "@/pages/chat/ChatPage";
import KnowledgeList from "@/pages/knowledge/KnowledgeList";
import KnowledgeDetail from "@/pages/knowledge/KnowledgeDetail";
import WorkflowEditor from "@/pages/workflow/WorkflowEditor";
import Settings from "@/pages/settings/Settings";
import NotFound from "@/pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <AppList /> },                    // 首页 = 应用列表
      { path: "apps", element: <AppList /> },
      { path: "apps/new", element: <AppCreate /> },
      { path: "apps/:id", element: <AppDetail /> },
      { path: "apps/:id/edit", element: <AppCreate /> },
      { path: "chat", element: <ChatPage /> },
      { path: "chat/:appId", element: <ChatPage /> },
      { path: "chat/:appId/:conversationId", element: <ChatPage /> },
      { path: "knowledge", element: <KnowledgeList /> },
      { path: "knowledge/new", element: <KnowledgeDetail /> },  // 复用详情页
      { path: "knowledge/:id", element: <KnowledgeDetail /> },
      { path: "workflows", element: <WorkflowList /> },
      { path: "workflows/new", element: <WorkflowEditor /> },
      { path: "workflows/:id", element: <WorkflowEditor /> },
      { path: "settings", element: <Settings /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);
```

## 规则

- 嵌套路由：`Layout` 组件包含侧边栏导航，子路由渲染在内容区
- 复用页面：创建/编辑用同一个组件，通过路由参数区分（`/new` 无 ID，`/:id/edit` 有 ID）
- 对话页面：支持可选参数（`appId` 和 `conversationId`），组件内用 `useParams()` 获取
