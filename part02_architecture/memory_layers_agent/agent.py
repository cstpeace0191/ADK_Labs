"""강의노트 Part 2 슬라이드 25: 이중 계층 메모리 — Session(단기) vs Memory Bank(장기).

| 차원     | Session Service (단기)                     | Memory Service (장기)                          |
|----------|--------------------------------------------|------------------------------------------------|
| 저장 범위 | 활성 대화 스레드와 임시 상태               | 세션을 넘는 영속 사실·지식                     |
| 데이터   | 메시지 이력, 도구 호출, State 변수         | 정리된 사용자 선호·기록                         |
| 생명주기 | 대화 스레드 종료와 함께 소멸               | 세션 간 영구 보존                              |
| 구현     | InMemory · Database · VertexAiSession      | InMemoryMemoryService · VertexAiMemoryBankService |
| 읽는 방법 | event 이력, {key} 템플릿, tool_context.state | load_memory / preload_memory 도구            |

이 에이전트는 표의 '읽는 방법' 두 열을 모두 쓴다.
  - 단기: instruction 의 {user:name?} · {trip?} 템플릿, 도구 안의 tool_context.state
  - 장기: preload_memory(매 턴 자동 검색) · load_memory(모델이 필요할 때 검색)
실행: python run_memory_layers.py   (또는 adk web 에서 memory_layers_agent 선택)
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools import ToolContext, load_memory, preload_memory

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
else:
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    os.environ.pop("GOOGLE_CLOUD_LOCATION", None)


def save_profile(name: str, tool_context: ToolContext) -> dict:
    """사용자 이름을 기억한다. user: 접두사 → 같은 사용자의 다른 세션에서도 보인다.

    Args:
        name: 사용자 이름
    """
    tool_context.state["user:name"] = name
    return {"status": "success", "saved": {"user:name": name}}


def save_trip(trip: str, tool_context: ToolContext) -> dict:
    """이번 대화에서 언급한 출장·여행 계획을 세션 State 에 적는다 (접두사 없음 → 이 세션에서만).

    Args:
        trip: 계획 요약 (예: "다음 주 화요일 부산 출장")
    """
    tool_context.state["trip"] = trip
    return {"status": "success", "saved": {"trip": trip}}


root_agent = Agent(
    name="memory_layers_agent",
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    description="Session(단기) State 와 Memory(장기) 검색을 함께 쓰는 비서",
    instruction="""
    너는 개인 비서다.
    [단기: 이번 세션 State]
      사용자 이름: {user:name?}
      이번 세션의 계획: {trip?}
    규칙
    1) 사용자가 이름을 말하면 save_profile, 출장·여행 계획을 말하면 save_trip 을 호출한다.
    2) 이번 세션 State 에 없는 과거 정보(음식 취향, 지난 대화의 계획 등)는
       자동으로 제공되는 과거 기억을 먼저 보고, 부족하면 load_memory 로 검색한다.
       load_memory 검색어는 조사를 붙이지 않은 핵심 단어 하나씩 쓴다 (예: "매운", "부산", "출장").
    3) 기억에도 없으면 모른다고 말한다. 지어내지 않는다.
    4) 답은 2~3문장으로 한다.
    """,
    tools=[save_profile, save_trip, preload_memory, load_memory],
)
