# 本地开发环境配置

> 详细内容请参考 CLAUDE.md 第 1.5 节

## 环境依赖

| 工具 | 最低版本 | 说明 |
|---|---|---|
| Python | 3.11+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| Docker | 24+ | 运行 MySQL、Redis |
| git | 2.x | 版本控制 |

## 首次启动步骤

```bash
# 1. 克隆仓库
git clone <repo-url> && cd hify

# 2. 启动基础设施（MySQL + Redis）
docker compose up -d

# 3. 后端设置
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # 编辑 .env 填入实际配置
alembic upgrade head        # 执行数据库迁移
uvicorn hify.main:app --reload --port 8000

# 4. 前端设置（新终端）
cd frontend
npm install
cp .env.example .env
npm run dev                 # Vite 开发服务器，默认 http://localhost:5173
```

启动完成后：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs（Swagger UI）

## docker-compose.yml（本地开发用）

```yaml
# docker-compose.yml — 仅用于本地开发启动 MySQL 和 Redis
version: "3.8"
services:
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: hify_dev
      MYSQL_DATABASE: hify
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
    volumes:
      - mysql-data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  mysql-data:
  redis-data:
```

## 后端 .env.example

```bash
# backend/.env.example — 复制为 .env 后修改

# MySQL
MYSQL_DSN=mysql+aiomysql://root:hify_dev@localhost:3306/hify

# Redis
REDIS_URL=redis://localhost:6379/0

# ChromaDB 向量数据目录
CHROMA_PERSIST_DIR=./data/chroma

# JWT 密钥（开发环境用固定值，生产环境随机生成）
JWT_SECRET=dev-secret-change-in-production

# LLM API Keys（按需填写）
OPENAI_API_KEY=
DEEPSEEK_API_KEY=

# 日志级别
LOG_LEVEL=DEBUG

# 服务端口
PORT=8000
```

## 前端 .env.example

```bash
# frontend/.env.example — 复制为 .env 后修改

# API 基础路径（空字符串 = 同源请求，Vite devServer 代理到后端）
VITE_API_BASE_URL=
```

## Vite 开发代理配置

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

## 常用开发命令

```bash
# 后端
cd backend
uvicorn hify.main:app --reload          # 启动开发服务器
alembic revision --autogenerate -m "xxx" # 生成迁移
alembic upgrade head                     # 执行迁移
pytest                                   # 运行测试
pytest --cov=hify                        # 带覆盖率

# 前端
cd frontend
npm run dev                              # 开发服务器
npm run build                            # 生产构建
npm run preview                          # 预览构建产物
npm run lint                             # ESLint
npm run type-check                       # TypeScript 类型检查

# 基础设施
docker compose up -d                     # 启动 MySQL + Redis
docker compose down                      # 停止
docker compose logs -f mysql             # 查看日志
```
