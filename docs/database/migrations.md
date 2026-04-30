# 数据库迁移规范（Alembic）

> 详细内容请参考 CLAUDE.md 第 3.3.4 节

使用 Alembic 管理 MySQL schema 版本控制。所有表结构变更必须通过迁移脚本执行，禁止手动 DDL。

## 目录结构

```
hify/
├── alembic/
│   ├── env.py                  # Alembic 环境配置（指向 core/database.py）
│   ├── script.py.mako          # 迁移脚本模板
│   └── versions/               # 迁移文件（按时间顺序）
│       ├── 001_create_users.py
│       ├── 002_create_apps.py
│       └── 003_add_app_config.py
├── alembic.ini                 # Alembic 主配置
└── ...
```

## alembic.ini 关键配置

```ini
[alembic]
script_location = alembic
sqlalchemy.url = mysql+aiomysql://root:password@localhost:3306/hify

[loggers]
keys = root,sqlalchemy,alembic
```

## env.py 配置要点

```python
# alembic/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# 导入所有 ORM 模型，确保 Base.metadata 包含所有表
from hify.core.database import Base
from hify.model_provider import models as provider_models  # noqa
from hify.chat import models as chat_models                # noqa
from hify.knowledge import models as knowledge_models      # noqa
from hify.workflow import models as workflow_models         # noqa
from hify.agent import models as agent_models               # noqa
from hify.tool import models as tool_models                 # noqa

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata
```

## 迁移文件命名约定

```
{序号}_{简短描述}.py

示例：
001_create_users.py
002_create_model_providers.py
003_create_apps.py
004_create_conversations_and_messages.py
005_create_knowledge_tables.py
006_create_workflow_tables.py
007_create_agent_and_tool_tables.py
008_create_message_chunk_refs.py
```

**规则**：
- 序号 3 位数字，从 001 开始递增
- 描述用下划线分隔，简短说明本次迁移内容
- 一个迁移文件只做一件事（加表、加列、改列、加索引），不要混合多种操作

## 迁移操作规范

```python
# ✅ 正确：显式写 upgrade 和 downgrade
def upgrade() -> None:
    op.create_table(
        "apps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
        comment="应用表",
    )
    op.create_index("idx_apps_owner", "apps", ["owner_id"])

def downgrade() -> None:
    op.drop_index("idx_apps_owner", table_name="apps")
    op.drop_table("apps")

# ❌ 错误：只写 upgrade 不写 downgrade
# ❌ 错误：用 autogenerate 后不加审查直接提交
```

## 禁止事项

- 禁止 `op.alter_column` 修改列类型或删除列时不提供 `downgrade`（生产环境可能需要回滚）
- 禁止在迁移文件中 import 业务代码（service、schema），只依赖 `alembic.op` 和 `sqlalchemy`
- 禁止同时修改 ORM 模型和运行迁移（先改模型 → 生成迁移 → 检查 → 运行迁移）

## 工作流

```bash
# 1. 修改 ORM 模型（models.py）
# 2. 生成迁移脚本（自动对比模型与数据库差异）
alembic revision --autogenerate -m "add app config column"

# 3. 检查生成的迁移文件（必须！autogenerate 可能漏掉或多出变更）
git diff alembic/versions/

# 4. 执行迁移
alembic upgrade head

# 5. 回滚（如果出问题）
alembic downgrade -1
```

## CI 检查

CI 流水线中加入迁移一致性检查，确保 ORM 模型与迁移脚本同步：

```bash
# 生成临时迁移文件，如果没有输出说明模型和数据库一致
alembic revision --autogenerate -m "check" --dry-run
# 如果有输出 → 说明有人改了模型没生成迁移，CI 失败
```
