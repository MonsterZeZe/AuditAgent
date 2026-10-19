# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""LangChain @tool 包装。

将领域工具包装为 LangChain tool，供 LLM function calling 与 ToolNode 使用。
"""

from langchain_core.tools import tool

from app.domain.tools.arithmetic import ArithmeticValidator
from app.domain.tools.invoice_ocr import InvoiceOcrTool
from app.domain.tools.working_paper import WorkingPaperGenerator


@tool
def working_paper_generator(subject: str) -> str:
    """生成审计底稿框架（审定表、明细表、抽凭底稿、询证函、测试底稿）。

    Args:
        subject: 审计科目名称，如"应收账款"、"存货"、"固定资产"等。
    """
    result = WorkingPaperGenerator().run({"subject": subject})
    return str(result.output.get("markdown", ""))


@tool
def arithmetic_validator(formula: str, data: dict) -> str:
    """财务计算校验：重算（坏账/折旧/跌价/税费/商誉）、勾稽校验、差异计算。

    Args:
        formula: 公式类型，取值 bad_debt / depreciation / inventory / tax / goodwill / reconciliation / difference。
        data: 财务数据字典，如 {"receivable": 1000, "ratio": 0.05}。
    """
    result = ArithmeticValidator().run({"formula": formula, "data": data})
    return str(result.output)


@tool
def invoice_ocr(file_path: str = "") -> str:
    """识别 PDF 发票并提取发票信息（号码、日期、金额、购销双方）为 JSON。

    Args:
        file_path: PDF 发票文件的路径；为空时自动使用 uploader 目录最新上传的发票。
    """
    result = InvoiceOcrTool().run({"file_path": file_path})
    if result.status == "success":
        return str(result.output)
    return f"识别失败: {result.error}"


LANGCHAIN_TOOLS = [working_paper_generator, arithmetic_validator, invoice_ocr]
