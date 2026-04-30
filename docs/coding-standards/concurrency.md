# 并发规范

> 详细内容请参考 CLAUDE.md 第 2.4.4 节

## 核心规则

1. **禁止在 async 函数中调用同步阻塞 I/O**（requests、time.sleep、subprocess）
2. **共享状态必须加锁或用 asyncio 原语**，禁止裸 dict/flag 做并发控制
3. **async 函数签名必须加 async**，调用必须加 await，禁止漏写
4. **后台任务用 asyncio.create_task**，不要用裸协程（fire-and-forget 会丢异常）
5. **依赖注入的资源不要跨请求共享或存储为类变量**

## 代码示例

```python
# ✅ 正确：异步 sleep
await asyncio.sleep(1)

# ✅ 正确：包进线程池
await asyncio.to_thread(sync_function, args)

# ❌ 错误：阻塞整个事件循环
time.sleep(1)

# ❌ 错误：同步 HTTP，阻塞事件循环
requests.get(url)

# ✅ 正确：asyncio.Event + Lock
class SSEConnectionManager:
    def __init__(self):
        self._connections: dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    async def register(self, user_id, conversation_id):
        async with self._lock:
            ...

# ❌ 错误：无锁保护
    self._connections[key] = stop_event

# ✅ 正确：async + await
async def get_user(db, user_id):
    return await db.get(User, user_id)

# ❌ 错误：漏写 await，返回 coroutine
async def get_user(db, user_id):
    return db.get(User, user_id)

# ✅ 正确：捕获异常
task = asyncio.create_task(self._index_document_async(doc_id))
task.add_done_callback(self._handle_index_error)

# ❌ 错误：异常被吞
asyncio.create_task(self._index_document_async(doc_id))

# ❌ 错误：类变量共享 session
class AppService:
    db: AsyncSession  # 类变量，多个请求共享同一个 session

# ✅ 正确：每次请求创建新实例
async def create_app(body, db=Depends(get_db)):
    service = AppService(db)
```
