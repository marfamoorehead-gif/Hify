# 异常处理规范

> 详细内容请参考 CLAUDE.md 第 2.4.2 节

## 核心规则

1. **禁止裸 except**，必须指定异常类型
2. **禁止吞异常**（except 后 pass 或只有 ...）
3. **用 raise ... from e 保留异常链**，不要丢原始堆栈
4. **不在 service 层抛 HTTPException**（唯一例外：core/security.py 认证鉴权）
5. **try 块只包真正可能抛异常的代码**，不要包整段逻辑

## 代码示例

```python
# ✅ 正确：指定异常类型
except httpx.TimeoutError:
    ...

# ❌ 错误：裸 except
except:
    ...

# ✅ 正确：不吞异常
except httpx.TimeoutError:
    logger.warning("LLM timeout", provider=provider_name, model=model_name)
    raise LLMTimeoutError(...) from e

# ❌ 错误：吞掉异常
except httpx.TimeoutError:
    pass

# ✅ 正确：保留异常链
except sqlalchemy.IntegrityError as e:
    raise AppAlreadyExistsError(...) from e

# ❌ 错误：原始堆栈断了
except sqlalchemy.IntegrityError as e:
    raise AppAlreadyExistsError(...)

# ✅ 正确：只包可能抛异常的代码
result = await llm_client.chat(messages)
try:
    parsed = json.loads(result)
except json.JSONDecodeError:
    logger.error("invalid llm response", raw=result)
    raise LLMParseError(...)

# ❌ 错误：try 块太大
try:
    result = await llm_client.chat(messages)
    parsed = json.loads(result)
    chunks = self.retriever.search(parsed["query"])
except Exception:
    pass
```
