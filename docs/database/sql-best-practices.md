# SQL 编写规范

> 详细内容请参考 CLAUDE.md 第 3.3.4 节

## 查询规范

| 规则 | 正确 | 错误 | 原因 |
|---|---|---|---|
| 禁止 `SELECT *` | `SELECT id, name, status` | `SELECT *` | 加字段影响覆盖索引、浪费带宽 |
| `INSERT` 必须指定列名 | `INSERT INTO t(a, b) VALUES(?, ?)` | `INSERT INTO t VALUES(?, ?)` | 加字段会断 |
| 禁止隐式类型转换 | `WHERE id = 123`（int 比 int） | `WHERE id = '123'`（str 比 int） | 索引失效 |
| `IN` 列表 ≤ 500 个 | 分批查或用临时表 | `WHERE id IN (1,2,...,5000)` | 解析慢、占内存 |
| `LIKE` 禁止左模糊 | `name LIKE 'gpt%'` | `name LIKE '%gpt%'` | 左模糊全表扫描 |
| WHERE 禁止对列用函数 | `created_at >= '2026-01-01'` | `YEAR(created_at) = 2026` | 函数导致索引失效 |

```python
# SQLAlchemy 中的正确写法

# ✅ 指定列（ORM 模式自动只查需要的列）
query = select(App.id, App.name, App.status).where(App.deleted == 0)

# ✅ IN 分批
chunk_ids = [...]  # 可能有几千个
results = []
for i in range(0, len(chunk_ids), 500):
    batch = chunk_ids[i:i+500]
    rows = (await db.execute(select(Chunk).where(Chunk.id.in_(batch)))).scalars().all()
    results.extend(rows)

# ✅ 范围查询代替函数
query = select(Message).where(
    Message.created_at >= datetime(2026, 1, 1),
    Message.created_at < datetime(2026, 2, 1),
    Message.deleted == 0,
)

# ❌ 禁止隐式转换（id 是 BigInteger，不能传字符串）
await db.get(App, "123")   # ❌ str 比 bigint
await db.get(App, 123)     # ✅ int 比 bigint
```

## 批量操作规范

| 操作 | 规范 |
|---|---|
| 批量 INSERT | 单次 `add_all` 不超过 500 行，超过分批 |
| 批量 UPDATE | 每批 500 行，用 `WHERE id IN (...)` 限定范围 |
| 禁止循环单条写入 | `for item in items: db.add(item)` ❌；`db.add_all(items)` ✅ |
| 大批量导入（文档分块） | 分批 500 行 `add_all` + 每批 `flush`，不要攒到几万行一次写 |

```python
# ✅ 正确：批量写入分批提交
async def batch_insert_chunks(self, chunks: list[Chunk]):
    for i in range(0, len(chunks), 500):
        batch = chunks[i:i+500]
        self.db.add_all(batch)
        await self.db.flush()
```

## UPDATE/DELETE 安全规范

- UPDATE/DELETE 必须带 WHERE 条件（代码中 SQLAlchemy 的 `update()` / `delete()` 不带 where 会全表操作）
- UPDATE/DELETE 必须带 `deleted == 0` 条件（逻辑删除场景下只操作未删除的数据）

```python
# ✅ 正确：带 WHERE + deleted 条件
await db.execute(
    update(App).where(App.id == app_id, App.deleted == 0).values(status="disabled")
)

# ❌ 错误：不带 WHERE，全表更新
await db.execute(update(App).values(status="disabled"))
```
