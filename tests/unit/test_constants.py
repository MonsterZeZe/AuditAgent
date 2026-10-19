# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""core.constants 与 core.exceptions 单元测试示例。"""

from app.core.constants.constants import Route, SecurityLevel, UserRole
from app.core.exceptions.exceptions import AppException, ErrorCode


def test_security_level_values() -> None:
    assert SecurityLevel.PUBLIC.value == "public"
    assert SecurityLevel.INTERNAL.value == "internal"
    assert SecurityLevel.SENSITIVE.value == "sensitive"
    assert SecurityLevel.SECRET.value == "secret"


def test_route_values() -> None:
    assert Route.RAG.value == "rag"
    assert Route.TOOL.value == "tool"
    assert Route.DIRECT.value == "direct"


def test_user_role_values() -> None:
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.READONLY.value == "readonly"


def test_app_exception_to_dict() -> None:
    exc = AppException(ErrorCode.AUTH_FAILED, "鉴权失败")
    assert exc.to_dict() == {
        "code": "E1001",
        "message": "鉴权失败",
        "detail": {},
    }
