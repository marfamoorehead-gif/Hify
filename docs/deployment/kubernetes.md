# Kubernetes 部署配置

> 详细内容请参考 CLAUDE.md 第 1.6 节

## 组件职责

| 组件 | 形态 | 副本 | 职责 | 资源 |
|---|---|---|---|---|
| Ingress Controller | 集群已有 | - | TLS 终结、域名路由、SSE 超时配置 | - |
| hify-web | Deployment | 1 | React 静态资源、前端路由、`/api/*` 反代 | 0.2 CPU / 256Mi |
| hify-api | Deployment | 1 | FastAPI 后端 + ChromaDB 进程内 | 1 CPU / 2Gi |
| MySQL | StatefulSet 或云托管 | 1 | 关系数据存储 | 1 CPU / 2Gi |
| Redis | StatefulSet 或云托管 | 1 | 缓存 + SSE 连接注册 | 0.5 CPU / 512Mi |

**持久化卷**：`chroma-data` PVC（10Gi）挂载到 hify-api，`mysql-data` PVC（20Gi）挂载到 MySQL。

---

## Ingress 配置（SSE 支持）

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hify
  annotations:
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
    - hosts: [hify.company.com]
      secretName: hify-tls
  rules:
    - host: hify.company.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hify-web
                port: { number: 80 }
```

---

## hify-api Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hify-api
spec:
  replicas: 1
  strategy:
    type: Recreate  # ChromaDB PersistentClient 用文件锁，RollingUpdate 会导致新旧 Pod 竞争同一 PVC 的文件锁，新 Pod crash-loop。Recreate 先杀旧 Pod 释放锁，再启新 Pod
  template:
    spec:
      terminationGracePeriodSeconds: 310  # 大于 SSE proxy_read_timeout 300s
      containers:
        - name: hify-api
          image: hify-api:latest
          ports: [{ containerPort: 8000 }]
          resources:
            requests: { cpu: "1", memory: "2Gi" }
            limits: { cpu: "2", memory: "4Gi" }
          env:
            - name: MYSQL_DSN
              valueFrom:
                secretKeyRef: { name: hify-secrets, key: mysql-dsn }
            - name: REDIS_URL
              valueFrom:
                secretKeyRef: { name: hify-secrets, key: redis-url }
            - name: LLM_API_KEYS
              valueFrom:
                secretKeyRef: { name: hify-secrets, key: llm-api-keys }
          volumeMounts:
            - name: chroma-data
              mountPath: /app/data/chroma
          readinessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 30
            periodSeconds: 30
      volumes:
        - name: chroma-data
          persistentVolumeClaim:
            claimName: chroma-data
```

### Recreate 策略说明

**hify-api 用 1 副本的原因**：ChromaDB PersistentClient 是文件锁模式，多副本不能共享 PVC 写入。V2 迁移到 ChromaDB Server 或 Milvus 后再扩副本。

**PodDisruptionBudget**：Recreate 策略下不需要 PDB。PDB 的 `minAvailable: 1` 会阻止 Recreate 删除旧 Pod（因为要求至少 1 个可用），导致部署卡死。因此 hify-api 不配置 PDB。部署时有短暂不可用窗口（K8s 原生行为），一期可接受。

---

## hify-web Nginx 配置

容器内 `nginx.conf`：

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # React SPA — 所有非文件请求回退到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反代到后端
    location /api/ {
        proxy_pass http://hify-api:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Request-Id $request_id;

        # SSE 关键配置
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_set_header Connection "";
    }

    # 静态资源长缓存（React 构建产物带 hash）
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 运维预期

- **瓶颈不在 QPS**：50 人峰值 15-25 QPS + 25 个 SSE 长连接，核心瓶颈是 LLM API 延迟（5-30 秒）和 Provider 并发限制
- **SSE 保障**：Ingress + hify-web 两层均关闭 proxy_buffering、proxy_read_timeout 300s，Python 层 15 秒 keepalive 注释帧
- **LLM 容错**：429 限流排队重试、多 Key 轮询、Fallback 降级模型（详见后端文档）
- **监控**：/health 健康检查（readinessProbe + livenessProbe）+ /metrics Prometheus 指标 + 结构化 JSON 日志（含 trace_id）

---

## 监控指标与告警规则

`/metrics` 端点暴露 Prometheus 格式指标，由 `shared/metrics.py` 统一注册，各模块在业务代码中埋点采集。

### 指标定义

```python
# shared/metrics.py
from prometheus_client import Histogram, Gauge, Counter

# ── 瓶颈 #3：ChromaDB 检索性能 ──
chroma_retrieval_seconds = Histogram(
    "hify_chroma_retrieval_seconds",
    "ChromaDB 向量检索耗时",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
chroma_collection_chunks = Gauge(
    "hify_chroma_collection_chunks",
    "每个知识库的 chunk 总数",
    ["knowledge_id"],
)
chroma_total_chunks = Gauge(
    "hify_chroma_total_chunks",
    "所有知识库的 chunk 总数",
)

# ── 瓶颈 #4：进程内存 ──
process_memory_rss_bytes = Gauge(
    "hify_process_memory_rss_bytes",
    "hify-api 进程 RSS 内存（字节）",
)
```

### 埋点示例

```python
# knowledge/retriever.py — 检索埋点
import psutil
from shared.metrics import chroma_retrieval_seconds, chroma_collection_chunks, process_memory_rss_bytes

class Retriever:
    async def vector_search(self, query_embedding, knowledge_id, top_k):
        with chroma_retrieval_seconds.time():
            results = await asyncio.to_thread(collection.query, ...)
        # 采集后更新内存指标（检索触发加载 collection 到内存）
        process_memory_rss_bytes.set(psutil.Process().memory_info().rss)
        return results
```

### 告警规则

| 指标 | 告警条件 | 级别 | 含义 |
|---|---|---|---|
| `hify_chroma_retrieval_seconds` | p95 > 500ms 持续 5 分钟 | WARN | 检索变慢，知识库可能需要拆分或迁移 |
| `hify_chroma_retrieval_seconds` | p95 > 2s 持续 5 分钟 | CRITICAL | 检索严重影响对话体验 |
| `hify_chroma_total_chunks` | > 25000 | WARN | 接近一期容量上限，规划 V2 迁移 |
| `hify_process_memory_rss_bytes` | > 3Gi | WARN | 内存压力，检查知识库规模 |
| `hify_process_memory_rss_bytes` | > 3.5Gi | CRITICAL | 即将 OOM，需重启或扩容 |

**一期不需要处理的判断依据**：50 人 × 平均 5 篇文档/人 = ~250 篇文档 ≈ ~12500 chunks，远低于 25000 告警阈值。

---

## 数据备份

- **MySQL**：每日 CronJob mysqldump → 对象存储
- **ChromaDB**：PVC 每日 tar 打包 → 对象存储
- **Redis**：纯缓存无需备份

---

## 总资源

~3 CPU / ~5Gi 内存 / ~30Gi 磁盘，单节点即可运行。
