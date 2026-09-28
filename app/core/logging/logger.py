"""结构化 JSON 日志。

统一日志格式，支持控制台（开发）与文件滚动（生产）双通道输出，
并支持 trace_id / session_id 等上下文字段透传。
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config.settings import get_settings


class JsonFormatter(logging.Formatter):
    """将日志记录格式化为结构化 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("trace_id", "session_id", "user_id", "module"):
            value = getattr(record, key, None)
            if value:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger。"""
    return logging.getLogger(name)


def setup_logging(level: Optional[str] = None) -> None:
    """初始化全局日志配置。"""
    settings = get_settings()
    log_level = (level or settings.log_level).upper()

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()

    formatter = JsonFormatter()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        os.makedirs(settings.log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(settings.log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # 日志目录不可写时仅保留控制台输出，不阻断启动
        pass
