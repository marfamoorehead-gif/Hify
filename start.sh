#!/usr/bin/env bash
set -euo pipefail

# ── 颜色 ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 配置 ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_PORT="${BACKEND_PORT:-8080}"
HEALTH_URL="http://localhost:${BACKEND_PORT}/health"
MAX_RETRIES=30
RETRY_INTERVAL=2

# ── PID 文件 ──────────────────────────────────────────
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

cleanup() {
    local pid
    pid="$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        warn "正在停止后端进程 (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
    fi
}
trap cleanup EXIT

# ── 工具检查 ──────────────────────────────────────────
command -v mysql  >/dev/null 2>&1 || die "未找到 mysql 客户端，请先安装 MySQL"
command -v redis-cli >/dev/null 2>/dev/null || die "未找到 redis-cli，请先安装 Redis"

# ── 1. 检查 MySQL ────────────────────────────────────
info "检查 MySQL 连接..."
MYSQL_DSN="$(grep '^MYSQL_DSN=' "$BACKEND_DIR/.env" | head -1 | cut -d= -f2-)"
if [ -z "$MYSQL_DSN" ]; then
    die "未在 backend/.env 中找到 MYSQL_DSN"
fi
# 从 DSN 解析: mysql+aiomysql://user:pass@host:port/dbname
MYSQL_USER="$(echo "$MYSQL_DSN" | sed -E 's|.*://([^:]+):.*|\1|')"
MYSQL_PASS="$(echo "$MYSQL_DSN" | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')"
MYSQL_HOST="$(echo "$MYSQL_DSN" | sed -E 's|.*@([^:]+):.*|\1|')"
MYSQL_PORT="$(echo "$MYSQL_DSN" | sed -E 's|.*@[^:]+:([0-9]+).*|\1|')"
if ! mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -h "$MYSQL_HOST" -P "$MYSQL_PORT" -e "SELECT 1" &>/dev/null; then
    die "MySQL 连接失败，请确认 MySQL 已启动且 backend/.env 中 MYSQL_DSN 配置正确"
fi
info "MySQL 连接正常"

# ── 2. 检查 Redis ────────────────────────────────────
info "检查 Redis 连接..."
if ! redis-cli -u redis://localhost:6379/0 ping &>/dev/null; then
    die "Redis 连接失败，请确认 Redis 已启动"
fi
info "Redis 连接正常"

# ── 3. 启动后端 ──────────────────────────────────────
info "安装后端依赖..."
cd "$BACKEND_DIR"
pip install -q -r requirements.txt 2>/dev/null || die "后端依赖安装失败"

info "启动后端服务 (端口: $BACKEND_PORT)..."
uvicorn hify.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
echo $! > "$BACKEND_PID_FILE"
BACKEND_PID=$(cat "$BACKEND_PID_FILE")

# ── 4. 轮询健康检查 ─────────────────────────────────
info "等待后端就绪 (最多 $((MAX_RETRIES * RETRY_INTERVAL)) 秒)..."
ok=false
for i in $(seq 1 "$MAX_RETRIES"); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        ok=true
        break
    fi
    sleep "$RETRY_INTERVAL"
done

if [ "$ok" = false ]; then
    die "后端健康检查失败，已等待 $((MAX_RETRIES * RETRY_INTERVAL)) 秒。请检查日志排查原因"
fi
info "后端已就绪 (PID: $BACKEND_PID)"

# ── 5. 启动前端 ──────────────────────────────────────
info "安装前端依赖..."
cd "$FRONTEND_DIR"
npm install --silent 2>/dev/null || die "前端依赖安装失败"

info "启动前端开发服务器..."
npm run dev &
echo $! > "$FRONTEND_PID_FILE"
wait
