"""Part 12 관측성 실습 공통 도우미 (모두 LLM 없이 동작).

- install_telemetry · print_span_tree · to_openmetrics · fake_llm은 common/telemetry_util.py에 있다
  (Part 14 실습 7단계도 같은 도구를 쓴다).
- FakeLlm: 대본대로 답하는 '가짜 모델'. BaseLlm을 상속해 실제 모델 자리에 끼우므로
  ADK의 generate_content span · 토큰 지표가 진짜 Gemini를 쓸 때와 똑같이 만들어진다.
  (부록 A의 before_model_callback 방식은 모델 호출을 건너뛰어 이런 span이 생기지 않는다.)
- weather_agent(): get_weather 도구 하나를 가진 실습용 에이전트
- run_turn(): Runner로 한 턴 실행
"""
from __future__ import annotations


from common.telemetry_util import (fake_llm, install_telemetry, iter_metrics,  # noqa: F401
                                   print_span_tree, to_openmetrics, trace_ids)

APP = "obs_lab"
USER = "u1"


# --------------------------------------------------------------------------- 가짜 모델 · 에이전트
def get_weather(city: str) -> dict:
    """도시의 현재 날씨를 돌려준다."""
    table = {"Seoul": ("맑음", 21), "Busan": ("흐림", 19)}
    sky, temp = table.get(city, ("알 수 없음", None))
    if temp is None:
        return {"status": "error", "message": f"{city} 날씨 정보 없음"}
    return {"status": "ok", "city": city, "sky": sky, "temp_c": temp}


def weather_agent(script: list | None = None, **kw):
    from google.adk.agents import LlmAgent
    script = script or [("get_weather", {"city": "Seoul"}), "서울은 맑고 21도입니다."]
    return LlmAgent(name="weather_agent", model=fake_llm(script),
                    instruction="날씨를 물으면 get_weather 도구로 확인해 답한다.",
                    tools=[get_weather], **kw)


async def run_turn(agent, text: str, *, runner=None, plugins=None, show: bool = True) -> str:
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    runner = runner or InMemoryRunner(agent=agent, app_name=APP, plugins=plugins or [])
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    final = ""
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    if show:
        print(f"  [user] {text}")
    async for ev in runner.run_async(user_id=USER, session_id=session.id, new_message=msg):
        if ev.is_final_response() and ev.content and ev.content.parts:
            final = "".join(p.text or "" for p in ev.content.parts)
            if show:
                print(f"  [{ev.author}] {final}")
    return final


def section(title: str) -> None:
    print(f"\n=== {title} ===")
