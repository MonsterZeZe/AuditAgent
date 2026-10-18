"""底稿生成工具。

根据科目、审定表数据、审计程序与发现事项，生成 Markdown 底稿框架，
包含审定表、明细表、抽凭底稿、询证函模板、测试底稿，并预留审计说明/结论空白栏。
"""

from app.domain.tools.base import Tool, ToolResult


class WorkingPaperGenerator(Tool):
    """审计底稿生成工具。"""

    name = "working_paper_generator"
    description = "生成审计底稿框架（审定表/明细表/抽凭底稿/询证函/测试底稿）"

    def run(self, params: dict) -> ToolResult:
        subject = str(params.get("subject", "审计科目"))
        audited_data = params.get("audited_data") or {}
        procedures = params.get("audit_procedures") or []
        findings = params.get("findings") or []

        if isinstance(audited_data, dict):
            items = list(audited_data.items())
        else:
            items = [(str(i), v) for i, v in enumerate(audited_data)]

        markdown = self._generate(subject, items, procedures, findings)
        return ToolResult(status="success", output={"markdown": markdown})

    def _generate(
        self,
        subject: str,
        items: list,
        procedures: list,
        findings: list,
    ) -> str:
        lines = [f"# {subject} 审计底稿", ""]

        # 审定表
        lines.append("## 一、审定表")
        lines.append("")
        lines.append("| 项目 | 账面数 | 审定数 | 差异 | 备注 |")
        lines.append("|------|--------|--------|------|------|")
        for name, data in items:
            if isinstance(data, dict):
                book = data.get("book", data.get("账面数", ""))
                audited = data.get("audited", data.get("审定数", ""))
            else:
                book, audited = data, ""
            diff: object = ""
            if isinstance(book, (int, float)) and isinstance(audited, (int, float)):
                diff = audited - book
            lines.append(f"| {name} | {book} | {audited} | {diff} |  |")
        lines.append("")

        # 明细表
        lines.append("## 二、明细表")
        lines.append("")
        lines.append("| 序号 | 客户/项目 | 金额 | 备注 |")
        lines.append("|------|-----------|------|------|")
        for i, (name, data) in enumerate(items, 1):
            amount = data.get("book", data) if isinstance(data, dict) else data
            lines.append(f"| {i} | {name} | {amount} |  |")
        lines.append("")

        # 抽凭底稿
        lines.append("## 三、抽凭底稿")
        lines.append("")
        lines.append("| 凭证号 | 日期 | 摘要 | 金额 | 附件 | 检查结论 |")
        lines.append("|--------|------|------|------|------|----------|")
        lines.append("|  |  |  |  |  |  |")
        lines.append("")

        # 询证函模板
        lines.append("## 四、询证函模板")
        lines.append("")
        lines.append("致：＿＿＿＿＿＿（被询证单位）")
        lines.append("")
        lines.append(f"本公司（事务所）现对 **{subject}** 进行审计，请贵单位核对下列往来款项并签章确认。")
        lines.append("")
        lines.append("| 项目 | 金额 | 备注 |")
        lines.append("|------|------|------|")
        for name, data in items:
            amount = data.get("book", data) if isinstance(data, dict) else data
            lines.append(f"| {name} | {amount} |  |")
        lines.append("")
        lines.append("贵单位（盖章）：＿＿＿＿＿＿　　日期：＿＿＿＿＿＿")
        lines.append("")

        # 测试底稿
        lines.append("## 五、测试底稿")
        lines.append("")
        lines.append("| 审计程序 | 执行人 | 执行结果 | 索引 |")
        lines.append("|----------|--------|----------|------|")
        for proc in procedures or ["（未提供审计程序）"]:
            lines.append(f"| {proc} |  |  |  |")
        lines.append("")

        # 发现事项
        lines.append("## 六、发现事项")
        lines.append("")
        if findings:
            for f in findings:
                lines.append(f"- {f}")
        else:
            lines.append("- （未记录发现事项）")
        lines.append("")

        # 审计说明与结论（预留空白）
        lines.append("## 七、审计说明")
        lines.append("")
        lines.append("（此处预留审计说明栏）")
        lines.append("")
        lines.append("## 八、审计结论")
        lines.append("")
        lines.append("（此处预留审计结论栏）")
        lines.append("")

        return "\n".join(lines)
