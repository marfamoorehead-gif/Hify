# 后端架构规范

> 详细内容请参考 CLAUDE.md 第 3.3 节

## 代码组织：按业务域分包（Domain Modular）

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
├── knowledge/                  #   知识库 + RAG
│   ├── router.py
│   ├── service.py
│   ├── models.py               #   Knowledge, Document, Chunk
│   ├── schemas.py
│   ├── pipeline.py             #   文档导入 → 分块 → 索引
│   ├── retriever.py            #   检索引擎（向量 + 关键词混合）
│   ├── embedder.py             #   Embedding 调用封装
│   └── exceptions.py
│
├── workflow/                   # 简版工作流引擎
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
├── tool/                       # 工具集成（OpenAPI Schema + HTTP 调用）
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   ├── schemas.py
│   ├── connector.py            #   工具连接器（HTTP 调用执行）
│   ├── openapi_parser.py       #   OpenAPI Schema 解析 → 工具定义
│   └── exceptions.py
│
└── shared/                     # 模块间共享（不放业务逻辑）
    ├── types.py                #   公共类型定义
    ├── schemas.py              #   统一响应格式（Result、PageResult、PageRequest）
    ├── pagination.py           #   分页工具
    ├── logging.py              #   trace_id 日志工具
    └── metrics.py              #   Prometheus 指标注册与采集
```

---

## 模块间依赖规则

```
model_provider  ← 被所有模块依赖（LLM 调用、Embedding）
chat           → model_provider, knowledge, agent
agent          → model_provider, tool
workflow        → model_provider, knowledge
knowledge      → model_provider（Embedding）
tool           → 不依赖其他业务模块
```

**约束**：模块间通过接口依赖注入，不直接 import 其他模块的 service 实现。V1 阶段如果某模块只有一个实现，允许直接 import 具体实现类，待出现第二个实现时再提取 Protocol 重构。

---

## 模块内部分层

每个业务模块内部严格按以下 4 层组织，不可混用：

```
模块/
├── router.py      # 路由层：HTTP 调度
├── service.py     # 服务层：业务逻辑编排
├── models.py      # 数据层：ORM 模型
└── schemas.py     # 契约层：请求/响应 DTO
```

### router.py 职责与约束

- 定义 FastAPI APIRouter，声明路径、方法、状态码
- 调用 `Depends()` 注入 Schema 校验、认证、数据库 Session
- 调用 `service.py` 中的方法处理请求
- **不写任何业务逻辑**、不写 if/else/for 循环、不直接操作数据库

### service.py 职责与约束

- 编排业务逻辑：校验、状态转换、调用其他服务、写数据库
- 通过构造函数接收依赖（db session、其他 service 的接口）
- 返回 Pydantic Schema 或 ORM 模型实例
- **不处理 HTTP 语义**（不 raise HTTPException，改用领域异常）

### models.py 职责与约束

- 定义 SQLAlchemy ORM 模型（表名、列、索引、关系）
- 定义数据库级别约束（唯一、非空、外键）
- **不写业务逻辑方法**，只放纯数据结构

### schemas.py 职责与约束

- 定义 Pydantic BaseModel，用于请求体校验和响应序列化
- 用 `ConfigDict(from_attributes=True)` 映射 ORM 模型
- 用 `Field(...)` 声明字段约束（长度、范围、正则）
- 命名约定：`{Entity}CreateRequest`、`{Entity}UpdateRequest`、`{Entity}Response`、`{Entity}ListResponse`

---

## 接口规范

### 路径设计

RESTful 风格：`/api/v1/{资源复数名}`

```
GET    /api/v1/providers               # 列表（分页）
POST   /api/v1/providers               # 创建
GET    /api/v1/providers/{id}          # 详情
PUT    /api/v1/providers/{id}          # 更新
DELETE /api/v1/providers/{id}          # 删除
POST   /api/v1/providers/{id}/test-connection  # 非 CRUD 操作用动词
```

**规则**：
- 资源名用复数、小写、连字符分隔（`/api/v1/model-providers`）
- CRUD 操作用标准 HTTP 方法，不在路径里写动词（`/create-app` ❌）
- 非 CRUD 操作（测试连接、重新索引、执行工作流）用 `POST + 动词` 路径
- 路径中的 `{id}` 为 BigInteger，不是 UUID

### 统一响应

所有接口返回 `Result<T>` 格式：

```python
# shared/schemas.py
class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None

class PageResult(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: list[T] = Field(default_factory=list)  # 空时返回 []，不返回 null
    total: int = 0
    page: int = 1
    page_size: int = 20
```

成功响应示例：

```json
{
    "code": 200,
    "message": "success",
    "data": {"id": 1, "name": "GPT-4o", "type": "chatbot"}
}
```

错误响应示例（由全局异常处理器统一生成）：

```json
{
    "code": 42401,
    "message": "Model provider not found",
    "data": null
}
```

### 分页规范

请求参数：

```python
class PageRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大 100")
```

响应：`Result[list[T]>` 替换为 `PageResult<T>`，包含 `list`、`total`、`page`、`page_size`。

大表分页特殊规则（详见数据库文档）：
- 第一页（`page=1`）返回 `total`
- 翻页时用游标参数 `after` 代替 `page`，不重复查 `total`，改用 `has_more` 标记

### 空值处理

```python
# 响应序列化时的空值规则（Pydantic model 配置）
class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str = ""           # 空字符串，不返回 null
    api_keys: list[str] = []        # 空数组，不返回 null
    status: str = "active"
```

**硬规则**：
- 列表字段空时返回 `[]`，不返回 `null`
- 字符串字段空时返回 `""`，不返回 `null`
- 对象不存在时返回 `null`（`data: null`）
- Pydantic Schema 中所有可空字段必须设 `default=""` 或 `default=[]`

### router.py 示例

```python
# ✅ 合法：路由只做调度
@router.post("/apps", response_model=AppResponse, status_code=201)
async def create_app(
    body: AppCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    app = await AppService(db).create(body, user.id)
    return AppResponse(data=app)

# ❌ 违规：路由里写了业务逻辑
@router.post("/apps")
async def create_app(body: AppCreateRequest, db:Depends(get_db)):
    if body.type not in ["chatbot", "agent", "workflow"]:  # ❌ 业务判断
        raise HTTPException(400)
    existing = await db.execute(select(App).where(...))      # ❌ 直接操作 DB
```

### service.py 示例

```python
# ✅ 合法：服务层编排业务逻辑
class AppService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, body: AppCreateRequest, user_id: str) -> App:
        # 业务校验
        await self._validate_app_limit(user_id)
        # 创建实体
        app = App(name=body.name, type=body.type, owner_id=user_id)
        self.db.add(app)
        await self.db.flush()
        return app

# ❌ 违规：服务层抛 HTTP 异常
async def create(self, body):
    if body.type not in ALLOWED_TYPES:
        raise HTTPException(400, "invalid type")  # ❌ 用领域异常
```

### models.py 示例

```python
# ✅ 合法：纯数据模型
class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

# ❌ 违规：模型里写了业务方法
class App(Base):
    ...
    def can_publish(self):                      # ❌ 业务逻辑不属于 models
        return self.status == "active"
```

### schemas.py 示例

```python
# ✅ 合法
class AppCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    type: Literal["chatbot", "agent", "workflow"]
    description: str | None = Field(default=None, max_length=1024)

class AppResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    type: str
    created_at: datetime
```
