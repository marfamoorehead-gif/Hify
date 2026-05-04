from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hify.core.events import lifespan
from hify.core.exceptions import register_exception_handlers
from hify.shared.schemas import Result

from hify.model_provider.router import router as model_provider_router
from hify.agent.router import router as agent_router
from hify.chat.router import router as chat_router
from hify.knowledge.router import router as knowledge_router
from hify.workflow.router import router as workflow_router
from hify.tool.router import router as tool_router

app = FastAPI(title="Hify", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
register_exception_handlers(app)


@app.get("/health")
async def health():
    return Result.ok(data={"status": "healthy"})


# 挂载模块路由
app.include_router(model_provider_router, prefix="/api/v1/model-providers")
app.include_router(agent_router, prefix="/api/v1/agents")
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(knowledge_router, prefix="/api/v1/knowledge")
app.include_router(workflow_router, prefix="/api/v1/workflows")
app.include_router(tool_router, prefix="/api/v1/tools")
