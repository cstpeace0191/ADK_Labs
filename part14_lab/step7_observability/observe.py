"""실습 7단계: 관측성 — 4·5단계 학사 워크플로우를 OpenTelemetry로 관측한다. 🟢 키 없이 실행.

강의노트 Part 14 '실습 7단계' 슬라이드와 Part 12 Observability(130–142)를 잇는다.
확인할 것
  ① 요청 1건 = trace 1개: invoke_workflow > invoke_node(노드마다) 트리
  ② 노드별 실행 횟수 · 평균 지연 → 느린 노드 찾기
  ③ 요청별로 끝난 노드(라우트) → 의도 분류가 어디로 보냈나
  ④ 개인정보 감사: 학번 · 주민번호가 span 속성에 남지 않았는가
  ⑤ 워크플로우 지연 지표를 OpenMetrics 텍스트로 (Prometheus가 긁어 갈 모양)
"""
from __future__ import annotations

import re
from collections import defaultdict

from common.runner_util import Session
from common.telemetry_util import install_telemetry, print_span_tree, to_openmetrics

LOGIN = {"user:student_id": "S001", "user:name": "김철수"}
QUESTIONS = ["내 성적 전부 보여줘", "CS101 성적은?", "이번 학기 수강 과목 알려줘",
             "주민번호 900101-1234567 로 조회해줘"]
PII_PATTERNS = [re.compile(r"\d{6}-\d{7}"), re.compile(r"\b20\d{6}\b")]   # 주민번호 · 8자리 학번

EXPORTER, READER = install_telemetry(service_name="academic-lab")


def _by_trace(spans):
    groups = defaultdict(list)
    for s in spans:
        groups[s.context.trace_id].append(s)
    return sorted(groups.values(), key=lambda g: min(s.start_time for s in g))


async def observe() -> dict:
    from step4_workflow.agent import root_agent as step4_root
    from step5_hitl_retry.agent import root_agent as step5_root

    EXPORTER.clear()
    for q in QUESTIONS:
        await Session(step4_root, app_name="lab", state=LOGIN, verbose=False).send(q)
    chat = Session(step5_root, app_name="lab", state=LOGIN, verbose=False)
    r = await chat.send("AI201 수강 취소하고 싶어요")          # 외부 API 재시도 → 승인 대기
    if r.pending:
        await chat.resume_input(r.pending, {"confirm": False, "reason": "관측 실습이라 취소 안 함"})

    spans = EXPORTER.get_finished_spans()
    traces = _by_trace(spans)

    print("\n  ① 요청 1건 = trace 1개 (CS101 성적 질문)")
    print_span_tree(traces[1])

    print("\n  ② 노드별 실행 횟수 · 평균 지연")
    stat = defaultdict(list)
    for s in spans:
        if s.name.startswith("invoke_node "):
            stat[s.name.split(" ", 1)[1]].append((s.end_time - s.start_time) / 1e6)
    for name, ms in sorted(stat.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        print(f"     {name:<18} {len(ms):>2}회  평균 {sum(ms) / len(ms):7.2f} ms")

    print("\n  ③ 요청별 마지막 노드 (라우트)")
    labels = QUESTIONS + ["AI201 수강 취소 (승인 요청)", "AI201 수강 취소 (거절 후 재개)"]
    for label, group in zip(labels, traces):
        nodes = [s for s in sorted(group, key=lambda s: s.end_time) if s.name.startswith("invoke_node ")]
        last = nodes[-1].name.split(" ", 1)[1] if nodes else "-"
        print(f"     {label:<34} → {last}")

    leaks = [s.name for s in spans for v in s.attributes.values() if any(p.search(str(v)) for p in PII_PATTERNS)]
    print(f"\n  ④ 개인정보 감사: span {len(spans)}개 속성 검사 → {'유출 ✗ ' + ', '.join(leaks) if leaks else '유출 없음 ✓'}")

    print("\n  ⑤ OpenMetrics (워크플로우 지연)")
    body = to_openmetrics(READER.get_metrics_data(), only_prefix="gen_ai.invoke_workflow.duration")
    for line in body.splitlines():
        if "_count" in line or "_sum" in line or line.startswith("# TYPE") or line == "# EOF":
            print("     " + line)
    return {"traces": len(traces), "spans": len(spans), "nodes": dict((k, len(v)) for k, v in stat.items()),
            "leaks": leaks}
