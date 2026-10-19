# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""健康检查路由。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """存活探针。"""
    return {"status": "ok"}
