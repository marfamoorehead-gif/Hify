# LLM 调用层规范

> 详细内容请参考 CLAUDE.md 第 3.3.6 节

model_provider 模块负责与外部 LLM API 交互。所有 Provider 走 OpenAI 兼容协议（`/v1/chat/completions`），用 `httpx.AsyncClient` 统一调用。从四个维度管理：线程管理、超时、重试、容错降级。

---

## 线程管理 — 全 async，零阻塞

全程 async，不使用线程池。`httpx.AsyncClient` 原生支持 async HTTP + SSE 流式，无阻塞点。

```
请求链路（全 async）：
user → FastAPI route → ChatService → LLMClient.chat_stream()
                                                ↓
                                          httpx.AsyncClient.stream("POST", ...)
                                                ↓
                                          async for line in response.aiter_lines()
                                                ↓
                                          yield token → SSE → 浏览器
```

`httpx.AsyncClient` 全局单例，在 `core/events.py` 的 shutdown 中 `await client.aclose()`：

```python
# model_provider/llm_client.py
import httpx

_http_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=30.0),
            limits=httpx.Limits(
                max_connections=100,
                max_connections_per_host=20,
            ),
        )
    return _http_client
```

---

## 超时分级

按场景分三级，`httpx.Timeout` 作为参数传入，不写死：

| 场景 | connect | read | 说明 |
|---|---|---|---|
| 流式对话（SSE） | 10s | 300s | LLM 思考可能很长，连接建立要快 |
| 非流式（Embedding / 工具调用） | 10s | 60s | 单次请求，不需要等太久 |
| 健康检查（Provider 连通性） | 5s | 10s | 快速失败 |

```python
class LLMClient:
    STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=30.0)
    DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=30.0)
    HEALTH_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)

    async def chat(self, messages, model, stream=False, timeout=None):
        client = await get_http_client()
        actual_timeout = timeout or (self.STREAM_TIMEOUT if stream else self.DEFAULT_TIMEOUT)
        ...
```

---

## 重试策略

### 重试决策矩阵

| 错误类型 | 是否重试 | 策略 |
|---|---|---|
| 429 Rate Limit | 重试 | 指数退避 + 尊重 `Retry-After` 头 |
| 500/502/503 服务端错误 | 重试 | 指数退避，最多 2 次 |
| 连接超时 / 网络错误 | 重试 | 指数退避，最多 2 次 |
| 401/403 认证失败 | 不重试 | Key 可能失效，立即失败 |
| 400 请求格式错误 | 不重试 | 请求本身有问题，立即失败 |
| 流式中途断开 | 不重试 | 已输出部分 token，无法重放 |

```python
# model_provider/retry.py
import asyncio
import random
import httpx

async def call_with_retry(
    request_fn,           # async callable，执行实际请求
    max_retries: int = 2,
    base_delay: float = 1.0,
):
    """带指数退避的重试，用于非流式调用"""
    for attempt in range(max_retries + 1):
        try:
            return await request_fn()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            # 不可重试 — 直接抛
            if status in (400, 401, 403, 404):
                raise
            # 可重试 — 计算延迟
            if status == 429:
                retry_after = e.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
            else:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            if attempt < max_retries:
                await asyncio.sleep(delay)
            else:
                raise
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)
            else:
                raise
```

流式调用不做重试，失败直接走 Fallback 降级：

```python
async def chat_stream(self, messages, model, ...):
    """流式调用 — 不重试，失败走 Fallback"""
    async def _do_stream():
        client = await get_http_client()
        async with client.stream("POST", url, json=payload, timeout=self.STREAM_TIMEOUT) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                raise httpx.HTTPStatusError(...)
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    yield parse_token(line)
    async for token in _do_stream():
        yield token
```

---

## 容错降级

三层容错，按优先级依次尝试：

```
请求失败
  ↓
Layer 1: Key 轮询（同 Provider 多 Key，429 时冷却当前 Key 切下一个）
  ↓ 全部 Key 耗尽
Layer 2: Fallback 模型（降级到更便宜/更稳定的模型）
  ↓ 无 Fallback 或 Fallback 也失败
Layer 3: 返回错误（LLMRateLimitError / LLMServiceUnavailableError）
```

### 数据模型

```python
# model_provider/models.py
class ModelProvider(Base):
    __tablename__ = "model_providers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)        # "openai", "deepseek", "ollama"
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_keys: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {"keys": ["sk-xxx", "sk-yyy"]}
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("model_providers.id"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)  # "gpt-4o", "deepseek-chat"
    fallback_model_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)  # 0 = 无降级
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
```

### Key 轮询池

```python
# model_provider/key_pool.py
import time

class APIKeyPool:
    """同 Provider 多 Key 轮询 + 冷却"""

    def __init__(self, keys: list[str]):
        self._keys = [k for k in keys if k]
        self._index = 0
        self._cooldown: dict[str, float] = {}  # key → 冷却截止时间

    def next(self) -> str | None:
        """取下一个可用 Key，跳过冷却中的"""
        now = time.monotonic()
        for _ in range(len(self._keys)):
            key = self._keys[self._index % len(self._keys)]
            self._index += 1
            if key not in self._cooldown or self._cooldown[key] <= now:
                return key
        return None  # 全部在冷却中

    def cool(self, key: str, seconds: float):
        """将 Key 标记为冷却（429 时调用）"""
        self._cooldown[key] = time.monotonic() + seconds
```

### 完整调用流程

```python
# model_provider/llm_client.py
class LLMClient:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_request(self, model_id: str, messages: list, stream: bool):
        """带完整容错的调用：Key 轮询 → 重试 → Fallback"""
        model = await self.db.get(Model, model_id)
        provider = await self.db.get(ModelProvider, model.provider_id)

        key_pool = APIKeyPool(provider.api_keys)
        key = key_pool.next()

        if key is None:
            # 所有 Key 都在冷却 → 直接 Fallback
            return await self._try_fallback(model, messages, stream)

        try:
            if stream:
                return self._stream_with_key(provider, key, model, messages)
            else:
                return await call_with_retry(
                    lambda: self._call_with_key(provider, key, model, messages),
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = float(e.response.headers.get("retry-after", 30))
                key_pool.cool(key, retry_after)
                next_key = key_pool.next()
                if next_key:
                    if stream:
                        return self._stream_with_key(provider, next_key, model, messages)
                    else:
                        return await call_with_retry(
                            lambda k=next_key: self._call_with_key(provider, k, model, messages),
                        )
            return await self._try_fallback(model, messages, stream)

    async def _try_fallback(self, model: Model, messages: list, stream: bool):
        """降级到 fallback 模型，无 fallback 则抛异常"""
        if model.fallback_model_id is None:
            raise LLMRateLimitError(detail=f"No fallback for model {model.model_name}")
        return await self._resolve_request(model.fallback_model_id, messages, stream)
```

### 整体流程图

```
用户请求
  │
  ▼
LLMClient.chat / chat_stream
  │
  ├─ 获取 Model 配置（含 fallback_model_id）
  ├─ 获取 Provider 配置（含多 Key 列表）
  │
  ▼
APIKeyPool.next() ──→ Key A
  │                       │
  │              httpx.AsyncClient 请求
  │                       │
  │         ┌──── 200 OK ────┤
  │         │                │
  │    流式: yield token   非流式: call_with_retry (最多 2 次)
  │         │
  │    ┌─ 429 ─── Key 冷却 → next Key ──→ 重试
  │    │
  │    ├─ 5xx ──→ call_with_retry 指数退避
  │    │
  │    ├─ 400/401/403 ──→ 直接抛异常
  │    │
  │    └─ 全部失败 ──→ _try_fallback
  │                         │
  │                   有 fallback ──→ 递归 _resolve_request
  │                   无 fallback ──→ 抛 LLMRateLimitError
```
