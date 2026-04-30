# 日志规范

> 详细内容请参考 CLAUDE.md 第 2.4.3 节

## 核心规则

1. **用 structlog 或标准库 logging**，JSON 格式输出，每条日志必须含 trace_id
2. **日志级别严格区分**（ERROR、WARNING、INFO、DEBUG）
3. **日志不用 f-string 拼消息**，用结构化字段
4. **禁止在日志中打印敏感信息**
5. **ERROR 日志必须含上下文字段**（谁、什么操作、什么错误、影响范围）

## 日志级别

| 级别 | 用途 | 示例 |
|---|---|---|
| ERROR | 需要人工介入的故障 | 数据库连接断开、LLM 全部 Provider 不可用 |
| WARNING | 异常但可自动恢复 | 单个 Provider 429 限流（已 Fallback）、请求超时后重试成功 |
| INFO | 关键业务节点 | 创建应用、发起对话、文档导入完成、工作流执行完成 |
| DEBUG | 开发调试用 | LLM 请求/响应内容、SQL 查询、中间变量 |

## 代码示例

```python
# 每条日志自动注入 trace_id（通过中间件/Filter）
import logging
logger = logging.getLogger(__name__)

# ✅ 正确：结构化字段
logger.info("conversation created", conversation_id=conv.id, user_id=user.id)

# ❌ 错误：f-string 拼接
logger.info(f"conversation created: conv={conv.id}, user={user.id}")

# ✅ 正确：不泄露敏感信息
logger.info("provider configured", provider_id=p.id, name=p.name)

# ❌ 错误：泄露 API Key
logger.info("provider configured", api_key=p.api_keys[0])

# ✅ 正确：ERROR 含完整上下文
logger.error(
    "llm request failed after all retries",
    model_id=model.id, provider=provider.name,
    error=str(e), fallback_used=bool(model.fallback_model_id),
    user_id=user_id, conversation_id=conv_id,
)

# ❌ 错误：无上下文
logger.error("request failed")
```
