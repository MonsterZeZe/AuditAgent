"""合规校验工具（示例审计工具）。

校验文本是否包含审计合规所需的关键要素，作为工具插件化接入的示例。
"""

from app.domain.tools.base import Tool, ToolResult

_COMPLIANCE_KEYWORDS = ("准则", "规定", "依据", "条款", "法规")


class ComplianceCheckTool(Tool):
    """合规校验工具。"""

    name = "compliance_check"
    description = "校验文本是否符合审计合规要求，检查是否包含关键合规要素"

    def run(self, params: dict) -> ToolResult:
        text = str(params.get("text", ""))
        if not text:
            return ToolResult(status="failed", error="缺少参数 text")
        missing = [k for k in _COMPLIANCE_KEYWORDS if k not in text]
        return ToolResult(
            status="success",
            output={
                "compliant": not missing,
                "missing_keywords": missing,
            },
        )
