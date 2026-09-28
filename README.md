# 审计领域智能 Agent 系统

面向审计领域的智能 Agent 系统，结合 RAG 知识库与本地大模型，实现**审计问答、合规校验、文档分析、风险识别**等核心能力。系统采用模块化分层设计，支持全链路可追溯、可监控、可断点恢复，满足审计场景对数据安全、结果可信、过程可审计的强需求。

## 核心特性

- **Agent 状态机**：基于 LangGraph，支持意图路由、RAG 检索、工具调用、结果校验、检查点持久化
- **RAG 二阶检索**：向量（ChromaDB）+ BM25 多路召回 → CrossEncoder 精排重排序
- **本地大模型**：Ollama 接入，统一 LLM 抽象接口，支持多模型替换
- **记忆系统**：短期（会话多轮）+ 长期（跨会话沉淀），均 SQLite 持久化
- **安全防护**：Prompt 注入检测、系统提示隔离、输出合规校验
- **工具插件化**：审计工具遵循统一规范，注册即用
- **多智能体预留**：能力型子图（RAG/工具/校验），为阶段 2 拆分预留边界

## 技术栈

| 层 | 技术 |
|----|------|
| Web 框架 | FastAPI + Uvicorn |
| Agent 框架 | LangChain + LangGraph |
| 向量库 | ChromaDB |
| 模型接入 | Ollama（本地） |
| 生成模型 | gemma3:4b |
| 嵌入模型 | nomic-embed-text |
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
│   ├── infrastructure/           # 基础设施层（LLM、向量库）
│   └── core/                     # 核心共享（配置、日志、异常、常量）
├── graph/                        # LangGraph 状态机（State + 节点 + 子图）
├── scripts/                      # 运维脚本（数据入库）
├── tests/                        # 单元测试
├── data/                         # 运行时数据（向量库、数据库，不入库）
├── models/                       # 本地模型文件（精排模型，不入库）
├── plugins/                      # 插件目录
└── deploy/                       # 部署配置
```

## 快速开始

### 1. 前置要求

- Python 3.10+
- [Ollama](https://ollama.com/)（本地大模型服务）

### 2. 准备模型

```bash
# 启动 Ollama 后拉取模型
ollama pull gemma3:4b          # 生成模型
ollama pull nomic-embed-text   # 嵌入模型
```

下载精排模型到项目 `models/` 目录（约 1.1GB）：

```bash
# Windows / 有 Xet CDN 网络问题时禁用 Xet
python -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-reranker-base', local_dir='models/bge-reranker-base')"
```

> 若下载因 Xet CDN 401 失败，加环境变量 `HF_HUB_DISABLE_XET=1` 重试。

### 3. 安装依赖

```bash
python -m venv venv
# Windows: venv\Scripts\activate  /  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# 开发依赖（测试/静态检查）
pip install -r requirements.txt && pip install pytest pytest-asyncio flake8 mypy
```

### 4. 配置

复制环境变量模板，按需修改：

```bash
cp .env.example .env
```

关键配置项见下文「配置项说明」。

### 5. 启动服务

```bash
# 生产/实测推荐（无热重载，避免偶发空响应）
uvicorn main:app --host 0.0.0.0 --port 8000

# 或开发模式（热重载，偶发模型空响应，仅调试用）
python main.py
```

访问 `http://localhost:8000/docs` 查看 Swagger 交互文档。

## 使用说明

### 数据入库

将审计文档（TXT/PDF/DOCX）加载、分块、嵌入并入库：

```bash
python scripts/ingest.py <文件或目录> [--collection accounting_standards] [--chunk-size 500] [--chunk-overlap 50]
```

### API 接口

#### `GET /health`

健康检查，返回 `{"status": "ok"}`。

#### `POST /chat`

执行一次审计问答。

**请求体**：

```json
{
  "question": "什么是会计信息质量要求",
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
  "sources": [{"doc_name": "会计准则示例", "chapter": "", "page": "1", "security_level": "internal"}],
  "execution_status": "success"
}
```

**多轮对话示例**（携带同一 `session_id` 可保留上下文）：

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  --data-binary @- <<'EOF'
{"question": "什么是会计信息质量要求", "session_id": "my-session"}
EOF
```

> 提示：Windows 下 curl 直接传中文 JSON 可能因编码报 400，建议用 Python 请求或将 JSON 写入 UTF-8 文件后用 `--data-binary @file`。

## 测试与检查

```bash
# 单元测试（26 项）
pytest tests/unit -q

# 静态检查
flake8 app graph scripts main.py tests
mypy app graph scripts main.py tests
```

## 配置项说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `gemma3:4b` | 生成模型 |
| `EMBEDDING_MODEL` | `nomic-embed-text` | 嵌入模型 |
| `RERANKER_MODEL` | `models/bge-reranker-base` | 精排模型路径 |
| `MODEL_TEMPERATURE` | `0.2` | 生成温度 |
| `MODEL_MAX_TOKENS` | `2048` | 最大生成 token 数 |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | 向量库持久化路径 |
| `SESSION_DB_PATH` | `./data/sessions.db` | 会话数据库路径 |
| `MEMORY_DB_PATH` | `./data/memories.db` | 长期记忆数据库路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_DIR` | `./logs` | 日志目录 |

## 注意事项

- **不要用 `reload=True`**：开发模式热重载会导致模型偶发返回空内容，生产/实测请用 `uvicorn main:app`（无 reload）。
- **生成模型选择**：`qwen3.5:2b` 存在思考模式 `content` 为空的问题（回答在 `thinking` 字段），故默认使用 `gemma3:4b`。
- **数据安全**：`data/`、`models/`、`.env` 均已加入 `.gitignore`，敏感数据不入库。
- **依赖注入**：领域层面向接口编程，模型/向量库/精排均可通过实现接口替换。

## 架构设计文档

完整架构设计见 [架构设计.md](架构设计.md) 与 [架构设计-章节细化.md](架构设计-章节细化.md)。
