"""全局常量与枚举定义。"""

from enum import Enum


class SecurityLevel(str, Enum):
    """数据密级。"""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class UserRole(str, Enum):
    """RBAC 角色。"""

    ADMIN = "admin"
    AUDIT_MANAGER = "audit_manager"
    AUDITOR = "auditor"
    READONLY = "readonly"


class IntentType(str, Enum):
    """意图类型。"""

    KNOWLEDGE_QUERY = "knowledge_query"
    TOOL_OPERATION = "tool_operation"
    DIRECT_QA = "direct_qa"
    UNKNOWN = "unknown"


class Route(str, Enum):
    """路由目标。"""

    RAG = "rag"
    TOOL = "tool"
    DIRECT = "direct"


class ExecutionStatus(str, Enum):
    """执行状态。"""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class MemoryType(str, Enum):
    """长期记忆类型。"""

    USER_PROFILE = "user_profile"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    TASK_HISTORY = "task_history"
