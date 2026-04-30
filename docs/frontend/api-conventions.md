# 前端 API 调用约定

> 详细内容请参考 CLAUDE.md 第 1.7 节

## axios 实例配置

```typescript
// services/api.ts
import axios from "axios";
import type { Result } from "@/types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 30000,
});

// 响应拦截器：统一处理业务错误码
api.interceptors.response.use(
  (response) => {
    const data = response.data as Result<unknown>;
    if (data.code !== 200) {
      return Promise.reject(new Error(data.message));
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 跳转登录
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default api;
```

## API 函数约定

```typescript
// services/app.ts
import api from "./api";
import type { Result, PageResult } from "@/types/api";
import type { App, AppCreateRequest } from "@/types/app";

export async function listApps(page = 1, pageSize = 20) {
  const { data } = await api.get<PageResult<App>>("/api/v1/apps", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function createApp(body: AppCreateRequest) {
  const { data } = await api.post<Result<App>>("/api/v1/apps", body);
  return data.data;
}
```

**规则**：
- 每个 API 函数对应一个后端端点，函数名 = `{操作}{资源}`（listApps、createApp、getApp）
- 返回类型必须显式声明（`Result<App>`、`PageResult<App>`）
- 禁止在组件中直接调 axios，统一通过 `services/*.ts`

---

## SSE 流式调用约定

Chat 对话使用 SSE（Server-Sent Events）接收 LLM 流式输出，通过 `useSSE` hook 统一管理。

### useSSE hook 接口

```typescript
// hooks/useSSE.ts
function useSSE(url: string, body: Record<string, unknown>) {
  return {
    data: string;            // 累积拼接的完整消息
    isStreaming: boolean;    // 是否正在接收
    error: Error | null;     // 连接错误
    abort: () => void;       // 手动中止
  };
}
```

### 消息拼接规则

- 后端逐 token 发送 delta：`data: {"delta": "你"}`
- 前端在 chatStore 中用 `updateMessage` 累加拼接，不替换：

```typescript
// ✅ 正确：delta 累加
updateMessage: (messageId, delta) => set((state) => ({
  messages: state.messages.map((msg) =>
    msg.id === messageId ? { ...msg, content: msg.content + delta } : msg
  ),
}));

// ❌ 错误：每次用完整内容替换（丢中间状态，闪烁）
updateMessage: (messageId, fullContent) => set((state) => ({
  messages: state.messages.map((msg) =>
    msg.id === messageId ? { ...msg, content: fullContent } : msg
  ),
}));
```

### 连接中断处理

| 场景 | 处理 |
|---|---|
| 网络断开 | 不自动重连。SSE 是一次性对话流，重连会丢上下文。提示用户"连接中断，请重新发送" |
| 服务端 keepalive | 透传，前端不处理。由 `useSSE` 内部消费 `: keepalive` 注释帧 |
| 后端主动关闭旧连接 | 同一对话重复发请求时，后端关闭旧 SSE。前端视为正常结束 |

### 中止规则

```typescript
// 用户切换对话或发送新消息时，必须 abort 旧请求
const { abort, isStreaming } = useSSE("/api/v1/chat/completions", body);

// 切换对话时中止
useEffect(() => {
  return () => { if (isStreaming) abort(); };
}, [conversationId]);
```

**规则**：
- 组件卸载时自动 abort（useSSE 内部在 useEffect cleanup 中关闭连接）
- 用户手动点击"停止生成"时调用 `abort()`
- abort 后不清空已接收的内容（保留部分回复）

---

## 错误处理规范

### 三层错误处理

```
层级 1：axios 拦截器 → 统一处理 401 跳转、网络错误、业务错误码
层级 2：TanStack Query → 请求失败时展示错误状态，自动重试
层级 3：ErrorBoundary → 捕获组件渲染崩溃，展示兜底页面
```

### API 错误展示

| 错误类型 | 处理方式 | 示例 |
|---|---|---|
| 401 未认证 | 拦截器自动跳转 `/login` | — |
| 400 参数错误 | Form 字段级提示 | `Form.setFields([{ name, errors }])` |
| 404 资源不存在 | 跳转 404 页面 | `navigate("*")` |
| 429 限流 | `message.warning` 提示 | "请求过于频繁，请稍后再试" |
| 500 服务端错误 | `message.error` 提示 | "服务异常，请稍后再试" |
| 网络超时 | `message.error` 提示 | "网络超时，请检查网络连接" |

```typescript
// 组件中的错误处理示例（TanStack Query）
const { data, error, isLoading } = useQuery({
  queryKey: ["apps"],
  queryFn: listApps,
});

if (error) {
  // TanStack Query 不会抛到 ErrorBoundary，需要手动展示
  return <Result status="error" title="加载失败" subTitle={error.message} />;
}
```

### ErrorBoundary

- 在 `App.tsx` 根组件外包裹 `ErrorBoundary`
- 捕获子组件渲染崩溃（TypeError、Cannot read properties of undefined 等）
- 展示兜底页面，提供"刷新页面"按钮
- **不捕获**：事件处理函数中的错误（用 try/catch）、异步错误（用 TanStack Query 的 error 状态）

```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="500"
          title="页面出错了"
          extra={<Button onClick={() => window.location.reload()}>刷新页面</Button>}
        />
      );
    }
    return this.props.children;
  }
}
```

### 全局未捕获错误

```typescript
// main.tsx 中注册全局错误处理
window.addEventListener("unhandledrejection", (event) => {
  console.error("未捕获的 Promise 错误:", event.reason);
  message.error("发生未知错误");
});
```

### 禁止事项

- **禁止 `catch` 后吞错误**：catch 里什么都不做，用户看不到任何反馈
- **禁止 `alert()` 展示错误**：用 Ant Design 的 `message.error()` 或 `notification.error()`
- **禁止在错误消息中暴露后端堆栈**：只展示用户可理解的描述
