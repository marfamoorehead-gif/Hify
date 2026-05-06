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
PID_DIR="$SCRIPT_DIR/.pids"
GRACEFUL_TIMEOUT=10

# ── 停止单个进程 ─────────────────────────────────────
# 用法: stop_process <名称> <PID 文件>
stop_process() {
    local name="$1"
    local pid_file="$2"

    if [ ! -f "$pid_file" ]; then
        warn "$name: PID 文件不存在 ($pid_file)，跳过"
        return 0
    fi

    local pid
    pid="$(cat "$pid_file")"

    if [ -z "$pid" ]; then
        warn "$name: PID 文件为空，清理文件"
        rm -f "$pid_file"
        return 0
    fi

    if ! kill -0 "$pid" 2>/dev/null; then
        info "$name: 进程已不在运行 (PID: $pid)，清理 PID 文件"
        rm -f "$pid_file"
        return 0
    fi

    info "$name: 发送 SIGTERM (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程退出
    local waited=0
    while [ "$waited" -lt "$GRACEFUL_TIMEOUT" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            info "$name: 已停止 (等待 ${waited}s)"
            rm -f "$pid_file"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    # 超时，强制终止
    warn "$name: 等待超时 (${GRACEFUL_TIMEOUT}s)，发送 SIGKILL..."
    kill -KILL "$pid" 2>/dev/null || true
    sleep 1

    if kill -0 "$pid" 2>/dev/null; then
        die "$name: SIGKILL 后进程仍在运行 (PID: $pid)，请手动处理"
    fi

    info "$name: 已强制停止"
    rm -f "$pid_file"
}

# ── 执行 ──────────────────────────────────────────────
if [ ! -d "$PID_DIR" ]; then
    die "PID 目录不存在 ($PID_DIR)，服务可能未启动"
fi

stop_process "后端" "$PID_DIR/backend.pid"
stop_process "前端" "$PID_DIR/frontend.pid"

info "所有服务已停止"
