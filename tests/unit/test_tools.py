"""ToolRegistry 与合规校验工具单元测试。"""

from app.domain.tools.compliance import ComplianceCheckTool
from app.domain.tools.registry import ToolRegistry


def test_register_and_list() -> None:
    registry = ToolRegistry()
    registry.register(ComplianceCheckTool())
    assert registry.list_names() == ["compliance_check"]


def test_execute_compliance_missing() -> None:
    registry = ToolRegistry()
    registry.register(ComplianceCheckTool())
    result = registry.execute("compliance_check", {"text": "依据会计准则规定"})
    assert result.status == "success"
    assert result.output["compliant"] is False


def test_execute_unknown_tool() -> None:
    registry = ToolRegistry()
    result = registry.execute("not_exist", {})
    assert result.status == "failed"
    assert "工具不存在" in result.error


def test_compliance_compliant() -> None:
    tool = ComplianceCheckTool()
    result = tool.run({"text": "依据会计准则和法规规定及相关条款"})
    assert result.output["compliant"] is True
