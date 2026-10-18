"""意图识别模块。

仅负责 RAG 子路由：判断用户查询应检索哪些知识库（法规/判例/双路）。
工具调用由 LLM 通过 @tool 自主决策，不经过意图识别。
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
    """意图识别器（规则实现，仅负责 RAG 子路由）。"""

    def classify(self, text: str) -> IntentResult:
        """对输入文本分类，返回需要检索的知识库列表与置信度。"""
        has_law = any(k in text for k in _LAW_KEYWORDS)
        has_case = any(k in text for k in _CASE_KEYWORDS)

        if has_law and has_case:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.9,
                "route": "rag",
                "rag_targets": ["law", "case"],
                "reason": "同时命中法规与判例关键词",
            }
        if has_law:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.85,
                "route": "rag",
                "rag_targets": ["law"],
                "reason": "命中法规关键词",
            }
        if has_case:
            return {
                "intent_type": "knowledge_query",
                "confidence": 0.85,
                "route": "rag",
                "rag_targets": ["case"],
                "reason": "命中判例关键词",
            }

        for kw in _KNOWLEDGE_KEYWORDS:
            if kw in text:
                return {
                    "intent_type": "knowledge_query",
                    "confidence": 0.5,
                    "route": "rag",
                    "reason": f"命中知识关键词: {kw}（低置信度，需 LLM 决策知识库）",
                }

        return {
            "intent_type": "direct_qa",
            "confidence": 0.6,
            "route": "direct",
            "reason": "默认直接问答（工具调用由 LLM 自主决策）",
        }
