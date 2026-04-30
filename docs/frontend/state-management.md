# 前端状态管理（Zustand Store）

> 详细内容请参考 CLAUDE.md 第 1.7 节

## Store 划分原则

按业务域分 store，每个 store 管理一类状态。服务端状态用 TanStack Query（不进 Zustand）。

| Store | 管理状态 | 不管理状态 |
|---|---|---|
| `appStore.ts` | 当前选中的应用、应用列表（缓存）、创建/编辑表单 | 应用详情（用 `useQuery`） |
| `chatStore.ts` | 消息列表（本地 optimistic update）、当前对话 ID、发送状态 | 消息历史（用 `useInfiniteQuery`） |
| `workflowStore.ts` | 工作流编辑器状态（nodes、edges、选中节点）、草稿 | 工作流列表（用 `useQuery`） |

## appStore 示例

```typescript
// stores/appStore.ts
import { create } from "zustand";
import type { App } from "@/types/app";

interface AppState {
  // State
  currentApp: App | null;
  apps: App[];
  isCreating: boolean;

  // Actions
  setCurrentApp: (app: App | null) => void;
  setApps: (apps: App[]) => void;
  setIsCreating: (isCreating: boolean) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentApp: null,
  apps: [],
  isCreating: false,

  setCurrentApp: (app) => set({ currentApp: app }),
  setApps: (apps) => set({ apps }),
  setIsCreating: (isCreating) => set({ isCreating }),
  reset: () => set({ currentApp: null, apps: [], isCreating: false }),
}));
```

## chatStore 示例

```typescript
// stores/chatStore.ts
import { create } from "zustand";
import type { Message } from "@/types/chat";

interface ChatState {
  // State
  messages: Message[];
  conversationId: string | null;
  isSending: boolean;

  // Actions
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, content: string) => void;
  setConversationId: (id: string | null) => void;
  setIsSending: (isSending: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  conversationId: null,
  isSending: false,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  updateMessage: (messageId, content) => set((state) => ({
    messages: state.messages.map((msg) =>
      msg.id === messageId ? { ...msg, content } : msg
    ),
  })),
  setConversationId: (id) => set({ conversationId: id }),
  setIsSending: (isSending) => set({ isSending }),
  clearMessages: () => set({ messages: [], conversationId: null }),
}));
```

## workflowStore 示例

```typescript
// stores/workflowStore.ts
import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";

interface WorkflowState {
  // State
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  isDirty: boolean;  // 未保存标记

  // Actions
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  selectNode: (nodeId: string | null) => void;
  markDirty: () => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  isDirty: false,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  onNodesChange: (changes) => set((state) => ({
    nodes: applyNodeChanges(changes, state.nodes),
    isDirty: true,
  })),
  onEdgesChange: (changes) => set((state) => ({
    edges: applyEdgeChanges(changes, state.edges),
    isDirty: true,
  })),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
  markDirty: () => set({ isDirty: true }),
  reset: () => set({ nodes: [], edges: [], selectedNodeId: null, isDirty: false }),
}));
```

## 规则

- 服务端数据用 `useQuery` / `useInfiniteQuery`（自动缓存、重试、去重）
- 客户端临时状态用 Zustand（表单草稿、UI 交互状态）
- Store 不包含异步逻辑（用 `services/*.ts` + TanStack Query 的 `mutation`）

---

## state 更新规则

### 不可变更新

Zustand 的 `set` 必须返回新对象，禁止直接修改 state：

```typescript
// ✅ 正确：展开运算符返回新对象
set((state) => ({ messages: [...state.messages, newMsg] }))

// ✅ 正确：替换整个字段
set({ currentApp: newApp })

// ❌ 错误：直接 mutate
state.messages.push(newMsg)    // 不会触发重新渲染
state.messages[0].content = x  // 静默修改，破坏 React 渲染契约
```

### 数组更新速查

| 操作 | 写法 |
|---|---|
| 末尾添加 | `[...arr, item]` |
| 开头添加 | `[item, ...arr]` |
| 按条件删除 | `arr.filter(item => item.id !== targetId)` |
| 按条件修改 | `arr.map(item => item.id === targetId ? { ...item, field: value } : item)` |
| 按索引替换 | `arr.map((item, i) => i === idx ? newItem : item)` |

### 对象更新速查

| 操作 | 写法 |
|---|---|
| 修改单个字段 | `{ ...obj, field: newValue }` |
| 合并多个字段 | `{ ...obj, ...partialUpdate }` |
| 嵌套对象更新 | `{ ...obj, nested: { ...obj.nested, field: value } }` |
