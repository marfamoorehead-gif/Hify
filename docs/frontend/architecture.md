# 前端架构总览

> 详细内容请参考 CLAUDE.md 第 1.7 节

## 技术选型

| 库 | 用途 | 版本锁定 |
|---|---|---|
| React 18 | UI 框架 | package.json |
| TypeScript | 类型安全 | strict 模式 |
| React Flow | 工作流可视化编辑器 | @xyflow/react |
| Zustand | 状态管理（轻量，替代 Redux） | 按业务域拆分多个 store |
| TanStack Query | 服务端状态管理（请求、缓存、重试） | 替代手写 useEffect + useState |
| Ant Design | UI 组件库 | 企业级场景适配 |
| Vite | 构建工具 | 开发服务器 + 生产构建 |
| react-markdown | Markdown 渲染（AI 回复） | — |

---

## 目录结构

```
frontend/
├── public/                      # 静态资源
│   └── favicon.ico
├── src/
│   ├── main.tsx                 # React 入口
│   ├── App.tsx                  # 根组件 + 路由
│   ├── router/                  # 路由配置
│   │   └── index.tsx            # React Router 路由表
│   │
│   ├── pages/                   # 页面组件（按功能分目录）
│   │   ├── apps/                # 应用管理（创建/编辑/列表）
│   │   │   ├── AppList.tsx
│   │   │   ├── AppCreate.tsx
│   │   │   └── AppDetail.tsx
│   │   ├── chat/                # 对话页面
│   │   │   ├── ChatPage.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   └── MessageList.tsx
│   │   ├── knowledge/           # 知识库管理
│   │   │   ├── KnowledgeList.tsx
│   │   │   └── KnowledgeDetail.tsx
│   │   ├── workflow/            # 工作流编辑器
│   │   │   ├── WorkflowEditor.tsx
│   │   │   ├── nodes/           # 自定义 React Flow 节点
│   │   │   │   ├── LLMNode.tsx
│   │   │   │   ├── KnowledgeNode.tsx
│   │   │   │   └── ...
│   │   │   └── edges/           # 自定义连线
│   │   ├── settings/            # 系统设置（Provider、模型管理）
│   │   └── NotFound.tsx
│   │
│   ├── components/              # 通用组件（跨页面复用）
│   │   ├── Layout.tsx           # 全局布局（侧边栏 + 内容区）
│   │   ├── SSEProvider.tsx      # SSE 连接管理
│   │   ├── MarkdownRenderer.tsx # Markdown 渲染（AI 回复）
│   │   └── Pagination.tsx       # 分页组件
│   │
│   ├── hooks/                   # 自定义 Hooks
│   │   ├── useSSE.ts            # SSE 流式连接 hook
│   │   └── usePagination.ts     # 分页逻辑 hook
│   │
│   ├── services/                # API 调用层
│   │   ├── api.ts               # axios 实例（baseURL、拦截器、错误处理）
│   │   ├── app.ts               # 应用相关 API
│   │   ├── chat.ts              # 对话相关 API
│   │   ├── knowledge.ts         # 知识库相关 API
│   │   ├── workflow.ts          # 工作流相关 API
│   │   └── provider.ts          # 模型 Provider API
│   │
│   ├── stores/                  # Zustand 状态管理
│   │   ├── appStore.ts          # 应用状态
│   │   ├── chatStore.ts         # 对话状态（消息列表、当前对话）
│   │   └── workflowStore.ts     # 工作流编辑状态（节点、边）
│   │
│   ├── types/                   # TypeScript 类型定义（与后端 Schema 对齐）
│   │   ├── api.ts               # Result<T>、PageResult<T> 通用响应
│   │   ├── app.ts               # App 相关类型
│   │   ├── chat.ts              # Chat 相关类型
│   │   └── workflow.ts          # Workflow 相关类型
│   │
│   └── utils/                   # 工具函数
│       ├── format.ts            # 格式化（日期、金额、Token 用量）
│       └── constants.ts         # 前端常量
│
├── index.html
├── vite.config.ts
├── tsconfig.json
├── .env                         # 前端环境变量
├── .env.example
└── package.json
```

---

## 组件命名规范

| 类型 | 命名 | 示例 |
|---|---|---|
| 页面组件 | PascalCase，功能描述 | `ChatPage`、`WorkflowEditor` |
| 通用组件 | PascalCase，组件功能 | `MarkdownRenderer`、`Pagination` |
| 自定义 Hook | camelCase，use 前缀 | `useSSE`、`usePagination` |
| 类型文件 | camelCase，与后端模块对齐 | `app.ts`、`chat.ts` |
| API 服务 | camelCase，与后端模块对齐 | `services/app.ts` |

---

## React Flow 工作流编辑器

```typescript
// 自定义节点必须注册 nodeTypes
const nodeTypes = {
  llm: LLMNode,
  knowledge: KnowledgeNode,
  http: HTTPNode,
  code: CodeNode,
  condition: ConditionNode,
  template: TemplateNode,
  variable: VariableNode,
};

function WorkflowEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <ReactFlow nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}>
      <Background />
      <Controls />
    </ReactFlow>
  );
}
```

**规则**：
- 节点配置用 Zustand 管理，不通过 URL 参数
- 保存工作流时将 nodes/edges 序列化为 JSON 发送到后端
- 节点间数据通过 React Flow 的 `Handle` 组件传递

---

## 环境变量

```bash
# .env.example
VITE_API_BASE_URL=              # API 基础路径（空字符串表示同源，生产环境由 Nginx 反代）
VITE_SSE_TIMEOUT=300000         # SSE 连接超时（毫秒）
```

**规则**：
- 前端环境变量必须以 `VITE_` 前缀（Vite 要求）
- 不在前端代码中存放任何密钥（API Key、Token 等）
- 所有前端环境变量通过 `import.meta.env.VITE_XXX` 访问

---

## 组件分层规范

按职责分三层，从上到下粒度递减：

```
Page（路由级别）
 └── Section（页面区块）
      └── Component（可复用组件）
```

| 层 | 位置 | 职责 | 示例 |
|---|---|---|---|
| Page | `pages/*/` | 路由对应组件，组装 Sections，获取数据 | `ChatPage.tsx` |
| Section | `pages/*/sections/` | 页面内的独立区块，组合 Components | `ChatPanel.tsx`、`MessageList.tsx` |
| Component | `components/` | 跨页面复用的通用组件 | `MarkdownRenderer.tsx`、`Pagination.tsx` |

### 判断标准

- **放 `components/`**：≥ 2 个页面使用，或明确是通用组件（Layout、Pagination）
- **放 `pages/*/sections/`**：只在一个页面内使用，但逻辑较多需要拆分
- **不拆**：简单页面 < 150 行，直接写在 Page 文件里

### 文件大小

- 单文件不超过 **300 行**（含 JSX + 逻辑 + 样式 import）
- 超过时优先拆出 Section，而不是抽通用 Component
- 纯展示组件（无逻辑）可放宽到 400 行

---

## 样式方案

**选型**：CSS Modules

- Vite 内置支持，零额外依赖
- 样式局部作用域，不会与 Ant Design 样式冲突
- 不引入 CSS-in-JS 的运行时开销

### 规则

- 样式文件就近放置：`Component.tsx` 旁边放 `Component.module.css`
- 不建全局 `styles/` 目录，全局样式写在 `index.css` 或 `App.css` 中
- 禁止行内 `style={{}}`（动态样式用 CSS 变量或 className 切换）

```
pages/chat/
├── ChatPage.tsx
├── ChatPage.module.css          ← 页面级样式
├── ChatPanel.tsx
├── ChatPanel.module.css         ← 区块级样式
└── sections/
    ├── MessageList.tsx
    └── MessageList.module.css   ← 每个组件样式就近
```

### 与 Ant Design 配合

- 布局和自定义组件用 CSS Modules
- Ant Design 组件的样式覆盖用 `className` + CSS Modules 选择器
- 不使用 `!important`

---

## TypeScript 类型规范

### 基本规则

- **禁止 `any`**：用 `unknown` 替代，强制类型收窄后再使用
- **禁止 `@ts-ignore` / `@ts-expect-error`**：解决类型错误，不要压制
- `tsconfig.json` 开启 `strict: true`、`noImplicitAny: true`

### 类型文件组织

```
types/
├── api.ts          # 通用响应类型（Result<T>、PageResult<T>、PageRequest）
├── app.ts          # 与后端 schemas.py 对齐
├── chat.ts         # 与后端 schemas.py 对齐
├── workflow.ts     # 与后端 schemas.py 对齐
└── ...
```

**与后端对齐规则**：
- 每个后端 `schemas.py` 中的 Response Schema 对应前端 `types/` 中的一个文件
- **请求参数**保持 snake_case（匹配后端接口），**响应字段**在 axios 拦截器中统一转为 camelCase
- 前端不重复定义后端已有的枚举（如 AppType、NodeType），从 `types/` 导出共用

### 类型导出规则

```typescript
// ✅ 正确：用 interface 定义数据结构，用 type 定义联合类型和工具类型
interface App {
  id: string;
  name: string;
  type: AppType;
}

type AppType = "chatbot" | "agent" | "workflow";
type AppCreateRequest = Pick<App, "name" | "type">;

// ❌ 错误：用 any 接收后端响应
const data: any = await createApp(body);

// ✅ 正确：显式声明返回类型
const data: App = await createApp(body);
```

---

## 组件编码规范

### 组件定义

- 统一使用**函数式组件 + Hooks**，禁止 class 组件
  - **唯一例外**：ErrorBoundary 必须用 class 组件（React 18 函数组件不支持 `getDerivedStateFromError`）
- 组件必须声明 Props 类型，用 `interface` 定义：

```typescript
// ✅ 正确
interface MessageListProps {
  messages: Message[];
  onLoadMore: () => void;
}

function MessageList({ messages, onLoadMore }: MessageListProps) {
  ...
}

// ❌ 错误：不定义 Props 类型
function MessageList(props: any) { ... }

// ❌ 错误：用 class 组件
class MessageList extends React.Component { ... }
```

### Key 使用规则

- 列表渲染的 Key **必须用唯一 ID**（`id`、`uuid`），禁止用数组 index
- Key 必须稳定（跨渲染不变），禁止用 `Math.random()` 或 `Date.now()`

```tsx
// ✅ 正确：用唯一 ID
{messages.map((msg) => (
  <MessageItem key={msg.id} message={msg} />
))}

// ❌ 错误：用 index（列表增删时导致渲染错乱）
{messages.map((msg, index) => (
  <MessageItem key={index} message={msg} />
))}
```

### Hooks 规则

- **禁止条件调用 Hooks**：`useState`、`useEffect` 等不能放在 if/for 中
- **useEffect 必须声明依赖数组**：禁止省略（ESLint `react-hooks/exhaustive-deps` 规则）
- **useEffect 清理副作用**：定时器、事件监听、SSE 连接必须在 cleanup 函数中释放

```typescript
// ✅ 正确：声明依赖 + 清理
useEffect(() => {
  const timer = setInterval(poll, 5000);
  return () => clearInterval(timer);
}, [poll]);

// ❌ 错误：省略依赖
useEffect(() => {
  fetchData(id);
});  // 每次 render 都执行
```

### 禁止事项

- **禁止在 render 中创建函数/对象引用**（用 `useCallback` / `useMemo` 缓存）：
  - 例外：组件顶层的简单事件处理不需要缓存
- **禁止通过 Props 传递 JSX 字符串**：用 ReactNode
- **禁止直接操作 DOM**：用 React ref，不用 `document.getElementById`

---

## 表单规范

### 基本规则

- 统一使用 **Ant Design Form 组件**，不手写表单逻辑
- 表单校验用 Form 自带的 `rules`，不手写校验函数
- 表单提交必须**防重复提交**（按钮 disabled 或 loading 状态）

### 防重复提交

```typescript
// ✅ 正确：提交时 disabled 按钮
const [submitting, setSubmitting] = useState(false);

const onFinish = async (values: AppCreateRequest) => {
  setSubmitting(true);
  try {
    await createApp(values);
    navigate("/apps");
  } finally {
    setSubmitting(false);
  }
};

return (
  <Form onFinish={onFinish}>
    ...
    <Button type="primary" htmlType="submit" loading={submitting}>
      创建
    </Button>
  </Form>
);
```

### 表单校验

```typescript
// ✅ 正确：用 Ant Design Form rules
<Form.Item
  name="name"
  label="应用名称"
  rules={[
    { required: true, message: "请输入应用名称" },
    { max: 100, message: "名称不超过 100 个字符" },
  ]}
>
  <Input />
</Form.Item>

// ❌ 错误：手写校验逻辑
const handleSubmit = () => {
  if (!name) {
    setError("请输入名称");
    return;
  }
  ...
};
```

---

## 列表渲染规范

- **Key 必须用唯一 ID**，见上方「Key 使用规则」
- **空列表展示**：列表为空时显示 Ant Design `Empty` 组件，不留空白
- **加载状态**：首次加载用 `Spin`，加载更多用列表底部 loading 指示器

```typescript
// 列表页标准结构
function AppList() {
  const { data, isLoading } = useQuery({ queryKey: ["apps"], queryFn: listApps });

  if (isLoading) return <Spin />;
  if (!data?.items.length) return <Empty description="暂无应用" />;

  return (
    <div>
      {data.items.map((app) => (
        <AppCard key={app.id} app={app} />
      ))}
    </div>
  );
}
```
