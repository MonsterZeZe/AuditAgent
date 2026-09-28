"""工具注册中心。

工具遵循统一插件规范，注册后即可被 Agent 调用，无需修改核心代码。
"""

from typing import Optional

from app.domain.tools.base import Tool, ToolResult


class ToolRegistry:
    """工具注册、发现与调用。"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具。"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """按名称查找工具。"""
        return self._tools.get(name)

    def list_names(self) -> list[str]:
        """列出所有已注册工具名。"""
        return list(self._tools.keys())

    def execute(self, name: str, params: dict) -> ToolResult:
        """执行工具，异常时返回失败结果而非抛出。"""
        tool = self.get(name)
        if tool is None:
            return ToolResult(status="failed", error=f"工具不存在: {name}")
        try:
            return tool.run(params)
        except Exception as exc:  # noqa: BLE001 - 工具异常需隔离，不阻断主流程
            return ToolResult(status="failed", error=str(exc))
