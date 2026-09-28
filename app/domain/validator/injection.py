"""Prompt 注入检测。

基于规则识别越狱指令、系统指令覆盖、提示泄露与检索篡改等攻击。
后续可扩展为模型辅助检测。
"""

from typing import Any

_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "忽略之前的指令",
    "忽略以上指令",
    "忘记之前的指令",
    "无视之前的",
    "you are now",
    "你现在是",
    "system prompt",
    "系统提示词",
    "你现在的角色是",
    "reveal your prompt",
    "show me your instructions",
    "你的提示词",
    "你的系统指令",
    "change top_k",
    "修改检索参数",
)


class InjectionDetector:
    """基于规则的 Prompt 注入检测。"""

    def detect(self, text: str) -> dict[str, Any]:
        """检测输入是否包含注入模式。"""
        lowered = text.lower()
        hits = [p for p in _INJECTION_PATTERNS if p.lower() in lowered]
        return {
            "detected": bool(hits),
            "patterns": hits,
            "severity": "high" if hits else "none",
        }
