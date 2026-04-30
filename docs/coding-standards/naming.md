# 命名规范

> 详细内容请参考 CLAUDE.md 第 2.4.1 节

## 模块/包名

全小写 + 下划线，不超 3 个单词

```
✅ model_provider / knowledge / chat
❌ ModelProvider / model-provider / llmClient
```

## 类名

PascalCase，异常类以 Error 结尾

```python
✅ class ChatService / class LLMRateLimitError / class AppCreateRequest
❌ class chat_service / class LLMRateLimit / class app_create_request
```

## 函数/方法/变量

snake_case，布尔返回用 is_/has_/can_ 前缀

```python
✅ async def create_conversation() / def is_active() / def has_permission()
❌ async def createConversation() / def check_active() / def get_permission()
```

## 常量

全大写 + 下划线，集中在模块顶部或 core/config.py

```python
✅ MAX_RETRY_COUNT = 3 / DEFAULT_PAGE_SIZE = 20 / KEEPALIVE_INTERVAL = 15
❌ maxRetryCount = 3 / DefaultPageSize = 20
```

## 禁止事项

禁止单字母变量（循环计数器 i/j/k 除外）和 Python 关键字/内置名

```python
✅ user_id / provider_name / chunk_index
❌ id / list / dict / str / input / l / O / I
```
