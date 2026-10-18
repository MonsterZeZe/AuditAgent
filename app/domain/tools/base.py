"""审计工具抽象接口。

工具遵循统一插件规范，新增审计工具（合规校验、财务计算、数据比对等）
仅需实现 Tool 接口并注册，无需修改核心 Agent 代码。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ToolResult:
    """工具执行结果（运行时对象）。"""

    status: Literal["success", "failed"]
    output: dict = field(default_factory=dict)
    error: str = ""


class Tool(ABC):
    """审计工具插件接口。"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """执行工具，返回结构化结果。"""
