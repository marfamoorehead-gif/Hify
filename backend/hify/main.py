from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from hify.core.config import settings
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


# K8s 探针用（不走版本前缀）
@app.get("/health")
async def health():
    return Result.ok(data={"status": "healthy"})


# 统一 API 路由
api_router = APIRouter(prefix=settings.api_v1_prefix)


@api_router.get("/health")
async def api_health():
    return Result.ok(data={"status": "healthy"})


api_router.include_router(model_provider_router, prefix="/model-providers", tags=["Model Provider"])
api_router.include_router(agent_router, prefix="/agents", tags=["Agent"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(workflow_router, prefix="/workflows", tags=["Workflow"])
api_router.include_router(tool_router, prefix="/tools", tags=["Tool"])

app.include_router(api_router)
