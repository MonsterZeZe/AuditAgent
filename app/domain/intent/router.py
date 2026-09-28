"""意图识别模块。

规则优先：基于关键词规则快速分类，命中率高且零成本；
规则无法判定时降级为直接问答。后续可接入模型兜底。
"""

from graph.state import IntentResult

_KNOWLEDGE_KEYWORDS = (
    "查",
    "检索",
    "什么是",
    "准则",
    "法规",
    "规定",
    "标准",
    "定义",
    "解释",
    "查询",
    "依据",
    "条款",
)

_TOOL_KEYWORDS = (
    "计算",
    "比对",
    "校验",
    "核算",
    "勾稽",
    "生成报告",
    "导出",
    "汇总",
    "分析报表",
)


class IntentRouter:
    """意图识别器（规则实现）。"""

    def classify(self, text: str) -> IntentResult:
        """对输入文本分类，返回意图结果与路由目标。"""
        for kw in _TOOL_KEYWORDS:
            if kw in text:
                return {
                    "intent_type": "tool_operation",
                    "confidence": 0.9,
                    "route": "tool",
                    "reason": f"命中工具关键词: {kw}",
                }
        for kw in _KNOWLEDGE_KEYWORDS:
            if kw in text:
                return {
                    "intent_type": "knowledge_query",
                    "confidence": 0.8,
                    "route": "rag",
                    "reason": f"命中知识关键词: {kw}",
                }
        return {
            "intent_type": "direct_qa",
            "confidence": 0.6,
            "route": "direct",
            "reason": "默认直接问答",
        }
