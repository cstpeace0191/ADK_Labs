"""agents-cli 프로젝트의 OpenTelemetry를 로컬에서 확인 (강의노트 Part 13 슬라이드 154). 🟢 키 · 네트워크 없이 실행.

실행 (part13_agents_cli 폴더): python telemetry/trace_local.py

- app/agent.py의 root_agent를 그대로 쓰되, 모델만 대본대로 답하는 가짜 모델로 바꾸고 도구는 오프라인(AGENT_OFFLINE=1)
- 배포된 서버와 같은 span 트리(invoke_workflow > invoke_agent > generate_content · execute_tool)가 나오는지
- gen_ai.agent.name이 manifest의 root_agent_name과 같은지 — 다르면 콘솔에서 trace를 이름으로 찾지 못한다
- 배포 설정(Terraform)이 켜는 텔레메트리 환경 변수를 정리해 보여 준다
"""
import asyncio
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT.parent))      # ADK_Labs (common)
sys.path.insert(0, str(PROJECT))             # app 패키지
os.environ["AGENT_OFFLINE"] = "1"
import common.bootstrap  # noqa: E402,F401
from common.telemetry_util import fake_llm, install_telemetry, print_span_tree  # noqa: E402

EXPORTER, _ = install_telemetry(service_name="agents-cli-workflow")   # = Terraform의 OTEL_SERVICE_NAME

# agents-cli-workflow/deployment/terraform/single-project/service.tf 가 Cloud Run에 넣는 값 (2026-11 생성본)
DEPLOY_ENV = [
    ("OTEL_SERVICE_NAME", "agents-cli-workflow", "trace · 지표의 service.name"),
    ("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true", "fast_api_app.py → get_fast_api_app(otel_to_cloud=True)"),
    ("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental", "최신 GenAI 의미 규약으로 기록"),
    ("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "NO_CONTENT", "span · 로그에 대화 내용 없음"),
    ("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false", "레거시 span에도 내용 없음"),
    ("OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK", "upload", "대화 본문은 따로 업로드 →"),
    ("OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH", "gs://<logs 버킷>/completions", "GCS(jsonl), 접근 통제"),
]


def manifest_root_name() -> str:
    text = (PROJECT / "agents-cli-manifest.yaml").read_text(encoding="utf-8")
    m = re.search(r"root_agent_name:\s*['\"]?([\w-]+)", text)
    return m.group(1) if m else "?"


async def main():
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from app.agent import root_agent

    agent = root_agent.model_copy(update={"model": fake_llm(
        [("get_weather", {"location": "Seoul"}), "서울은 지금 맑습니다 (오프라인 표본값)."])})
    runner = InMemoryRunner(agent=agent, app_name="app")
    s = await runner.session_service.create_session(app_name="app", user_id="u1")
    msg = types.Content(role="user", parts=[types.Part(text="서울 날씨 알려줘")])
    async for ev in runner.run_async(user_id="u1", session_id=s.id, new_message=msg):
        if ev.is_final_response() and ev.content and ev.content.parts:
            print("  [agent]", "".join(p.text or "" for p in ev.content.parts))

    spans = EXPORTER.get_finished_spans()
    print("\n=== span 트리 (배포된 서버에서 Cloud Trace에 보이는 모양) ===")
    print_span_tree(spans)
    names = {s.attributes.get("gen_ai.agent.name") for s in spans} - {None}
    want = manifest_root_name()
    print(f"\n  gen_ai.agent.name = {sorted(names)} · manifest root_agent_name = {want} → "
          f"{'일치 ✓' if want in names else '불일치 ✗ (agent.py와 manifest를 같이 고쳐야 한다)'}")
    print("\n=== 배포 설정이 켜는 텔레메트리 환경 변수 (service.tf) ===")
    for k, v, why in DEPLOY_ENV:
        print(f"  {k:<46} {v:<30} {why}")


if __name__ == "__main__":
    asyncio.run(main())
