# Copyright 2026 MonsterZeZe
# Licensed under the Apache License, Version 2.0
# Repository: https://github.com/MonsterZeZe/AuditAgent

"""Agent 编排器。

驱动 LangGraph 状态机，管理节点执行、条件路由、重试与断点恢复。
"""

from typing import cast

from graph.graph import build_graph
from graph.state import AgentState


class AgentOrchestrator:
    """Agent 编排器骨架。"""

    def __init__(self) -> None:
        self._graph = build_graph()

    def invoke(self, initial_state: dict) -> AgentState:
        """同步执行状态机。"""
        return cast(AgentState, self._graph.invoke(initial_state))

    async def ainvoke(self, initial_state: dict) -> AgentState:
        """异步执行状态机。"""
        return cast(AgentState, await self._graph.ainvoke(initial_state))

    def stream(self, initial_state: AgentState):
        """流式执行状态机。"""
        return self._graph.stream(initial_state)

    def resume(self, checkpoint_id: str) -> AgentState:
        """从检查点恢复执行（断点恢复）。"""
        # TODO: 接入 LangGraph checkpointer 后实现
        raise NotImplementedError
