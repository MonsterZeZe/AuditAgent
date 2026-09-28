"""审计智能助手 - Streamlit 交互页面。

在侧边栏可视化展示短期记忆（当前会话对话历史）与长期记忆（跨会话历史关注），
主区域为聊天问答界面。

用法:
    streamlit run streamlit_app.py
"""

from uuid import uuid4

import streamlit as st

from app.application.session.session import SessionManager
from app.domain.memory.store import SqliteMemoryStore
from graph.graph import build_graph


@st.cache_resource
def get_orchestrator():
    """缓存编译后的 Agent 图（避免每次重载）。"""
    return build_graph()


@st.cache_resource
def get_session_manager() -> SessionManager:
    return SessionManager()


@st.cache_resource
def get_memory_store() -> SqliteMemoryStore:
    return SqliteMemoryStore()


st.set_page_config(page_title="审计智能助手", page_icon="📋", layout="wide")
st.title("📋 审计智能助手")

# 会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

session_manager = get_session_manager()
memory_store = get_memory_store()

# ---- 侧边栏：记忆系统可视化 ----
with st.sidebar:
    st.header("⚙️ 会话设置")
    user_id = st.text_input("用户 ID", value="streamlit-user")
    if st.button("🔄 新建会话"):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # 短期记忆：当前会话对话历史
    st.subheader("🧠 短期记忆（当前会话）")
    if st.session_state.session_id:
        st.caption(f"会话 ID: `{st.session_state.session_id[:8]}…`")
        short_memories = session_manager.load_messages(st.session_state.session_id)
        if short_memories:
            for m in short_memories:
                icon = "👤" if m["role"] == "user" else "🤖"
                st.caption(f"{icon} {m['content'][:36]}")
        else:
            st.caption("（会话已创建，暂无对话）")
    else:
        st.caption("（尚未创建会话，发起提问后自动创建）")

    st.divider()

    # 长期记忆：跨会话历史关注
    st.subheader("💾 长期记忆（跨会话）")
    long_memories = memory_store.recall(user_id, top_k=5)
    if long_memories:
        for m in long_memories:
            st.caption(f"· {m['content'][:48]}")
    else:
        st.caption("（暂无长期记忆，随问答自动沉淀）")

# ---- 主区域：聊天 ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("请输入您的审计问题")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    session_id = session_manager.get_or_create(st.session_state.session_id, user_id)
    st.session_state.session_id = session_id

    history = session_manager.load_messages(session_id)
    memories = memory_store.recall(user_id, top_k=3)

    initial_state = {
        "user_input": question,
        "session_id": session_id,
        "trace_id": uuid4().hex,
        "user_id": user_id,
        "messages": history,
        "long_term_memory": memories,
    }

    with st.spinner("思考中..."):
        result = get_orchestrator().invoke(initial_state)

    answer = result.get("generation", "")
    session_manager.append(session_id, "user", question)
    session_manager.append(session_id, "assistant", answer)
    memory_store.add_memory(
        user_id,
        "task_history",
        f"问：{question}\n答：{answer[:200]}",
        topic=question[:50],
    )

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
        sources = result.get("rag_context", {}).get("sources", [])
        if sources:
            with st.expander("📚 引用来源"):
                for s in sources:
                    st.caption(
                        f"· {s.get('doc_name', '未知')} 章节:{s.get('chapter', '')} "
                        f"页码:{s.get('page', '')} 密级:{s.get('security_level', '')}"
                    )

    # 回答后刷新侧边栏记忆展示
    st.rerun()
