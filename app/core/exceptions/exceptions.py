# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""统一异常定义与错误码。

所有业务异常继承 AppException，携带标准错误码，便于全局异常处理层
返回标准化错误信息与全链路追踪。
"""

from enum import Enum


class ErrorCode(str, Enum):
    """全局错误码。"""

    UNKNOWN = "E0000"

    # 接入层
    AUTH_FAILED = "E1001"
    RATE_LIMITED = "E1002"
    INVALID_PARAM = "E1003"
    PROMPT_INJECTION = "E1004"

    # 模型
    MODEL_UNAVAILABLE = "E2001"
    MODEL_TIMEOUT = "E2002"

    # 检索
    RETRIEVAL_FAILED = "E3001"

    # 工具
    TOOL_NOT_FOUND = "E4001"
    TOOL_FAILED = "E4002"

    # 校验
    VALIDATION_FAILED = "E5001"

    # 会话
    SESSION_NOT_FOUND = "E6001"


class AppException(Exception):
    """应用异常基类。"""

    def __init__(
        self,
        code: ErrorCode,
        message: str = "",
        *,
        detail: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message or code.value
        self.detail = detail or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """序列化为标准错误响应结构。"""
        return {
            "code": self.code.value,
            "message": self.message,
            "detail": self.detail,
        }


class AuthException(AppException):
    """鉴权失败。"""

    def __init__(self, message: str = "") -> None:
        super().__init__(ErrorCode.AUTH_FAILED, message)


class ModelException(AppException):
    """模型调用异常。"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.MODEL_UNAVAILABLE,
        message: str = "",
    ) -> None:
        super().__init__(code, message)


class RetrievalException(AppException):
    """检索异常。"""

    def __init__(self, message: str = "") -> None:
        super().__init__(ErrorCode.RETRIEVAL_FAILED, message)


class ToolException(AppException):
    """工具调用异常。"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.TOOL_FAILED,
        message: str = "",
    ) -> None:
        super().__init__(code, message)


class ValidationException(AppException):
    """结果校验异常。"""

    def __init__(self, message: str = "") -> None:
        super().__init__(ErrorCode.VALIDATION_FAILED, message)
