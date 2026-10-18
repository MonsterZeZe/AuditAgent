"""审计智能助手 - Streamlit 交互页面。

侧边栏可视化展示短期记忆（当前会话）与长期记忆（跨会话），
支持点击对话记录追问、展开查看详情、切换历史会话。

用法:
    streamlit run streamlit_app.py
"""

from pathlib import Path
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
if "followup_context" not in st.session_state:
    st.session_state.followup_context = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

session_manager = get_session_manager()
memory_store = get_memory_store()


def switch_session(session_id: str) -> None:
    """切换到指定会话，加载其对话历史。"""
    st.session_state.session_id = session_id
    st.session_state.messages = [
        {"role": m["role"], "content": m["content"]}
        for m in session_manager.load_messages(session_id)
    ]
    st.session_state.followup_context = None


# ---- 侧边栏 ----
with st.sidebar:
    st.header("📤 文件上传")
    uploaded_file = st.file_uploader(
        "上传文件到 uploader 目录",
        type=["txt", "pdf", "docx", "md", "markdown"],
    )
    if uploaded_file is not None:
        save_dir = Path("uploader")
        save_dir.mkdir(exist_ok=True)
        # 加时间戳前缀，避免重名覆盖，并保留原文件名
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = save_dir / f"{timestamp}_{uploaded_file.name}"
        save_path.write_bytes(uploaded_file.getbuffer())
        st.session_state.uploaded_files.append(str(save_path))
        st.success(f"已保存: {save_path.name}")

    st.divider()

    st.header("⚙️ 会话设置")
    user_id = st.text_input("用户 ID", value="streamlit-user")
    if st.button("🔄 新建会话"):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.followup_context = None
        st.rerun()

    st.divider()

    # 历史会话切换
    st.subheader("📂 历史会话（点击切换）")
    sessions = session_manager.list_sessions(user_id)
    if sessions:
        for s in sessions[:10]:
            current = s["session_id"] == st.session_state.session_id
            prefix = "▶ " if current else "· "
            label = f"{prefix}{s['session_id'][:8]}… ({s['updated_at'][:10]})"
            if st.button(label, key=f"switch_{s['session_id']}"):
                switch_session(s["session_id"])
                st.rerun()
    else:
        st.caption("（暂无历史会话）")

    st.divider()

    # 短期记忆：当前会话对话历史（可展开 + 追问）
    st.subheader("🧠 短期记忆（当前会话）")
    if st.session_state.session_id:
        st.caption(f"会话 ID: `{st.session_state.session_id[:8]}…`")
        short_memories = session_manager.load_messages(st.session_state.session_id)
        if short_memories:
            for i, m in enumerate(short_memories):
                icon = "👤" if m["role"] == "user" else "🤖"
                with st.expander(f"{icon} {m['content'][:20]}…", expanded=False):
                    st.write(m["content"])
                    if st.button("↩️ 追问这条", key=f"followup_{i}"):
                        st.session_state.followup_context = m["content"]
                        st.rerun()
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
            with st.expander(f"· {m['content'][:24]}…", expanded=False):
                st.write(m["content"])
    else:
        st.caption("（暂无长期记忆，随问答自动沉淀）")

# ---- 主区域 ----

# 追问提示
if st.session_state.followup_context:
    with st.container(border=True):
        st.markdown("**↩️ 追问模式**")
        st.caption(st.session_state.followup_context[:200])
        if st.button("✖ 取消追问"):
            st.session_state.followup_context = None
            st.rerun()

# 聊天历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("请输入问题，或点击侧边栏记录后在此追问")

if question:
    # streamlit 1.64+ 的 chat_input 可能返回 ChatInputValue 对象，统一取 text
    if hasattr(question, "text"):
        question = question.text

    followup = st.session_state.followup_context
    if followup:
        question = f"针对以下对话内容进行追问：\n{followup}\n\n追问：{question}"
        st.session_state.followup_context = None

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
        "chat_history": history,
        "long_term_memory": memories,
        "uploaded_files": st.session_state.get("uploaded_files", []),
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

    st.rerun()
