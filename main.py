"""应用入口。

启动 FastAPI 服务，初始化日志配置并注册路由。
"""

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.core.logging.logger import setup_logging


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    setup_logging()
    app = FastAPI(title="audit-agent", version="0.1.0")
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
