# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""财务计算校验工具。

支持重算（坏账计提、折旧摊销、存货跌价、税费测算、商誉减值）、
勾稽关系校验（资产=负债+权益）与差异计算（账面 vs 审定）。
"""

from app.domain.tools.base import Tool, ToolResult


class ArithmeticValidator(Tool):
    """财务计算校验工具。"""

    name = "arithmetic_validator"
    description = "财务计算校验（重算/勾稽关系/差异计算）"

    def run(self, params: dict) -> ToolResult:
        formula = str(params.get("formula", ""))
        data = params.get("data") or {}

        handlers = {
            "bad_debt": self._bad_debt,
            "depreciation": self._depreciation,
            "inventory": self._inventory,
            "tax": self._tax,
            "goodwill": self._goodwill,
            "reconciliation": self._reconciliation,
            "difference": self._difference,
        }
        handler = handlers.get(formula)
        if handler is None:
            return ToolResult(status="failed", error=f"未知公式类型: {formula}")
        return handler(data)

    @staticmethod
    def _bad_debt(data: dict) -> ToolResult:
        """坏账计提：坏账准备 = 应收余额 × 计提比例。"""
        receivable = data.get("receivable", data.get("应收余额", 0))
        ratio = data.get("ratio", data.get("计提比例", 0))
        result = receivable * ratio
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"{receivable} × {ratio} = {result}",
            },
        )

    @staticmethod
    def _depreciation(data: dict) -> ToolResult:
        """折旧摊销：年折旧 = (原值 - 残值) / 年限。"""
        cost = data.get("cost", data.get("原值", 0))
        residual = data.get("residual", data.get("残值", 0))
        years = data.get("years", data.get("年限", 1))
        if years == 0:
            return ToolResult(status="failed", error="年限不能为 0")
        result = (cost - residual) / years
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"({cost} - {residual}) / {years} = {result}",
            },
        )

    @staticmethod
    def _inventory(data: dict) -> ToolResult:
        """存货跌价：跌价准备 = max(成本 - 可变现净值, 0)。"""
        cost = data.get("cost", data.get("成本", 0))
        nrv = data.get("nrv", data.get("可变现净值", 0))
        result = max(cost - nrv, 0)
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"max({cost} - {nrv}, 0) = {result}",
            },
        )

    @staticmethod
    def _tax(data: dict) -> ToolResult:
        """税费测算：税费 = 计税基础 × 税率。"""
        base = data.get("base", data.get("计税基础", 0))
        rate = data.get("rate", data.get("税率", 0))
        result = base * rate
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"{base} × {rate} = {result}",
            },
        )

    @staticmethod
    def _goodwill(data: dict) -> ToolResult:
        """商誉减值：减值 = max(账面价值 - 可收回金额, 0)。"""
        book = data.get("book_value", data.get("账面价值", 0))
        recoverable = data.get("recoverable", data.get("可收回金额", 0))
        result = max(book - recoverable, 0)
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"max({book} - {recoverable}, 0) = {result}",
            },
        )

    @staticmethod
    def _reconciliation(data: dict) -> ToolResult:
        """勾稽校验：资产 = 负债 + 权益。"""
        assets = data.get("assets", data.get("资产", 0))
        liabilities = data.get("liabilities", data.get("负债", 0))
        equity = data.get("equity", data.get("权益", 0))
        right = liabilities + equity
        balanced = abs(assets - right) < 1e-6
        return ToolResult(
            status="success",
            output={
                "balanced": balanced,
                "assets": assets,
                "liabilities_plus_equity": right,
                "detail": f"资产 {assets} {'=' if balanced else '≠'} 负债+权益 {right}",
            },
        )

    @staticmethod
    def _difference(data: dict) -> ToolResult:
        """差异计算：差异 = 审定数 - 账面数。"""
        book = data.get("book", data.get("账面数", 0))
        audited = data.get("audited", data.get("审定数", 0))
        result = audited - book
        return ToolResult(
            status="success",
            output={
                "result": result,
                "detail": f"{audited} - {book} = {result}",
            },
        )
