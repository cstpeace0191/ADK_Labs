"""obs2 — 내용(프롬프트·응답·도구 인자) 기록과 개인정보 (강의노트 Part 12 슬라이드 138). 🟢 LLM 없이 실행.

실행: python obs2_content_capture.py [modes|pii|all]
  modes : OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT 값별로 span에 어떤 '내용' 속성이 붙는지 비교
  pii   : 사용자가 학번을 입력했을 때 그 값이 span으로 새는지 모드별로 검사

환경 변수는 ADK가 실행될 때 한 번 읽히므로, 모드마다 자식 프로세스를 새로 띄운다.
"""
import asyncio
import json
import os
import subprocess
import sys

import _path  # noqa: F401
from _obs import section

CONTENT_KEYS = ("gen_ai.input.messages", "gen_ai.output.messages", "gen_ai.system_instructions",
                "gen_ai.tool.call.arguments", "gen_ai.tool.call.result")
PII = "20261234"
QUESTION = f"제 학번은 {PII}이에요. 서울 날씨 알려줘"
MODES = ["", "NO_CONTENT", "EVENT_ONLY", "SPAN_ONLY", "SPAN_AND_EVENT"]


def child() -> None:
    """자식 프로세스: 한 턴 실행 후 span 속성 요약을 JSON으로 출력."""
    from _obs import install_telemetry, run_turn, weather_agent
    exporter, _ = install_telemetry()
    asyncio.run(run_turn(weather_agent(), QUESTION, show=False))
    spans = exporter.get_finished_spans()
    found = sorted({k for s in spans for k in s.attributes if k in CONTENT_KEYS})
    leak = [s.name for s in spans if any(PII in str(v) for v in s.attributes.values())]
    sample = next((str(s.attributes["gen_ai.input.messages"]) for s in spans
                   if "gen_ai.input.messages" in s.attributes), "")
    print(json.dumps({"found": found, "leak": leak, "sample": sample[:90]}, ensure_ascii=False))


def run_mode(mode: str) -> dict:
    env = {**os.environ, "_OBS_CHILD": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", None)
    if mode:
        env["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = mode
    out = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, encoding="utf-8")
    last = [ln for ln in out.stdout.splitlines() if ln.startswith("{")]
    if not last:
        print(out.stdout[-1500:], out.stderr[-1500:])
        raise SystemExit(1)
    return json.loads(last[-1])


RESULTS: dict[str, dict] = {}


def results() -> dict[str, dict]:
    if not RESULTS:
        for m in MODES:
            RESULTS[m] = run_mode(m)
    return RESULTS


def modes() -> None:
    section("modes: 캡처 모드별로 span에 붙는 내용 속성")
    for m, r in results().items():
        label = m or "(설정 안 함)"
        print(f"  {label:<15} → {', '.join(k.replace('gen_ai.', '') for k in r['found']) or '내용 없음 (메타데이터만)'}")
    print("\n  기본값(비움 = NO_CONTENT): 모델·토큰·도구 이름만 남고 대화 내용은 남지 않는다")
    print("  EVENT_ONLY(true도 같은 뜻): 내용은 span이 아니라 로그 이벤트로만 나간다 (LoggerProvider 필요)")
    sample = results()["SPAN_ONLY"]["sample"]
    print(f"  SPAN_ONLY 예: gen_ai.input.messages = {sample}…")


def pii() -> None:
    section(f"pii: 사용자가 학번({PII})을 입력했을 때 span으로 새는가?")
    for m, r in results().items():
        label = m or "(설정 안 함)"
        status = f"유출 ✗ ({', '.join(sorted(set(r['leak'])))})" if r["leak"] else "안전 ✓"
        print(f"  {label:<15} → {status}")
    print("\n  운영 원칙: 기본은 NO_CONTENT. 내용이 꼭 필요하면 접근이 통제된 별도 저장소로 보내고")
    print("  입력 단계에서 개인정보를 막는다 (Part 7 콜백 가드레일, Part 14 실습 3단계)")


ITEMS = {"modes": modes, "pii": pii}

if __name__ == "__main__":
    if os.getenv("_OBS_CHILD"):
        child()
        sys.exit(0)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in ITEMS.items():
        if which in (k, "all"):
            fn()
