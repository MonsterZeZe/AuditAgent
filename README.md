# 审计领域智能 Agent 系统

面向审计领域的智能 Agent 系统，结合双 RAG 知识库与本地大模型，实现**审计问答、合规校验、文档分析、风险识别、财务计算、底稿生成**等核心能力。系统采用模块化分层设计，支持全链路可追溯、可监控、可断点恢复，满足审计场景对数据安全、结果可信、过程可审计的强需求。

## 核心特性

- **Agent 状态机**：基于 LangGraph，`first_agent(bind_tools) + ToolNode` 工具循环 + 意图路由 + RAG 检索 + 结果校验
- **双 RAG 知识库**：法规知识库（法定依据）+ 判例知识库（个案参考），独立 Collection 互不干扰，支持扩展更多知识库
- **RAG 二阶检索**：向量（ChromaDB）+ BM25 多路召回 → CrossEncoder 精排重排序，差异化分块策略
- **工具自主调用**：大模型通过 `@tool` 自主决策调用工具（底稿生成/发票识别/财务计算）
- **记忆系统**：短期（会话多轮）+ 长期（跨会话沉淀），均 SQLite 持久化
- **安全防护**：Prompt 注入检测、判例安全提示约束
- **多智能体预留**：知识库列表化，新增知识库仅需扩展映射

## 技术栈

| 层 | 技术 |
|----|------|
| Web 框架 | FastAPI + Uvicorn |
| 交互界面 | Streamlit |
| Agent 框架 | LangChain + LangGraph（ToolNode、bind_tools） |
| 向量库 | ChromaDB |
| 模型接入 | Ollama（本地） |
| 生成模型 | qwen3.5:2b（支持 function calling） |
| 嵌入模型 | bge-small-zh-v1.5（sentence-transformers） |
| 精排模型 | bge-reranker-base（CrossEncoder） |
| 持久化 | SQLite（会话 + 长期记忆） |
| 语言 | Python 3.10+ |

## 目录结构

```
audit-agent/
├── app/
│   ├── api/                      # 接入层（HTTP 接口、路由、schema）
│   ├── application/              # 应用层（编排器、会话管理）
│   ├── domain/                   # 领域层（意图、RAG、工具、记忆、校验）
│   │   └── tools/                #   审计工具（@tool 包装 + 领域实现）
│   ├── infrastructure/           # 基础设施层（LLM、向量库、持久化）
│   └── core/                     # 核心共享（配置、日志、异常、常量）
├── graph/                        # LangGraph 状态机
│   ├── state.py                  #   State 契约
│   ├── services.py               #   服务懒加载 + 知识库映射
│   ├── nodes/                    #   节点（first_agent/intent/retrieval/generate 等）
│   └── edges/                    #   条件边路由
├── scripts/                      # 运维脚本（数据入库）
├── streamlit_app.py              # Streamlit 交互页面
├── tests/                        # 单元测试
├── data/                         # 运行时数据（向量库、数据库，不入库）
├── models/                       # 本地模型文件（不入库）
├── uploader/                     # 用户上传文件（不入库）
└── deploy/                       # 部署配置
```

## 快速开始

### 1. 前置要求

- Python 3.10+
- [Ollama](https://ollama.com/)（本地大模型服务）

### 2. 准备模型

```bash
# 启动 Ollama 后拉取生成模型（需支持 function calling）
ollama pull qwen3.5:2b
```

下载嵌入与精排模型到 `models/` 目录：

```bash
# 嵌入模型（检索/入库向量）
python -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-small-zh-v1.5', local_dir='models/bge-small-zh-v1.5')"

# 精排模型（CrossEncoder）
python -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-reranker-base', local_dir='models/bge-reranker-base')"
```

> 若下载因 Xet CDN 401 失败，加环境变量 `HF_HUB_DISABLE_XET=1` 重试。

### 3. 安装依赖

```bash
python -m venv venv
# Windows: venv\Scripts\activate  /  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# 开发依赖（测试/静态检查）
pip install pytest pytest-asyncio flake8 mypy
```

### 4. 配置

```bash
cp .env.example .env
```

关键配置项见下文「配置项说明」。

### 5. 启动服务

```bash
# HTTP 接口（无热重载，避免偶发空响应）
uvicorn main:app --host 0.0.0.0 --port 8000

# Streamlit 交互页面
streamlit run streamlit_app.py
```

访问 `http://localhost:8000/docs` 查看 Swagger 交互文档，或 `http://localhost:8501` 使用 Streamlit 页面。

## 使用说明

### 数据入库

数据按目录自动识别知识库与分块策略：

| 数据目录 | 知识库 Collection | 分块策略 |
|----------|------------------|----------|
| `dataset/judgements/`（判例） | `case_library` | 按"一、二、"分点 |
| `dataset/laws/`（法规） | `regulatory_laws` | 按"第X条" |

```bash
# 入库判例（自动进 case_library）
python scripts/ingest.py dataset/judgements/

# 入库法规（自动进 regulatory_laws）
python scripts/ingest.py dataset/laws/
```

> 支持 txt / md / pdf / docx 格式，可按 `--collection` 手动覆盖。

### API 接口

#### `POST /chat`

**请求体**：

```json
{
  "question": "审计函证的准则要求是什么",
  "session_id": "可选，会话 ID（多轮对话）",
  "user_id": "可选，用户标识（长期记忆）"
}
```

**响应体**：

```json
{
  "trace_id": "请求追踪 ID",
  "session_id": "会话 ID",
  "answer": "回答内容",
  "intent": "knowledge_query",
  "route": "rag",
  "sources": [],
  "execution_status": "success"
}
```

### Streamlit 交互页面

- 侧边栏**上传文件**（自动保存到 `uploader/`，与当前会话绑定）
- 上传发票 PDF 后，提问"帮我识别发票"即可自动调用 OCR 工具
- 支持多轮对话、点击追问、历史会话切换、短期/长期记忆可视化

### 工具能力

系统内置 4 个审计工具，由大模型自主决策调用：

| 工具 | 能力 |
|------|------|
| `working_paper_generator` | 生成审定表/明细表/询证函等底稿框架 |
| `invoice_ocr` | 识别 PDF 发票，提取号码/日期/金额等为 JSON |
| `arithmetic_validator` | 重算/勾稽校验/差异计算 |

## 测试与检查

```bash
# 单元测试
pytest tests/unit -q

# 静态检查
flake8 app graph scripts main.py streamlit_app.py tests
mypy app graph scripts main.py tests
```

## 配置项说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `qwen3.5:2b` | 生成模型（需支持 function calling） |
| `EMBEDDING_MODEL_PATH` | `models/bge-small-zh-v1.5` | 嵌入模型路径 |
| `RERANKER_MODEL` | `models/bge-reranker-base` | 精排模型路径 |
| `MODEL_TEMPERATURE` | `0.2` | 生成温度 |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | 向量库持久化路径 |
| `SESSION_DB_PATH` | `./data/sessions.db` | 会话数据库路径 |
| `MEMORY_DB_PATH` | `./data/memories.db` | 长期记忆数据库路径 |
| `BM25_CACHE_DIR` | `./data/bm25_cache` | BM25 索引缓存目录 |
| `MAX_BM25_DOCUMENTS` | `30000` | BM25 文档数上限 |

## 注意事项

- **模型选择**：`qwen3.5:2b` 是唯一支持 function calling 且内存占用小的本地模型；但它有思考模式，单次调用约 20-30 秒，端到端较慢。
- **不要用 `reload=True`**：热重载会导致模型偶发空响应，生产请用 `uvicorn main:app`。
- **数据安全**：`data/`、`models/`、`uploader/`、`.env` 均已加入 `.gitignore`。
- **知识库扩展**：新增知识库只需在 `graph/services.py` 的 `KNOWLEDGE_BASES` 添加映射，并在 `intent/router.py` 添加触发词。
- **工具扩展**：新增工具用 `@tool` 装饰器定义，加入 `langchain_tools.py` 的 `LANGCHAIN_TOOLS` 列表即可。

## 架构设计文档

完整架构设计见 [架构设计.md](架构设计.md) 与 [架构设计-章节细化.md](架构设计-章节细化.md)。
