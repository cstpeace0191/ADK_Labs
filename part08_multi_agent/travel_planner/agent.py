"""강의노트 Part 8 슬라이드 94~95: ADK 2.0 협업 모드 — coordinator + single_turn / task 서브에이전트.

mode        | 사용자와 대화        | 부모로 복귀
chat (기본) | 가능                 | 수동 transfer
task        | 명확화 질문 가능     | 완료 시 자동 (input/output_schema)
single_turn | 불가                 | 결과와 함께 자동
"""
import os

from google.adk import Agent
from pydantic import BaseModel, Field

MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")


# ── 도구 (목업)
def geocode_address(place: str) -> dict:
    """장소 이름을 위경도로 변환한다."""
    coords = {"제주": (33.49, 126.53), "부산": (35.18, 129.08), "도쿄": (35.68, 139.69)}
    lat, lng = coords.get(place, (37.57, 126.98))
    return {"status": "success", "place": place, "lat": lat, "lng": lng}


def get_weather(lat: float, lng: float, date: str) -> dict:
    """위경도와 날짜(YYYY-MM-DD)로 예보를 조회한다."""
    return {"status": "success", "forecast": "맑음, 최고 21°C" if lat < 35 else "구름 조금, 최고 17°C"}


def search_flights(origin: str, destination: str, date: str) -> dict:
    """항공편을 검색한다."""
    return {"status": "success", "flights": [
        {"flight_no": "KE1201", "time": "08:00", "price": 98000, "seats": ["window", "aisle"]},
        {"flight_no": "OZ8915", "time": "13:30", "price": 76000, "seats": ["aisle"]},
    ]}


def book_flight(flight_no: str, seat: str) -> dict:
    """항공편을 예약한다. seat 는 window 또는 aisle."""
    return {"status": "success", "booking_id": f"BK-{flight_no}-{seat[:1].upper()}"}


# ── 구조화 입출력 계약
class FlightInput(BaseModel):
    origin: str = Field(description="출발 도시")
    destination: str = Field(description="도착 도시")
    date: str = Field(description="YYYY-MM-DD")


class FlightResult(BaseModel):
    booking_id: str
    flight_no: str
    seat: str


weather_agent = Agent(
    name="weather_checker",
    model=MODEL,
    mode="single_turn",  # 사용자 대화 없음, 결과만 반환
    description="여행지와 날짜의 날씨를 조회한다.",
    instruction="geocode_address 로 좌표를 구한 뒤 get_weather 로 예보를 조회해 한 줄로 요약하라.",
    tools=[get_weather, geocode_address],
)

flight_agent = Agent(
    name="flight_booker",
    model=MODEL,
    mode="task",  # 필요하면 사용자에게 질문 (예: 좌석 선호)
    description="항공편을 검색하고 예약한다.",
    instruction="search_flights 로 검색하고, 좌석 선호(window/aisle)를 모르면 사용자에게 물어본 뒤 "
                "book_flight 로 예약하라.",
    input_schema=FlightInput,
    output_schema=FlightResult,
    tools=[search_flights, book_flight],
)

root_agent = Agent(
    name="travel_planner",  # coordinator (mode 지정 안 함 = chat)
    model=MODEL,
    instruction="여행 계획을 돕는다. 날씨는 weather_checker, 항공권은 flight_booker 에게 맡기고 "
                "결과를 모아 일정 요약을 제공하라. 출발지는 기본 서울.",
    sub_agents=[weather_agent, flight_agent],
)
