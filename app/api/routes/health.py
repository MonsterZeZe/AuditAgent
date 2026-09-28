"""健康检查路由。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """存活探针。"""
    return {"status": "ok"}
