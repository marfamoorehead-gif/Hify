import logging
import uuid
from contextvars import ContextVar

import structlog

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def setup_logging(log_level: str = "DEBUG") -> None:
    """配置 structlog，JSON 格式输出，自动注入 trace_id。"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _inject_trace_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level),
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _inject_trace_id(logger, method_name, event_dict):
    """将 trace_id 注入每条日志。"""
    trace_id = trace_id_var.get("")
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def generate_trace_id() -> str:
    """生成新的 trace_id。"""
    trace_id = uuid.uuid4().hex[:16]
    trace_id_var.set(trace_id)
    return trace_id


def get_logger(name: str):
    """获取带名称的 structlog logger。"""
    return structlog.get_logger(name)
