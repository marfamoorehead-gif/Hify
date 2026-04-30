# Hify — CLAUDE.md

## 项目概述

### 产品定位

Hify 是一个面向团队内部的简化版 AI Agent 平台，灵感来源于 Dify。支持构建对话助手、智能代理和自动化工作流，提供 RAG 知识库检索和工具集成能力。一人开发，20-50 人使用，Docker + Kubernetes 部署。

### 做什么（V1 MVP）

- **三种应用类型**：Chatbot（对话助手）、Agent（智能代理）、Workflow（自动化工作流）
- **工作流引擎**：7 个核心节点 — LLM、知识检索、HTTP 请求、代码执行、条件分支、模板、变量赋值
- **RAG 知识库**：向量索引 + 混合检索 + 文件导入（DOCX/TXT，单文件 ≤ 20MB）+ 自动分块
- **模型管理**：OpenAI 兼容协议接入 + Ollama 本地模型 + 模型切换
- **工具集成**：通过 OpenAPI Schema 集成内部 API
- **提示词编辑器**：变量插值、多模型对比调试
- **发布方式**：Web App + RESTful API（SSE 流式输出）
- **基础运维**：结构化日志、健康检查接口、Token 用量统计

### 不做什么（V1 明确排除）

- Chatflow（用 Workflow + 对话记忆节点替代）、Text Generator（用 Chatbot 替代）
- 多模态能力（视觉理解、图像生成）
- 插件市场（Marketplace）、MCP 协议、Agent 策略插件化
- Notion / 网站爬取导入、外部知识库连接
- 嵌入式组件、前端模板定制
- A/B 测试、角色权限、多工作空间、订阅计费
- 外部可观测性平台集成（LangSmith / Langfuse）

### 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | React + TypeScript | React Flow 工作流编辑器，可参考 Dify 前端实现 |
| 后端 | Python FastAPI | AI/LLM SDK 原生支持，流式输出简洁 |
| 数据库 | MySQL 8.* | 关系数据存储（应用、对话、工作流、知识库元数据） |
| 向量库 | ChromaDB | 文档 chunk 向量存储与检索，嵌入进程内运行，零额外运维 |
| 缓存 | Redis | 应用配置、Embedding 结果、检索结果、LLM 响应缓存 |
| 部署 | Docker + Kubernetes + Nginx | K8s 部署，Nginx Ingress 处理 SSE 长连接，hify-web 容器托管静态资源 |

### 本地开发环境

详细配置请参考：[本地开发环境配置](docs/deployment/local-dev.md)

**快速开始**：

```bash
# 1. 启动基础设施（MySQL + Redis）
docker compose up -d

# 2. 后端设置
cd backend && pip install -r requirements.txt && alembic upgrade head
uvicorn hify.main:app --reload

# 3. 前端设置
cd frontend && npm install && npm run dev
```

启动完成后：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 部署架构

#### 组件清单与请求流转

```
浏览器
  │
  │ https://hify.company.com
  ▼
Ingress Controller（集群已有）
  │  SSE 配置：proxy-buffering off, proxy-read-timeout 300
  ▼
hify-web (Deployment, 1 replica)
  │  Nginx 容器：React 静态资源 + /api/* 反代到 hify-api
  │
  │ /api/*
  ▼
hify-api (Deployment, 1 replica + PDB)
  │  FastAPI 后端 + ChromaDB PersistentClient（进程内）
  │  PVC 挂载 ChromaDB 向量数据
  │
  ├──→ MySQL (StatefulSet / 云托管) — 关系数据存储
  ├──→ Redis (StatefulSet / 云托管) — 缓存 + SSE 连接注册
  └──→ 外部 LLM API — OpenAI / GLM / DeepSeek / Ollama
```

**hify-api 用 1 副本的原因**：ChromaDB PersistentClient 是文件锁模式，多副本不能共享 PVC 写入。V2 迁移到 ChromaDB Server 或 Milvus 后再扩副本。

#### 各组件职责

| 组件 | 形态 | 副本 | 职责 | 资源 |
|---|---|---|---|---|
| Ingress Controller | 集群已有 | - | TLS 终结、域名路由、SSE 超时配置 | - |
| hify-web | Deployment | 1 | React 静态资源、前端路由、`/api/*` 反代 | 0.2 CPU / 256Mi |
| hify-api | Deployment | 1 | FastAPI 后端 + ChromaDB 进程内 | 1 CPU / 2Gi |
| MySQL | StatefulSet 或云托管 | 1 | 关系数据存储 | 1 CPU / 2Gi |
| Redis | StatefulSet 或云托管 | 1 | 缓存 + SSE 连接注册 | 0.5 CPU / 512Mi |

持久化卷：`chroma-data` PVC（10Gi）挂载到 hify-api，`mysql-data` PVC（20Gi）挂载到 MySQL。

#### 关键配置

详细 K8s 配置（Ingress、Deployment、Nginx）请参考：[Kubernetes 部署配置](docs/deployment/kubernetes.md)

**关键点**：
- **Recreate 策略**：ChromaDB PersistentClient 用文件锁，RollingUpdate 会导致新旧 Pod 竞争同一 PVC
- **SSE 超时**：Ingress + Nginx 两层均设置 `proxy_read_timeout: 300s`
- **资源限制**：hify-api 1 CPU / 2Gi（请求）→ 2 CPU / 4Gi（限制）

#### 运维预期

- **瓶颈**：核心瓶颈是 LLM API 延迟（5-30 秒）和 Provider 并发限制
- **SSE 保障**：Ingress + hify-web 两层关闭 proxy_buffering，Python 层 15 秒 keepalive
- **LLM 容错**：429 限流排队重试、多 Key 轮询、Fallback 降级模型（详见 [LLM 调用规范](docs/backend/llm-integration.md)）
- **监控**：/health 健康检查 + /metrics Prometheus 指标 + 结构化 JSON 日志（含 trace_id）

#### 监控指标与告警

详细监控指标和告警规则请参考：[Kubernetes 部署配置 - 监控指标与告警](docs/deployment/kubernetes.md#监控指标与告警)

**关键告警阈值**：
- ChromaDB 检索 p95 > 2s → CRITICAL
- 总 chunk 数 > 25000 → WARN（一期容量上限）
- 进程内存 > 3.5Gi → CRITICAL（即将 OOM）

### 前端架构

详细内容请参考：
- [前端架构总览](docs/frontend/architecture.md)
- [API 调用约定](docs/frontend/api-conventions.md)
- [状态管理（Zustand）](docs/frontend/state-management.md)
- [路由设计](docs/frontend/routing.md)

**技术栈**：React 18 + TypeScript + Zustand + TanStack Query + Ant Design + Vite

**核心设计原则**：
- 按功能分目录（pages/、components/、hooks/、services/、stores/、types/）
- 服务端状态用 TanStack Query，客户端临时状态用 Zustand
- 组件按职责分层（Page → Section → Component），避免单文件超过 300 行
- API 调用统一通过 `services/*.ts`，禁止在组件中直接调用 axios
- SSE 流式调用用自定义 `useSSE` hook，支持中断和保活

## 行为指令

### 写代码时
- 每个功能用最简单直接的方式实现
- 不引入不必要的设计模式，除非我明确要求
- 不做过度抽象
- 不引入技术栈以外的依赖，需要时先问我
- 所有外部调用必须有超时设置
- 配置项外化到 .env 文件，通过 Pydantic BaseSettings 读取，不硬编码
  
### 改代码时
- 先理解相关模块的设计意图
- 不要为了新功能破坏已有接口契约
- 改完确保已有测试通过
  
### 不确定时
- 架构选择给我 2-3 个方案对比，我来拍板
- 规范没覆盖的情况，先问我，不要自己编规矩

### 编码规范

编码规范确保代码质量和一致性。详细内容请参考：

- [命名规范](docs/coding-standards/naming.md) — 模块/包名、类名、函数/方法/变量、常量命名约定
- [异常处理规范](docs/coding-standards/error-handling.md) — 异常捕获、异常链、异常抛出规范
- [日志规范](docs/coding-standards/logging.md) — 日志级别、结构化日志、敏感信息保护
- [并发规范](docs/coding-standards/concurrency.md) — 异步编程、共享状态、资源管理

#### 核心原则

**命名（5 条）**
- N1. 模块/包名：全小写 + 下划线，不超 3 个单词
- N2. 类名：PascalCase，异常类以 Error 结尾
- N3. 函数/方法/变量：snake_case，布尔返回用 is_/has_/can_ 前缀
- N4. 常量：全大写 + 下划线，集中在模块顶部或 core/config.py
- N5. 禁止单字母变量（循环计数器 i/j/k 除外）和 Python 关键字/内置名

**异常处理（5 条）**
- E1. 禁止裸 except，必须指定异常类型
- E2. 禁止吞异常（except 后 pass 或只有 ...）
- E3. 用 raise ... from e 保留异常链，不要丢原始堆栈
- E4. 不在 service 层抛 HTTPException（唯一例外：core/security.py 认证鉴权）
- E5. try 块只包真正可能抛异常的代码，不要包整段逻辑

**日志（5 条）**
- L1. 用 structlog 或标准库 logging，JSON 格式输出，每条日志必须含 trace_id
- L2. 日志级别严格区分（ERROR/WARNING/INFO/DEBUG）
- L3. 日志不用 f-string 拼消息，用结构化字段
- L4. 禁止在日志中打印敏感信息
- L5. ERROR 日志必须含上下文字段（谁、什么操作、什么错误、影响范围）

**并发（5 条）**
- C1. 禁止在 async 函数中调用同步阻塞 I/O（requests、time.sleep、subprocess）
- C2. 共享状态必须加锁或用 asyncio 原语，禁止裸 dict/flag 做并发控制
- C3. async 函数签名必须加 async，调用必须加 await，禁止漏写
- C4. 后台任务用 asyncio.create_task，不要用裸协程（fire-and-forget 会丢异常）
- C5. 依赖注入的资源（db session、httpx client）不要跨请求共享或存储为类变量

### 测试规范

详细内容请参考：[pytest 测试规范](docs/testing/pytest-guide.md)

#### 核心原则

**测试类型**
- 单元测试：不依赖外部服务，测试业务逻辑和 Pydantic 校验
- 集成测试：需要 MySQL/Redis，测试 API 端点和完整流程

**Mock 约定**
- 外部调用必须 mock，数据库用测试实例
- Unit 测试：Mock LLM API、Redis、ChromaDB、外部 HTTP
- Integration 测试：Mock LLM API（用预录响应），用真实 MySQL 和 FastAPI

**覆盖率目标**
- service.py ≥ 90%（核心业务逻辑）
- router.py ≥ 80%（路由调度）
- models.py / schemas.py ≥ 70%（默认值、校验规则）
- 整体 ≥ 80%（CI 门禁）

**测试命名**
- 格式：`test_{方法名}_{场景}_{预期结果}`
- 示例：`test_create_app_with_valid_data_returns_201()`

**运行命令**
```bash
pytest                                    # 全量测试
pytest tests/unit/chat/                   # 单模块
pytest --cov=hify --cov-report=term-missing  # 带覆盖率
pytest tests/integration/                 # 只跑集成测试
```


### 代码组织：按业务域分包（Domain Modular）

单体应用，按业务域组织代码，每个模块自包含路由/服务/模型/Schema。后续拆微服务时一个目录对应一个服务。

```
hify/
├── main.py                     # FastAPI 入口，挂载各模块路由
├── core/                       # 全局基础设施（不放业务逻辑）
│   ├── config.py               #   配置管理
│   ├── database.py             #   DB 连接池、Session 工厂
│   ├── redis.py                #   Redis 连接
│   ├── exceptions.py           #   全局异常基类 + 处理器
│   ├── security.py             #   认证鉴权
│   ├── events.py               #   应用生命周期（startup/shutdown）
│   └── cache.py                #   缓存工具函数
│
├── model_provider/             # 模型提供商管理
│   ├── router.py               #   路由
│   ├── service.py              #   业务逻辑
│   ├── models.py               #   ORM
│   ├── schemas.py              #   Pydantic DTO
│   ├── llm_client.py           #   LLM 调用封装（OpenAI 兼容协议）
│   ├── key_pool.py             #   API Key 轮询池（多 Key 轮询 + 冷却）
│   ├── retry.py                #   重试策略（指数退避 + Retry-After）
│   └── exceptions.py           #   领域异常
│
├── agent/                      # Agent 配置与执行
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   ├── schemas.py
│   ├── executor.py             #   Agent 执行引擎（ReAct / Function Calling）
│   ├── strategy.py             #   推理策略抽象
│   └── exceptions.py
│
├── chat/                       # 对话引擎（SSE 流式）
│   ├── router.py
│   ├── service.py
│   ├── models.py               #   Conversation, Message, MessageChunkRef
│   ├── schemas.py
│   ├── sse.py                  #   SSE 流式输出封装
│   ├── context.py              #   对话上下文管理（记忆窗口）
│   └── exceptions.py
│
├── knowledge/                  # 知识库 + RAG
│   ├── router.py
│   ├── service.py
│   ├── models.py               #   Knowledge, Document, Chunk
│   ├── schemas.py
│   ├── pipeline.py             #   文档导入 → 分块 → 索引
│   ├── retriever.py            #   检索引擎（向量 + 关键词混合）
│   ├── embedder.py             #   Embedding 调用封装
│   └── exceptions.py
│
├── workflow/                   #   简版工作流引擎
│   ├── router.py
│   ├── service.py
│   ├── models.py               #   Workflow, Node, Edge, Execution
│   ├── schemas.py
│   ├── engine.py               #   DAG 执行引擎
│   ├── nodes/                  #   节点实现
│   │   ├── base.py             #     节点基类
│   │   ├── llm.py              #     LLM 节点
│   │   ├── knowledge.py        #     知识检索节点
│   │   ├── http.py             #     HTTP 请求节点
│   │   ├── code.py             #     代码执行节点
│   │   ├── condition.py        #     条件分支节点
│   │   ├── template.py         #     模板节点
│   │   └── variable.py         #     变量赋值节点
│   └── exceptions.py
│
├── tool/                       #   工具集成（OpenAPI Schema + HTTP 调用）
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   ├── schemas.py
│   ├── connector.py            #   工具连接器（HTTP 调用执行）
│   ├── openapi_parser.py       #   OpenAPI Schema 解析 → 工具定义
│   └── exceptions.py
│
└── shared/                     #   模块间共享（不放业务逻辑）
    ├── types.py                #   公共类型定义
    ├── schemas.py              #   统一响应格式（Result、PageResult、PageRequest）
    ├── pagination.py           #   分页工具
    ├── logging.py              #   trace_id 日志工具
    └── metrics.py              #   Prometheus 指标注册与采集
```

### 模块间依赖规则

```
model_provider  ← 被所有模块依赖（LLM 调用、Embedding）
chat           → model_provider, knowledge, agent
agent          → model_provider, tool
workflow        → model_provider, knowledge
knowledge      → model_provider（Embedding）
tool           → 不依赖其他业务模块
```

约束：模块间通过接口依赖注入，不直接 import 其他模块的 service 实现。V1 阶段如果某模块只有一个实现，允许直接 import 具体实现类，待出现第二个实现时再提取 Protocol 重构。

### 代码组织规范

详细内容请参考：[后端架构规范](docs/backend/architecture.md)

#### 核心原则

**一、模块内部分层**

每个业务模块内部严格按以下 4 层组织，不可混用：

```
模块/
├── router.py      # 路由层：HTTP 调度
├── service.py     # 服务层：业务逻辑编排
├── models.py      # 数据层：ORM 模型
└── schemas.py     # 契约层：请求/响应 DTO
```

**职责分工**：
- **router.py**：定义 FastAPI APIRouter，调用 service.py，不写业务逻辑
- **service.py**：编排业务逻辑，返回 Pydantic Schema 或 ORM 模型
- **models.py**：定义 SQLAlchemy ORM 模型，纯数据结构
- **schemas.py**：定义 Pydantic BaseModel，用于请求体校验和响应序列化

**二、异常处理规范**

- router.py / service.py 只抛 `HifyBaseException` 子类，不抛 `HTTPException`
- 唯一可以使用 `HTTPException` 的地方是认证鉴权（`core/security.py`）
- 全局异常处理器统一将领域异常转为 HTTP 响应

**错误码分段规范**：
- 40000-40999：请求参数 / 业务逻辑错误
- 41000-41999：认证授权错误
- 42000-42999：LLM / Provider 相关错误
- 43000-43999：工作流执行错误
- 44000-44999：知识库 / RAG 相关错误
- 45000-45999：工具调用相关错误
- 50000-50999：系统内部错误（兜底）

**三、跨模块调用规则**

**允许的调用方式**：
- service.py → 同模块 models.py（直接 import + ORM 操作）
- service.py → 其他模块 service.py（通过 FastAPI Depends() 注入接口）
- router.py → 同模块 service.py（直接实例化或 Depends()）
- 任何文件 → core/、shared/、其他模块 schemas.py（直接 import）

**禁止的调用方式**：
- service.py 直接 import 其他模块的 service.py 实现类
- router.py 直接操作数据库（必须经过 service.py）
- models.py import 任何非 core/ 或标准库的模块
- 跨模块直接 import ORM 模型（用 app_id 等 ID 关联，不建跨模块外键）

**四、数据库操作规范**

详细内容请参考：
- [数据库 Schema 设计](docs/database/schema-design.md)
- [数据库迁移规范](docs/database/migrations.md)
- [SQL 编写规范](docs/database/sql-best-practices.md)

**核心原则**：
- 每个 service.py 通过构造函数接收 `AsyncSession`
- 同一请求内的多个 DB 操作共用同一个 Session
- 事务由 `get_db` 依赖自动管理（请求成功 commit，异常 rollback）
- 默认使用强一致性（共享 Session），只有明确的异步/后台任务使用最终一致性
- 跨模块通过 ID 关联，不建跨模块外键

**事务安全规则**：
- 事务内禁止 RPC/HTTP 调用（先完成 DB 操作并 commit，再调外部接口）
- 事务要尽量短（先在内存中准备好数据，再开事务一气呵成写入）
- 禁止在循环中开事务（改为批量收集后一次 commit）

**向量存储方案**：
- V1 使用 ChromaDB 作为向量存储，嵌入 FastAPI 进程内运行（PersistentClient）
- MySQL 存储文档元数据和分块文本，ChromaDB 存储向量化后的 embedding 并负责检索
- 职责划分：MySQL 存关系数据，ChromaDB 存向量数据

**五、SSE 连接管理规范**

chat/sse.py 必须处理以下场景：
- **连接争用**：同一用户同一对话发起新请求时，服务端主动关闭旧 SSE 连接
- **保活机制**：LLM 思考时间可能超过 15 秒，用 `asyncio.wait_for` 在 token 间隔插入 SSE 注释帧（`: keepalive\n\n`），配合 Nginx `proxy_read_timeout 300s` 双重保障

**六、LLM 调用规范**

详细内容请参考：[LLM 调用规范](docs/backend/llm-integration.md)

model_provider 模块负责与外部 LLM API 交互。所有 Provider 走 OpenAI 兼容协议（`/v1/chat/completions`），用 `httpx.AsyncClient` 统一调用。

**四个维度**：

1. **线程管理** — 全 async，零阻塞
   - 全程 async，不使用线程池
   - `httpx.AsyncClient` 原生支持 async HTTP + SSE 流式，无阻塞点
   - `httpx.AsyncClient` 全局单例，在 `core/events.py` 的 shutdown 中 `await client.aclose()`

2. **超时分级**
   - 流式对话（SSE）：connect 10s，read 300s
   - 非流式（Embedding / 工具调用）：connect 10s，read 60s
   - 健康检查（Provider 连通性）：connect 5s，read 10s

3. **重试策略**
   - 429 Rate Limit：重试，指数退避 + 尊重 `Retry-After` 头
   - 500/502/503 服务端错误：重试，指数退避，最多 2 次
   - 连接超时 / 网络错误：重试，指数退避，最多 2 次
   - 401/403 认证失败、400 请求格式错误：不重试，立即失败
   - 流式中途断开：不重试，已输出部分 token，无法重放

4. **容错降级**
   - Layer 1：Key 轮询（同 Provider 多 Key，429 时冷却当前 Key 切下一个）
   - Layer 2：Fallback 模型（降级到更便宜/更稳定的模型）
   - Layer 3：返回错误（LLMRateLimitError / LLMServiceUnavailableError）

### 新增功能的操作清单

给模块新增一个功能时，按顺序改动以下文件：

```
1. {module}/models.py       — 新增/修改 ORM 模型
2. {module}/schemas.py      — 新增请求/响应 Schema
3. {module}/exceptions.py   — 新增领域异常（如需要）
4. {module}/service.py      — 新增业务方法
5. {module}/router.py       — 新增路由，调用 service 方法
6. main.py                  — 无需改动（路由已挂载）
```

新增一个模块时：

```
1. 创建 {module}/ 目录
2. 创建 models.py, schemas.py, exceptions.py, service.py, router.py
3. 在 main.py 中挂载路由：app.include_router(module_router, prefix="/api/v1/{module}")
4. V1 阶段：如需被其他模块调用，直接 export 具体实现类
   V2 阶段：当同一接口出现第二个实现时，提取 Protocol 到 shared/types.py
```
