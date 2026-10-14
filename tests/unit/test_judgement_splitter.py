"""JudgementSplitter 结构化分块单元测试。"""

from app.domain.rag.ingestion.splitters.judgement import JudgementSplitter


def test_split_by_heading() -> None:
    text = "文号 当事人 引言。\n一、违规事实 xxx。\n二、处罚决定 yyy。"
    splitter = JudgementSplitter()
    chunks = splitter.split(text)
    assert len(chunks) == 3  # 头部 + 两个分点


def test_clean_web_residue() -> None:
    text = "【打印】【关闭窗口】一、内容。"
    splitter = JudgementSplitter()
    chunks = splitter.split(text)
    assert "【打印】" not in chunks[0]


def test_inline_heading() -> None:
    text = "标题 一、关于备案渠道 xxx 二、关于首次备案 yyy"
    splitter = JudgementSplitter()
    chunks = splitter.split(text)
    assert len(chunks) == 3  # 头部 + 两个行内分点
