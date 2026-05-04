# Hify

面向团队内部的简化版 AI Agent 平台，灵感来源于 Dify。支持构建对话助手、智能代理和自动化工作流，提供 RAG 知识库检索和工具集成能力。

## 功能特性

- **三种应用类型** — Chatbot（对话助手）、Agent（智能代理）、Workflow（自动化工作流）
- **工作流引擎** — 7 个核心节点：LLM、知识检索、HTTP 请求、代码执行、条件分支、模板、变量赋值
- **RAG 知识库** — 向量索引 + 混合检索 + 文件导入（DOCX/TXT）+ 自动分块
- **模型管理** — OpenAI 兼容协议接入 + 多 Key 轮询 + Fallback 降级
- **工具集成** — 通过 OpenAPI Schema 集成内部 API
- **SSE 流式输出** — 实时对话流 + 保活机制
- **基础运维** — 结构化日志、健康检查、Token 用量统计（Prometheus）

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 后端 | Python FastAPI | 异步框架，SSE 流式输出 |
| 前端 | React + TypeScript | 计划中，React Flow 工作流编辑器 |
| 数据库 | MySQL 8.* | 关系数据存储 |
| 向量库 | ChromaDB | 文档向量存储与检索，进程内运行 |
| 缓存 | Redis | 应用配置、检索结果缓存 |
| 部署 | Docker + K8s + Nginx | Nginx Ingress 处理 SSE 长连接 |

## 项目结构

```
backend/
├── hify/
│   ├── main.py                 # FastAPI 入口
│   ├── core/                   # 基础设施（配置、数据库、Redis、异常、安全）
│   ├── model_provider/         # 模型提供商（LLM 调用、Key 轮询、重试）
│   ├── agent/                  # Agent 配置与执行（ReAct / Function Calling）
│   ├── chat/                   # 对话引擎（SSE 流式、上下文管理）
│   ├── knowledge/              # 知识库 + RAG（文档导入、分块、检索）
│   ├── workflow/               # 工作流引擎（DAG 执行、7 种节点）
│   │   └── nodes/              #   LLM / 知识检索 / HTTP / 代码 / 条件 / 模板 / 变量
│   ├── tool/                   # 工具集成（OpenAPI Schema 解析、HTTP 调用）
│   └── shared/                 # 共享（响应格式、分页、日志、指标）
├── alembic/                    # 数据库迁移
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 启动基础设施

```bash
# MySQL + Redis（需要先配置 docker-compose.yml）
docker compose up -d
```

### 2. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填写 MySQL、Redis 连接信息和 LLM API Key

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn hify.main:app --reload --port 8080
```

### 3. 前端（计划中）

```bash
cd frontend && npm install && npm run dev
```

### 访问地址

| 服务 | 地址 |
|---|---|
| 后端 API | http://localhost:8080 |
| API 文档 | http://localhost:8080/docs |
| 健康检查 | http://localhost:8080/health |

## API 路由

| 模块 | 路由前缀 |
|---|---|
| 模型提供商 | `/api/v1/model-providers` |
| Agent | `/api/v1/agents` |
| 对话 | `/api/v1/chat` |
| 知识库 | `/api/v1/knowledge` |
| 工作流 | `/api/v1/workflows` |
| 工具 | `/api/v1/tools` |

## 文档

### 架构与设计

| 文档 | 说明 |
|---|---|
| [后端架构](docs/backend/architecture.md) | 模块分层、跨模块调用、数据库操作规范 |
| [前端架构](docs/frontend/architecture.md) | 组件分层、技术栈选型 |
| [LLM 调用规范](docs/backend/llm-integration.md) | 线程管理、超时分级、重试策略、容错降级 |

### 数据库

| 文档 | 说明 |
|---|---|
| [Schema 设计](docs/database/schema-design.md) | 表结构设计、字段规范 |
| [迁移规范](docs/database/migrations.md) | Alembic 迁移工作流 |
| [SQL 编写规范](docs/database/sql-best-practices.md) | 查询优化、索引策略 |

### 前端

| 文档 | 说明 |
|---|---|
| [API 调用约定](docs/frontend/api-conventions.md) | 统一请求封装、错误处理 |
| [状态管理](docs/frontend/state-management.md) | Zustand + TanStack Query |
| [路由设计](docs/frontend/routing.md) | 页面路由规划 |

### 编码规范

| 文档 | 说明 |
|---|---|
| [命名规范](docs/coding-standards/naming.md) | 模块、类、函数、变量命名约定 |
| [异常处理](docs/coding-standards/error-handling.md) | 异常捕获、异常链、错误码分段 |
| [日志规范](docs/coding-standards/logging.md) | 结构化日志、trace_id、敏感信息保护 |
| [并发规范](docs/coding-standards/concurrency.md) | 异步编程、共享状态、资源管理 |

### 测试与部署

| 文档 | 说明 |
|---|---|
| [pytest 测试规范](docs/testing/pytest-guide.md) | 测试类型、Mock 约定、覆盖率目标 |
| [本地开发环境](docs/deployment/local-dev.md) | 完整本地开发配置指南 |
| [Kubernetes 部署](docs/deployment/kubernetes.md) | K8s 配置、资源规划、监控告警 |

## 部署

Docker + Kubernetes 部署，Nginx Ingress 处理 TLS 和 SSE 长连接。核心组件：

- **hify-web** — Nginx 容器托管前端静态资源 + `/api/*` 反代
- **hify-api** — FastAPI 后端 + ChromaDB 进程内（1 副本，文件锁限制）
- **MySQL** — 关系数据存储
- **Redis** — 缓存 + SSE 连接注册

详细配置见 [Kubernetes 部署文档](docs/deployment/kubernetes.md)。

## License

Private — 内部使用
