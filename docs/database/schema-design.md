# 数据库 Schema 设计规范

> 详细内容请参考 CLAUDE.md 第 3.3.4 节

## 通用字段约定

### 数据库全局配置

```python
# core/database.py — SQLAlchemy 引擎配置
engine = create_async_engine(
    dsn,
    pool_size=10,          # 常驻连接数
    max_overflow=20,       # 峰值可额外创建的连接数
    pool_recycle=1800,     # 连接最长存活 30 分钟，防 MySQL 8 小时断连
    pool_pre_ping=True,    # 每次取连接时检测可用性
    echo=False,
)
```

```sql
-- MySQL 全局配置（my.cnf 或初始化脚本）
-- 字符集：utf8mb4（支持 emoji 和 4 字节字符），不用 utf8
-- 排序规则：utf8mb4_unicode_ci（不区分大小写，适合搜索）
-- 存储引擎：InnoDB（事务、行锁、MVCC），不要用 MyISAM
-- 所有建表语句自动继承：
CREATE DATABASE hify DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 表/列命名规范

| 对象 | 规则 | 正确示例 | 错误示例 |
|---|---|---|---|
| 表名 | 全小写 + 下划线，复数名词，不加项目前缀 | `users` / `conversations` / `message_chunk_refs` | `User` / `hify_users` / `user` |
| 列名 | 全小写 + 下划线，有业务含义 | `created_at` / `owner_id` / `prompt_tokens` | `createdAt` / `cid` / `pt` |
| 关联表 | `{主表}_{从表}`，按主从顺序 | `agent_tool_bindings` | `tool_agent_map` |
| 索引名 | `idx_{表名}_{列名}`（非主键） | `idx_message_conv_created` | `index1` |
| 唯一索引 | `uq_{表名}_{列名}` | `uq_app_name_owner` | `unique_name` |

### 表设计上限

| 规则 | 上限 | 原因 |
|---|---|---|
| 单表字段数 | ≤ 30 | 超过说明职责不单一，考虑拆表 |
| 单行总长度 | ≤ 8KB | InnoDB 页 16KB，行跨页性能差；TEXT 列存溢出页不受此限 |
| 每张表必须有 `__table_args__` 中的 `comment` | — | 一人开发也必须加，3 个月后自己看不懂 |

### 硬规矩（不可违反）

1. **主键用 BIGINT 自增，禁止 UUID** — UUID 随机性导致索引页分裂，写入性能差
2. **禁止 NULL** — 业务空值用空字符串 `""` 或 `0` 代替，所有列 `nullable=False`
3. **金额和 Token 用量用 BIGINT 存最小精度** — 如金额存分（12345 = 123.45 元），Token 存个位，不用 DECIMAL/FLOAT
4. **枚举用 VARCHAR(32)** — 不用 MySQL ENUM（加值要 ALTER TABLE）

### 字段类型定义

**主键**：

```python
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
```

**ID 列（外键引用 / 跨模块关联）**：

```python
# 同模块内：BigInteger + ForeignKey + 索引
app_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("apps.id"), nullable=False, index=True)

# 跨模块：只存 ID，不建 ForeignKey，0 表示未关联
knowledge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
```

**时间戳**：每张表必须有 `created_at`，可选 `updated_at`。

```python
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(
    DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
)
```

**状态/类型字段**：

```python
status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
type: Mapped[str] = mapped_column(String(32), nullable=False)
```

**逻辑删除字段**：所有业务表必须有 `deleted` 字段，禁止物理删除。

```python
deleted: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)  # 0=正常, 1=已删除
```

**金额 / Token 用量**：

```python
# 金额：存最小单位（分），BIGINT
price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)  # 12345 = 123.45 元

# Token 用量：存个位，BIGINT
prompt_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
completion_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
```

**JSON 字段**：

```python
config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # 空值用 {}，不用 NULL
```

---

## 索引设计原则

### 规则 1：每个 ForeignKey 列必须有索引

MySQL 不会自动给子表的外键列建索引。漏掉会导致外键检查时全表扫描。

```python
# 正确
conversation_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("conversations.id"), nullable=False, index=True
)

# 错误 — 外键无索引
conversation_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("conversations.id"), nullable=False
)  # ❌
```

### 规则 2：逻辑删除字段 deleted 必须进索引

几乎所有查询都带 `WHERE deleted = 0`，不把 `deleted` 加进索引等于索引白建。

```python
# ✅ 正确 — deleted 在索引中
__table_args__ = (
    Index("idx_agent_user", "user_id", "deleted"),
)

# ❌ 错误 — 不含 deleted，查询 WHERE user_id = ? AND deleted = 0 无法完全命中索引
__table_args__ = (
    Index("idx_agent_user", "user_id"),
)
```

### 规则 3：复合索引等值列在前，范围列在后

MySQL 索引的最左前缀原则：等值过滤（`=`）的列放前面，范围/排序列放后面。顺序错了索引利用率暴跌。

```python
# 查询模式：WHERE conversation_id = ? AND deleted = 0 ORDER BY created_at DESC
# 索引：等值列在前（conversation_id, deleted），范围/排序列在后（created_at）
__table_args__ = (
    Index("idx_message_conv_created", "conversation_id", "deleted", "created_at"),
)
```

### 规则 4：一个表不超过 5 个索引（含主键）

索引加速查询但拖慢写入。50-500 人规模写入量不大，但原则要守住。

建索引的判断标准：
- WHERE 条件中高频出现的列 → 建索引
- JOIN 关联列 → 建索引
- ORDER BY / GROUP BY 列 → 如果前面的等值列已建复合索引，排序列可以包含在内
- SELECT 只返回的列 → 不建索引

### 规则 5：跨模块引用的 ID 列按需建索引

```python
# 如果有 "按 knowledge_id 查询 chunk" 的场景 → 建索引
knowledge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)

# 如果只是存储关联，不存在按此列查询的场景 → 不建索引
model_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
```

### 规则 6：用 Index 定义复合索引，不在单列重复建

```python
# ❌ 错误：两个单列索引，查询只能用一个
knowledge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

# ✅ 正确：一个复合索引覆盖两种查询
knowledge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
status: Mapped[str] = mapped_column(String(32), nullable=False)
__table_args__ = (
    Index("idx_knowledge_status", "knowledge_id", "status"),
)
```

### 规则 7：多对多关联表两个方向都要索引

关联表按 A_id 查和按 B_id 查都是高频操作，只建一个方向，另一个方向全表扫描。

```python
class AgentToolBinding(Base):
    __tablename__ = "agent_tool_bindings"

    agent_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("agent_configs.id"), nullable=False)
    tool_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tools.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("agent_id", "tool_id"),        # 主键覆盖 agent_id → tools 方向
        Index("idx_tool_agent", "tool_id"),                  # 反向：按 tool_id 查 agents
    )
```

### 规则 8：唯一约束用 UNIQUE INDEX，不只在代码层校验

并发场景下代码校验有竞态问题，数据库约束是最后防线。

```python
# ✅ 正确 — 数据库层面保证唯一
__table_args__ = (
    UniqueConstraint("name", "owner_id", name="uq_app_name_owner"),
)

# ❌ 错误 — 只在 service.py 中 if exists 检查，并发时会插入重复数据
```

### 规则 9：禁止在大文本字段建索引

`content`、`prompt`、`description` 等 TEXT 字段不能建索引。需要全文搜索的场景后续引入 ES。

```python
# ❌ 禁止
Index("idx_content", "content")  # TEXT 字段不能建 B-Tree 索引

# 如果需要搜索 → 方案：
# 1. 短字符串（如 name）用普通索引 + LIKE 'prefix%'（只能前缀匹配）
# 2. 全文搜索 → V2 引入 Elasticsearch
```

---

## 大表预判与应对策略

Hify 中会持续增长的数据表：

| 表 | 增长速度（50 人/天） | 一年预估 | 最大表？ | 应对策略 |
|---|---|---|---|---|
| messages | 每次对话 2-N 条，~5000 行/天 | ~180 万行 | 是 | 索引覆盖 + 游标分页 + 预留归档 |
| message_chunk_refs | 每条 AI 消息 1-N 条，~10000 行/天 | ~360 万行 | 是 | 索引覆盖 + 游标分页 |
| chunks | 导入时批量，不持续增长 | 取决于文档量 | 可能 | 向量在 ChromaDB，MySQL 只存元数据 |
| workflow_executions | ~500 行/天 | ~18 万行 | 否 | 无需特殊处理 |
| tool_calls | ~1000 行/天（Agent 模式） | ~36 万行 | 否 | 无需特殊处理 |

**messages 和 message_chunk_refs 是仅有的两张大表**，一期建好索引够用半年。

### 策略 1：索引覆盖热查询

```python
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    model_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    deleted: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        # 热查询：WHERE conversation_id = ? AND deleted = 0 ORDER BY created_at
        # 等值列在前（conversation_id, deleted），排序列在后（created_at）
        Index("idx_message_conv_created", "conversation_id", "deleted", "created_at"),
    )
```

### 策略 2：游标分页，禁止 OFFSET 深分页

```sql
-- ❌ 禁止：OFFSET 深分页，百万行时极慢
SELECT * FROM message ORDER BY id DESC LIMIT 20 OFFSET 100000;

-- ✅ 正确：游标分页，O(1) 不随页数增加变慢
SELECT * FROM message
WHERE conversation_id = ? AND id < #{last_id} AND deleted = 0
ORDER BY id DESC
LIMIT 20;
```

```python
# service.py — 游标分页实现
async def list_messages(self, conversation_id: int, after: int | None, limit: int = 50):
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.deleted == 0)
    )
    if after:
        query = query.where(Message.id < after)
    query = query.order_by(Message.id.desc()).limit(limit)
    return (await self.db.execute(query)).scalars().all()

# schemas.py — 请求
class MessageListRequest(BaseModel):
    conversation_id: int
    after: int | None = Field(default=None, description="上一页最后一条消息的 id")
    limit: int = Field(default=50, le=200)
```

### 策略 3：COUNT 查询单独处理，列表页只在第一页返回 total

```python
# 列表页分页模式：
# - 第一页（after is None）：查 total + 数据，返回 {"items": [...], "total": 1234, "has_more": true}
# - 后续页（after 有值）：只查数据，不查 total，返回 {"items": [...], "has_more": true/false}
async def list_messages_page(self, conversation_id: int, after: int | None, limit: int = 50):
    query = select(Message).where(
        Message.conversation_id == conversation_id, Message.deleted == 0
    )
    if after:
        query = query.where(Message.id < after)

    items = (await self.db.execute(
        query.order_by(Message.id.desc()).limit(limit + 1)
    )).scalars().all()

    has_more = len(items) > limit
    items = items[:limit]

    total = None
    if after is None:
        # 仅第一页查 total
        total = await self.db.scalar(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id, Message.deleted == 0
            )
        )
    return {"items": items, "total": total, "has_more": has_more}
```

### 策略 4：分区（V2 阶段，一期不需要）

当 messages 超过 500 万行时（约 3 年），按月分区：

```sql
-- V2 阶段执行，一期不建分区
ALTER TABLE messages PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p202601 VALUES LESS THAN (TO_DAYS('2026-02-01')),
    PARTITION p202602 VALUES LESS THAN (TO_DAYS('2026-03-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

---

## JSON 字段使用规范

Hify 的 JSON 字段使用场景：

| 表 | JSON 字段 | 存什么 | 查询方式 |
|---|---|---|---|
| model_providers | api_keys | `["sk-xxx", "sk-yyy"]` | 整体读取，不按元素查 |
| models | model_params | `{"temperature": 0.7, "max_tokens": 4096}` | 整体读取 |
| apps | app_config | `{"knowledge_ids": [...], "prompt": "..."}` | 整体读取 |
| workflow_nodes | node_config | `{"model_id": "...", "template": "..."}` | 整体读取 |

**规则**：
- JSON 列只存配置型数据，整体读写
- 如果未来出现需要 `WHERE json_col->>'$.field' = ?` 的查询 → 将该字段拆成独立列
- 不在 JSON 列上建索引（一期无此需求）

---

## 建表检查清单

AI 新建一张表时，逐项检查：

```
── 命名 ──
□ 表名全小写 + 下划线，复数名词（apps / conversations / message_chunk_refs）
□ 列名全小写 + 下划线，有业务含义（created_at / owner_id），不用驼峰或缩写
□ 索引名 idx_{表名}_{列名}，唯一索引名 uq_{表名}_{列名}

── 全局配置 ──
□ 字符集 utf8mb4 + 排序规则 utf8mb4_unicode_ci + 引擎 InnoDB

── 字段 ──
□ id 列是 BigInteger + autoincrement，不用 UUID
□ 所有列 nullable=False，空值用 default="" 或 default=0
□ 业务表有 deleted 字段（SmallInteger, nullable=False, default=0）
□ 有 created_at（DateTime, server_default=func.now(), nullable=False）
□ 需要更新追踪的表有 updated_at
□ 金额和 Token 用量列用 BigInteger，存最小精度
□ status/type 字段用 String(32)，不用 MySQL ENUM
□ 单表字段数 ≤ 30

── 索引 ──
□ 同模块 ForeignKey 列有 index=True
□ 跨模块引用列无 ForeignKey，用 BigInteger + default=0
□ 复合索引含 deleted 字段（几乎所有查询都带 deleted = 0）
□ 复合索引等值列在前、范围/排序列在后
□ 多对多关联表两个方向都有索引
□ 唯一约束用 UniqueConstraint，不只在代码层校验
□ 禁止在 TEXT 字段建索引
□ 复合索引不超过 3 列，总索引数 ≤ 5（含主键）

── 其他 ──
□ 表有 comment 说明用途
□ 名称 256、描述 1024（default=""）、正文 Text
□ JSON 列 default=dict，只存配置型数据
```
