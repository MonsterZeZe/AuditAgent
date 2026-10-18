"""应用配置管理。

基于 pydantic-settings 从环境变量与 .env 文件加载配置，实现环境差异化隔离。
生产环境密钥由运维通过环境变量注入，代码与配置中禁止硬编码。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。

    字段名大小写不敏感，可通过同名环境变量（如 OLLAMA_MODEL）覆盖。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "audit-agent"
    app_env: str = "dev"  # dev / test / staging / prod
    debug: bool = True

    # 模型（Ollama）
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:2b"
    model_temperature: float = 0.2
    model_top_p: float = 0.9
    model_max_tokens: int = 2048
    model_timeout: int = 60
    model_max_concurrency: int = 4

    # 模型来源：ollama（本地）/ api（远程 OpenAI 兼容）
    llm_provider: str = "ollama"
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    api_model: str = "gpt-4o-mini"

    # 嵌入模型
    embedding_model: str = "bge-small-zh-v1.5"

    # 精排模型（CrossEncoder）
    reranker_model: str = "models/bge-reranker-base"

    # 语义分块嵌入模型
    semantic_embedding_model: str = "models/bge-large-zh-v1.5"

    # 检索/入库嵌入模型（向量库，本地 sentence-transformers）
    embedding_model_path: str = "models/bge-small-zh-v1.5"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"

    # BM25 索引缓存
    bm25_cache_dir: str = "./data/bm25_cache"
    max_bm25_documents: int = 30000

    # 会话持久化
    session_db_path: str = "./data/sessions.db"

    # 长期记忆持久化
    memory_db_path: str = "./data/memories.db"

    # 日志
    log_level: str = "INFO"
    log_dir: str = "./logs"


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例（进程内缓存）。"""
    return Settings()
