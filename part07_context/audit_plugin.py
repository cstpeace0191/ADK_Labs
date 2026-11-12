"""강의노트 Part 7 슬라이드 89 Plugin: 앱 전체에 적용되는 콜백 묶음(BasePlugin).

에이전트마다 로깅·정책 콜백을 반복하지 않고 Runner(plugins=[...])에 한 번 등록한다.
"""
import time

from google.adk.plugins import BasePlugin


class AuditPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="audit")
        self.log: list[dict] = []
        self._t0: dict[str, float] = {}

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        self._t0[tool_context.function_call_id] = time.perf_counter()
        print(f"   [audit] ▶ {tool.name} args={tool_args}")
        return None

    async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
        ms = (time.perf_counter() - self._t0.pop(tool_context.function_call_id, time.perf_counter())) * 1000
        self.log.append({"tool": tool.name, "args": tool_args, "result": result, "ms": round(ms, 1)})
        print(f"   [audit] ◀ {tool.name} {ms:.1f}ms result={result}")
        return None
