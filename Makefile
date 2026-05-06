.PHONY: start stop restart build clean package help

VERSION  := 0.1.0
NAME     := hify
DIST_DIR := dist
FRONTEND_DIR := frontend
BACKEND_DIR  := backend

# ── 开发 ──────────────────────────────────────────────

start: ## 启动前后端开发服务
	@bash start.sh

stop: ## 停止前后端开发服务
	@bash stop.sh

restart: stop start ## 重启前后端开发服务

# ── 构建 ──────────────────────────────────────────────

build: build-frontend ## 构建前后端产物

build-frontend: ## 构建前端静态资源
	cd $(FRONTEND_DIR) && npm install --silent && npm run build

# ── 清理 ──────────────────────────────────────────────

clean: ## 清理构建产物和 PID 文件
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(BACKEND_DIR)/build $(BACKEND_DIR)/dist $(BACKEND_DIR)/*.egg-info
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pids
	rm -rf $(DIST_DIR)

# ── 打包 ──────────────────────────────────────────────

package: build ## 打包成 tar.gz 分发包
	@rm -rf $(DIST_DIR)
	@mkdir -p $(DIST_DIR)/$(NAME)-$(VERSION)
	@cp -r $(BACKEND_DIR) $(DIST_DIR)/$(NAME)-$(VERSION)/backend
	@cp -r $(FRONTEND_DIR)/dist $(DIST_DIR)/$(NAME)-$(VERSION)/frontend/dist
	@cp start.sh stop.sh Makefile $(DIST_DIR)/$(NAME)-$(VERSION)/
	@cd $(DIST_DIR) && tar czf $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	@rm -rf $(DIST_DIR)/$(NAME)-$(VERSION)
	@echo "打包完成: $(DIST_DIR)/$(NAME)-$(VERSION).tar.gz"

# ── 帮助 ──────────────────────────────────────────────

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
