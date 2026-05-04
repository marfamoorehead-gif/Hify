# 前端测试规范

## 技术选型

| 工具 | 用途 |
|---|---|
| Vitest | 测试运行器（Vite 原生集成，零配置） |
| React Testing Library | 组件测试（以用户行为为中心） |
| MSW (Mock Service Worker) | API Mock（拦截网络请求） |
| @testing-library/user-event | 模拟真实用户操作 |

## 配置

### vitest.config.ts

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/main.tsx",
        "src/**/*.d.ts",
        "src/types/**",
        "src/test/**",
      ],
      thresholds: {
        "src/services/**": { branches: 80, functions: 80 },
        "src/hooks/**": { branches: 80, functions: 80 },
        "src/stores/**": { branches: 80, functions: 80 },
      },
    },
  },
});
```

### src/test/setup.ts

```typescript
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
});

// Mock IntersectionObserver（Ant Design 懒加载需要）
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);

// Mock ResizeObserver（React Flow 需要）
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", MockResizeObserver);

// Mock matchMedia（Ant Design 响应式需要）
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

## 测试文件组织

```
src/
├── services/
│   ├── app.ts
│   └── app.test.ts              ← 测试文件就近放置
├── hooks/
│   ├── useSSE.ts
│   └── useSSE.test.ts
├── stores/
│   ├── chatStore.ts
│   └── chatStore.test.ts
├── components/
│   ├── MarkdownRenderer.tsx
│   └── MarkdownRenderer.test.tsx
├── pages/
│   ├── apps/
│   │   ├── AppList.tsx
│   │   └── AppList.test.tsx
│   └── chat/
│       ├── ChatPage.tsx
│       └── ChatPage.test.tsx
└── test/
    ├── setup.ts                  ← 全局 setup
    ├── render.tsx                ← 自定义 render（包裹 Provider）
    └── msw-handlers.ts           ← MSW 请求处理
```

## 测试分类

### 1. 工具函数 / Service 层测试

测试纯函数和 API 调用函数，用 MSW mock 网络请求。

```typescript
// services/app.test.ts
import { describe, it, expect } from "vitest";
import { listApps, createApp } from "./app";
import { server } from "@/test/msw-server";
import { http, HttpResponse } from "msw";

describe("listApps", () => {
  it("返回应用列表", async () => {
    server.use(
      http.get("/api/v1/apps", () =>
        HttpResponse.json({
          code: 200,
          data: { items: [{ id: "1", name: "Test App" }], total: 1 },
        })
      )
    );

    const result = await listApps(1, 20);
    expect(result.items).toHaveLength(1);
    expect(result.items[0].name).toBe("Test App");
  });
});
```

### 2. Store 测试

测试 Zustand store 的状态变更逻辑。

```typescript
// stores/chatStore.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore } from "./chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
  });

  it("addMessage 追加消息", () => {
    const { addMessage } = useChatStore.getState();
    addMessage({ id: "1", role: "user", content: "Hello" });

    const { messages } = useChatStore.getState();
    expect(messages).toHaveLength(1);
    expect(messages[0].content).toBe("Hello");
  });

  it("updateMessage 累加 delta", () => {
    const store = useChatStore.getState();
    store.addMessage({ id: "1", role: "assistant", content: "你" });
    store.updateMessage("1", "好");

    expect(useChatStore.getState().messages[0].content).toBe("你好");
  });

  it("clearMessages 清空消息和对话 ID", () => {
    const store = useChatStore.getState();
    store.addMessage({ id: "1", role: "user", content: "Hello" });
    store.setConversationId("conv-1");
    store.clearMessages();

    expect(useChatStore.getState().messages).toHaveLength(0);
    expect(useChatStore.getState().conversationId).toBeNull();
  });
});
```

### 3. 组件测试

用 React Testing Library 测试用户交互和渲染结果。

```typescript
// components/MarkdownRenderer.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MarkdownRenderer } from "./MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("渲染 Markdown 文本", () => {
    render(<MarkdownRenderer content="**粗体**" />);
    const strong = screen.getByText("粗体");
    expect(strong.tagName).toBe("STRONG");
  });

  it("空内容不报错", () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.innerHTML).toBe("");
  });
});
```

### 4. Hook 测试

用 `@testing-library/react` 的 `renderHook` 测试自定义 hook。

```typescript
// hooks/useSSE.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSSE } from "./useSSE";

// Mock fetchEventSource
vi.mock("@microsoft/fetch-event-source", () => ({
  fetchEventSource: vi.fn(),
}));

describe("useSSE", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("初始状态正确", () => {
    const { result } = renderHook(() =>
      useSSE("/api/v1/chat/completions", { message: "hello" })
    );

    expect(result.current.data).toBe("");
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("abort 中止流式连接", () => {
    const { result } = renderHook(() =>
      useSSE("/api/v1/chat/completions", { message: "hello" })
    );

    act(() => {
      result.current.abort();
    });

    expect(result.current.isStreaming).toBe(false);
  });
});
```

### 5. 页面集成测试

测试完整页面的渲染和用户操作流程。

```typescript
// pages/apps/AppList.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { AppList } from "./AppList";
import { server } from "@/test/mssw-server";
import { http, HttpResponse } from "msw";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe("AppList", () => {
  it("加载并展示应用列表", async () => {
    server.use(
      http.get("/api/v1/apps", () =>
        HttpResponse.json({
          code: 200,
          data: {
            items: [
              { id: "1", name: "助手A", type: "chatbot" },
              { id: "2", name: "代理B", type: "agent" },
            ],
            total: 2,
          },
        })
      )
    );

    renderWithProviders(<AppList />);

    await waitFor(() => {
      expect(screen.getByText("助手A")).toBeInTheDocument();
      expect(screen.getByText("代理B")).toBeInTheDocument();
    });
  });

  it("空列表展示 Empty", async () => {
    server.use(
      http.get("/api/v1/apps", () =>
        HttpResponse.json({
          code: 200,
          data: { items: [], total: 0 },
        })
      )
    );

    renderWithProviders(<AppList />);

    await waitFor(() => {
      expect(screen.getByText("暂无应用")).toBeInTheDocument();
    });
  });
});
```

## MSW 配置

```typescript
// src/test/msw-server.ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

// 默认 handler：未匹配的请求返回 500
const fallbackHandler = http.all("*", () =>
  HttpResponse.json({ code: 500, message: "MSW: 未匹配的请求" }, { status: 500 })
);

export const server = setupServer(fallbackHandler);

// 在 setup.ts 中或 vitest.config.ts 的 globalSetup 中启动
// beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());
```

在 `src/test/setup.ts` 末尾追加：

```typescript
import { server } from "./msw-server";
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## 覆盖率目标

| 层 | 目标 | 说明 |
|---|---|---|
| `services/**` | ≥ 80% | API 调用逻辑、错误处理 |
| `hooks/**` | ≥ 80% | 自定义 hook 状态管理 |
| `stores/**` | ≥ 80% | Zustand store 状态变更 |
| `components/**` | ≥ 70% | 通用组件渲染和交互 |
| `pages/**` | ≥ 60% | 关键页面集成测试 |
| 整体 | ≥ 80% | CI 门禁 |

## 测试命名

格式：`test_{描述}_{场景}_{预期结果}`

```typescript
describe("createApp", () => {
  it("正常参数返回创建的应用", async () => { ... });
  it("重复名称返回 400 错误", async () => { ... });
  it("未认证返回 401 跳转登录", async () => { ... });
});
```

## 运行命令

```bash
vitest                                    # 监听模式
vitest run                                # 单次运行
vitest run src/services/app.test.ts       # 单文件
vitest run --coverage                     # 带覆盖率
vitest run --reporter=verbose             # 详细输出
```

## 规则

### 必须遵守

- **Mock 外部依赖**：API 请求用 MSW，React Flow 等 UI 库用 `vi.mock`
- **测试用户行为**：用 `screen.getByText` / `userEvent.click`，不直接操作 DOM 节点
- **独立测试**：每个测试用例独立，beforeEach 重置状态
- **清理副作用**：定时器、事件监听、SSE 连接在 afterEach 中清理
- **不测试实现细节**：不测试组件内部 state，测试用户能看到的输出

### 禁止事项

- **禁止测试第三方库行为**：不测 Ant Design 组件本身，只测你的使用方式
- **禁止 `as any` 绕过类型**：测试代码同样遵守 TypeScript strict 规则
- **禁止快照测试滥用**：只在样式/结构关键且稳定时用快照，不用于频繁变动的 UI
- **禁止 `waitFor` 无条件使用**：只在异步操作后使用，同步断言直接 expect
