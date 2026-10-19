"""OCR 发票识别工具。

从 PDF 发票中提取文本并解析关键字段，整理为 JSON 输出。
未指定文件路径时，自动扫描 uploader 目录取最新上传的 PDF。
"""

import re
from pathlib import Path
from typing import Optional

from app.domain.tools.base import Tool, ToolResult

_UPLOAD_DIR = "uploader"


class InvoiceOcrTool(Tool):
    """发票识别工具。"""

    name = "invoice_ocr"
    description = "识别 PDF 发票，提取发票信息整理为 JSON"

    def run(self, params: dict) -> ToolResult:
        file_path = str(params.get("file_path", "") or "").strip()
        if not file_path:
            file_path = self._find_latest_pdf() or ""
        if not file_path or not Path(file_path).exists():
            return ToolResult(status="failed", error=f"文件不存在: {file_path or '(空)'}")

        try:
            text = self._extract_pdf_text(file_path)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(status="failed", error=f"PDF 解析失败: {exc}")

        if not text.strip():
            return ToolResult(
                status="failed",
                error="未提取到文本，可能是扫描件，需接入 OCR 引擎",
            )

        invoice = self._parse_invoice(text)
        return ToolResult(
            status="success",
            output={"invoice": invoice, "file_path": file_path},
        )

    @staticmethod
    def _find_latest_pdf() -> Optional[str]:
        """扫描 uploader 目录，返回最新上传的 PDF 文件路径。"""
        dir_path = Path(_UPLOAD_DIR)
        if not dir_path.exists():
            return None
        pdfs = sorted(dir_path.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        return str(pdfs[0]) if pdfs else None

    @staticmethod
    def _extract_pdf_text(file_path: str) -> str:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _parse_invoice(text: str) -> dict:
        """从发票文本中提取关键字段（兼容标签配对与扫描件乱序两种布局）。"""
        invoice: dict = {}
        flat = " ".join(line.strip() for line in text.split("\n") if line.strip())

        # 发票号码：标签配对优先，否则取 20 位/18 位纯数字
        m = re.search(r"发票号码[^\d]*(\d{18,20})", flat)
        if m:
            invoice["invoice_number"] = m.group(1)
        else:
            m = re.search(r"(?<!\d)(\d{20})(?!\d)", flat) or re.search(
                r"(?<!\d)(\d{18})(?!\d)", flat
            )
            if m:
                invoice["invoice_number"] = m.group(1)

        # 开票日期
        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", flat)
        if m:
            invoice["issue_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # 统一社会信用代码（18 位含字母，排除纯数字的发票号码）
        codes = re.findall(r"(?<!\w)([0-9A-Z]{18})(?!\w)", flat)
        letter_codes = [c for c in codes if any(ch.isalpha() for ch in c)]
        if letter_codes:
            invoice["credit_code"] = letter_codes[0]

        # 金额（¥/￥ 后的小数金额，取最大作为价税合计）
        amounts = re.findall(r"[¥￥]\s*([0-9,]+\.\d{2})", flat)
        if amounts:
            invoice["total_amount"] = f"{max(float(a.replace(',', '')) for a in amounts):.2f}"

        # 购买方/销售方名称（标签配对，兼容"名称："与"名称"）
        m = re.search(r"购买方(?:信息)?名称[：:]?\s*([^\n:：]+)", flat)
        if m and m.group(1).strip():
            invoice["buyer_name"] = m.group(1).strip()
        m = re.search(r"销售方(?:信息)?名称[：:]?\s*([^\n:：]+)", flat)
        if m and m.group(1).strip():
            invoice["seller_name"] = m.group(1).strip()

        return invoice
