# 测试规范（pytest）

## 一、基本原则

### AIR 原则

单元测试必须满足三个特性：

- **A（Automatic）**：全自动执行，无人工干预。不允许用 `input()`、`print()` 调试，结果通过断言自动判定。
- **I（Independent）**：用例之间互不依赖。禁止测试 A 依赖测试 B 创建的数据，每个测试自建自销。
- **R（Repeatable）**：可重复执行。同样的代码在任何环境跑结果一致，不受时间、网络、外部状态影响。

### BCDE 原则

编写测试用例时覆盖：

- **B（Border）**：边界值测试（空值、最大值、临界值）
- **C（Correct）**：正确的输入得到正确的结果（happy path）
- **D（Design）**：与设计文档对齐，覆盖所有业务规则分支
- **E（Error）**：异常路径必须覆盖（错误输入、外部依赖故障、超时）

### 测试金字塔

```
        ╱  E2E  ╲              少量，覆盖核心流程
       ╱─────────╲             Chat 对话、Workflow 执行、知识库导入检索
      ╱ 集成测试  ╲            适量，覆盖 API 端点和模块交互
     ╱─────────────╲
    ╱   单元测试    ╲          大量，覆盖业务逻辑、校验、工具函数
   ╱─────────────────╲
```

推荐比例：**单元 70% : 集成 20% : E2E 10%**

## 二、目录结构

```
hify/
├── tests/
│   ├── conftest.py              # 全局 fixtures（db session、httpx client、mock 工厂）
│   ├── unit/                    # 单元测试（不依赖外部服务）
│   │   ├── test_models.py       # ORM 模型默认值、约束
│   │   └── {module}/            # 按模块组织
│   │       ├── test_service.py  # service 层逻辑
│   │       └── test_schemas.py  # Pydantic 校验
│   ├── integration/             # 集成测试（需要 MySQL/Redis）
│   │   ├── test_api.py          # API 端到端（TestClient + 真实 DB）
│   │   └── test_workflow.py     # 工作流执行
│   └── fixtures/                # 测试数据工厂
│       ├── factories.py         # 工厂函数（create_app, create_conversation）
│       └── seed_data.py         # 种子数据
├── pytest.ini                   # pytest 配置
└── .coveragerc                  # 覆盖率配置
```

## 三、pytest 配置

```ini
# pytest.ini
[pytest]
testpaths = tests
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short -x
```

```ini
# .coveragerc
[run]
source = hify
omit =
    tests/*
    hify/main.py
    hify/core/events.py

[report]
fail_under = 80
show_missing = true
```

## 四、核心 fixtures

```python
# tests/conftest.py
from sqlalchemy import event
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from hify.main import app
from hify.core.database import Base, get_db

# 测试用独立数据库，不碰开发库
TEST_DSN = "mysql+aiomysql://root:password@localhost:3306/hify_test"

# asyncio_mode = auto 时 pytest-asyncio 自动管理 event loop，
# 无需手动定义 event_loop fixture（0.21+ 版本手动定义会产生冲突警告）

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DSN, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    """每个测试独立事务，测试结束自动 rollback。
    使用 begin_nested()（SAVEPOINT）支持被测代码内部的嵌套事务。"""
    connection = await engine.connect()
    transaction = await connection.begin()
    session = async_sessionmaker(bind=connection)()

    # 嵌套事务：被测代码如果内部调用 session.begin()，
    # 会被 SAVEPOINT 包裹，不会和外层事务冲突
    nested = await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def end_savepoint(session_, transaction_):
        nonlocal nested
        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

## 五、Mock 规范

### 基本规则

**外部调用必须 mock，数据库用测试实例**：

```python
# ✅ 正确：mock LLM 调用，用测试数据库
from unittest.mock import AsyncMock, patch

async def test_chat_completion(client, db_session):
    with patch("hify.model_provider.llm_client.LLMClient.chat") as mock_chat:
        mock_chat.return_value = "Hello from test"
        response = await client.post("/api/v1/chat/completions", json={...})
        assert response.status_code == 200

# ❌ 错误：mock 数据库（丢失 SQL 约束验证、事务行为）
```

### Mock 粒度

| 层 | Mock 什么 | 不 Mock 什么 |
|---|---|---|
| Unit | LLM API、Redis、ChromaDB、外部 HTTP | 业务逻辑、Pydantic 校验 |
| Integration | LLM API（用预录响应） | MySQL（用测试实例）、FastAPI 路由 |

### Mock 编写规范

```python
# ✅ mock 打在调用的位置，不是定义的位置
# 如果 chat/service.py 中 `from hify.model_provider.llm_client import LLMClient`
# 那么 mock 应该打在 chat/service.py 引用的 LLMClient 类上
with patch("hify.chat.service.LLMClient") as MockLLMClient:
    mock_instance = MockLLMClient.return_value
    mock_instance.chat.return_value = "expected response"
    ...

# ✅ mock 返回值要明确，不要用 MagicMock 自动生成
mock_chat.return_value = "expected response"  # 明确
mock_chat.return_value = MagicMock()           # ❌ 不明确，掩盖错误

# ✅ 使用 side_effect 模拟异常
mock_chat.side_effect = httpx.TimeoutException("connect timeout")
```

### 禁止事项

- **禁止 mock 被测方法本身**：测试 `create_app()` 时不应该 mock `create_app()`
- **禁止 mock 标准库基础操作**：如 `datetime`、`json.loads`，除非测试时间敏感逻辑
- **禁止 `return_value=MagicMock()`**：Magic 自动应答会掩盖真实 bug
- **禁止过度 mock**：如果 mock 数量超过断言数量，说明测试设计有问题

## 六、测试命名

```python
# 格式：test_{方法名}_{场景}_{预期结果}
async def test_create_app_with_valid_data_returns_201():
    ...

async def test_create_app_with_duplicate_name_raises_40002():
    ...

async def test_chat_completion_when_llm_timeout_returns_503():
    ...
```

**命名原则**：看名字就知道测什么场景、期望什么结果，无需阅读测试代码。禁止用 `test_feature_works()`、`test_happy_path()` 这种模糊命名。

## 七、断言规范

### 一个测试验证一个行为

```python
# ✅ 正确：一个测试验证一个行为
async def test_create_app_with_valid_data_returns_201(client):
    response = await client.post("/api/v1/apps", json=valid_payload)
    assert response.status_code == 201
    assert response.json()["data"]["name"] == valid_payload["name"]

# ❌ 错误：一个测试验证所有 CRUD 操作
async def test_app_crud(client):
    # 创建、查询、更新、删除全塞一个测试里
    ...
```

**例外**：创建后验证字段完整性属于同一行为的延伸验证，允许附带的断言。

### 禁止的断言方式

```python
# ❌ 禁止：断言 True，永远通过
assert response.json()["success"]

# ✅ 正确：断言具体的值
assert response.json()["success"] is True

# ❌ 禁止：用 try/except 代替断言
try:
    await service.create_app(invalid_data)
    assert False, "Should have raised error"
except ValueError:
    pass

# ✅ 正确：用 pytest.raises
with pytest.raises(ValueError, match="name is required"):
    await service.create_app(invalid_data)
```

## 八、边界值与异常路径

### 必须测试的边界场景

每个接受输入的函数/接口，至少覆盖：

| 场景 | 示例 |
|---|---|
| 空值 / None | `name=None`, `messages=[]` |
| 最大长度 | 名称 255 字符（刚好到限制）、256 字符（超限） |
| 最小值 / 零 | `temperature=0`, `top_p=0`, `limit=0` |
| 超出范围 | `temperature=3.0`（超过 2.0 上限）, `limit=-1` |
| 特殊字符 | 名称包含 `<script>`、`'OR 1=1`、emoji |
| 类型错误 | 字符串传了整数、数组传了字符串 |

### 异常路径覆盖

每个调用外部依赖的地方，必须测试：

```python
# 1. 外部服务超时
async def test_chat_when_llm_timeout_returns_503(client):
    mock_llm.side_effect = httpx.TimeoutException("timeout")
    response = await client.post("/api/v1/chat/completions", json={...})
    assert response.status_code == 503

# 2. 外部服务限流（429）
async def test_chat_when_llm_rate_limited_returns_429(client):
    mock_llm.side_effect = httpx.HTTPStatusError(
        "rate limited", request=..., response=MagicMock(status_code=429)
    )
    response = await client.post("/api/v1/chat/completions", json={...})
    assert response.status_code == 429

# 3. 数据库约束冲突
async def test_create_app_with_duplicate_name_raises_conflict(client):
    await client.post("/api/v1/apps", json={"name": "dup"})
    response = await client.post("/api/v1/apps", json={"name": "dup"})
    assert response.status_code == 409

# 4. 参数校验失败
async def test_create_app_with_invalid_type_returns_422(client):
    response = await client.post("/api/v1/apps", json={"name": 12345})
    assert response.status_code == 422
```

## 九、测试数据管理

### 原则

- **自建自销**：每个测试自己准备数据，不依赖其他测试留下的数据
- **幂等性**：同样的测试跑 N 遍结果一致
- **隔离性**：测试之间不共享可变状态

### 工厂函数

```python
# tests/fixtures/factories.py
from hify.model_provider.schemas import ModelProviderCreate

def make_provider(**overrides):
    """创建模型提供商测试数据，支持任意字段覆盖"""
    defaults = {
        "name": "test-openai",
        "provider_type": "openai",
        "api_key": "sk-test-xxxxx",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4", "gpt-3.5-turbo"],
    }
    return ModelProviderCreate(**{**defaults, **overrides})
```

### 清理策略

```python
# 方式 1：数据库事务回滚（推荐，conftest.py 已配置）
# 每个测试结束自动 rollback，测试间完全隔离

# 方式 2：显式清理（用于非数据库状态，如 Redis）
@pytest_asyncio.fixture
async def redis_clean(redis_client):
    yield redis_client
    keys = await redis_client.keys("test:*")
    if keys:
        await redis_client.delete(*keys)

# 方式 3：临时文件（用于知识库文件上传测试）
@pytest.fixture
def temp_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    yield upload_dir
    # tmp_path 自动清理
```

### 禁止事项

- **禁止硬编码测试数据 ID**：用 `uuid4()` 或工厂函数生成
- **禁止测试间共享可变状态**：如全局变量、类属性
- **禁止依赖测试执行顺序**：每个测试必须能独立运行

## 十、覆盖率目标

| 层 | 目标 | 说明 |
|---|---|---|
| service.py | ≥ 90% | 核心业务逻辑 |
| router.py | ≥ 80% | 路由调度 |
| models.py / schemas.py | ≥ 70% | 默认值、校验规则 |
| 整体 | ≥ 80% | CI 门禁 |

### 覆盖率不代表质量

```python
# 以下测试 100% 行覆盖，但 0% 价值
async def test_create_app():
    await service.create_app({"name": "test"})  # 没有断言
```

**真正的覆盖是场景覆盖**，不是行覆盖：正常路径 + 所有异常路径 + 边界值。

## 十一、运行命令

```bash
# 全量测试
pytest

# 单模块
pytest tests/unit/chat/

# 带覆盖率
pytest --cov=hify --cov-report=term-missing

# 只跑集成测试
pytest tests/integration/

# 只跑单元测试
pytest tests/unit/

# 失败时进入调试
pytest --pdb

# 详细输出（看 print）
pytest -s -v
```

## 十二、CI 门禁

提交代码前必须通过：

| 门禁 | 条件 | 不过关时 |
|---|---|---|
| 单元测试 | 全部通过 | 阻止合并 |
| 覆盖率 | 整体 ≥ 80%，service ≥ 90% | 阻止合并 |
| 集成测试 | 全部通过 | 阻止合并 |
| Lint | ruff check 通过 | 阻止合并 |
