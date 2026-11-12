"""강의노트 Part 11 슬라이드 116: 평가셋(evalset) 생성 — ADK의 EvalSet 스키마로 직접 만든다.

각 케이스 = 사용자 질문 + 기대 도구 궤적(tool_uses) + 기대 최종 응답.
실행: python make_evalset.py   →  weather_agent/weather.evalset.json
(adk run weather_agent --save_session 으로 저장한 실제 세션을 adk web Eval 탭에서 평가셋으로 추가해도 된다.)
"""
from pathlib import Path

from google.adk.evaluation.eval_case import EvalCase, IntermediateData, Invocation
from google.adk.evaluation.eval_set import EvalSet
from google.genai import types

CASES = [
    ("seoul", "서울 날씨 알려줘", "서울", "서울은 맑음, 18°C입니다."),
    ("busan", "부산 날씨는 어때?", "부산", "부산은 흐림, 20°C입니다."),
    ("unknown", "제주 날씨?", "제주", "제주의 날씨 정보는 없습니다."),
]


def text(role: str, t: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part(text=t)])


def build() -> EvalSet:
    cases = []
    for cid, question, city, answer in CASES:
        inv = Invocation(
            invocation_id=f"inv-{cid}",
            user_content=text("user", question),
            final_response=text("model", answer),
            intermediate_data=IntermediateData(
                tool_uses=[types.FunctionCall(name="get_weather", args={"city": city})]),
        )
        cases.append(EvalCase(eval_id=cid, conversation=[inv],
                              session_input={"app_name": "weather_agent", "user_id": "eval_user", "state": {}}))
    return EvalSet(eval_set_id="weather", name="weather", description="날씨 에이전트 회귀 테스트",
                   eval_cases=cases)


if __name__ == "__main__":
    out = Path(__file__).parent / "weather_agent" / "weather.evalset.json"
    out.write_text(build().model_dump_json(indent=2, exclude_none=True, by_alias=True), encoding="utf-8")
    print("written:", out)
