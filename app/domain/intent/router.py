"""意图识别模块。

规则优先：关键词快速分类意图，并对 RAG 查询做子路由
（法规知识库 / 判例知识库 / 双路），硬规则命中即跳过 LLM，节省开销。
"""

from graph.state import IntentResult

# 法规知识库触发词：执业要求、程序规范、准则规定、法定义务、合规判断依据
_LAW_KEYWORDS = (
    "准则",
    "法规",
    "规定",
    "注册会计师法",
    "会计法",
    "执业",
    "程序",
    "函证",
    "监盘",
    "法定义务",
    "合规",
    "监管",
    "职业道德",
    "独立性",
    "审计程序",
)

# 判例知识库触发词：审计失败案例、司法责任、风险后果、过错认定案例
_CASE_KEYWORDS = (
    "判决",
    "案例",
    "处罚",
    "法律责任",
    "司法",
    "诉讼",
    "风险后果",
    "过错",
    "本院认为",
    "赔偿",
    "行政处罚",
    "责任认定",
    "失败案例",
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

_KNOWLEDGE_KEYWORDS = (
    "查",
    "检索",
    "什么是",
    "定义",
    "解释",
    "查询",
    "依据",
    "条款",
    "标准",
)


class IntentRouter:
    """意图识别器（规则实现）。"""

    def classify(self, text: str) -> IntentResult:
        """对输入文本分类，返回意图、路由与 RAG 子路由目标。"""
        for kw in _TOOL_KEYWORDS:
            if kw in text:
                return {
                    "intent_type": "tool_operation",
                    "confidence": 0.9,
                    "route": "tool",
                    "reason": f"命中工具关键词: {kw}",
                }

        has_law = any(k in text for k in _LAW_KEYWORDS)
        has_case = any(k in text for k in _CASE_KEYWORDS)

        if has_law and has_case:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.9,
                "route": "rag",
                "rag_target": "both",
                "reason": "同时命中法规与判例关键词",
            }
        if has_law:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.85,
                "route": "rag",
                "rag_target": "law",
                "reason": "命中法规关键词",
            }
        if has_case:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.85,
                "route": "rag",
                "rag_target": "case",
                "reason": "命中判例关键词",
            }

        for kw in _KNOWLEDGE_KEYWORDS:
            if kw in text:
                return {
                    "intent_type": "knowledge_query",
                    "confidence": 0.7,
                    "route": "rag",
                    "rag_target": "law",
                    "reason": f"命中知识关键词: {kw}",
                }

        return {
            "intent_type": "direct_qa",
            "confidence": 0.6,
            "route": "direct",
            "reason": "默认直接问答",
        }
