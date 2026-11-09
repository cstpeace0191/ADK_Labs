"""강의노트 Part 10 슬라이드 105 (두 번째 예): payload + response_schema 를 가진 RequestInput.

- payload        : UI 에 함께 표시할 데이터 (추천 일정)
- response_schema: 기대 응답 형식 '안내' — 형식 강제가 아니므로 받은 값은 코드에서 다시 검증한다
"""
from google.adk import Event, Workflow
from google.adk.events import RequestInput
from pydantic import BaseModel, ValidationError


class Activity(BaseModel):
    name: str
    hours: float


class ActivitiesList(BaseModel):
    city: str
    activities: list[Activity]


class UserFeedback(BaseModel):
    liked: list[str]
    comment: str = ""


def recommend(node_input: str):
    city = node_input.strip() or "서울"
    return ActivitiesList(city=city, activities=[
        Activity(name="고궁 산책", hours=2), Activity(name="시장 먹거리 투어", hours=1.5),
        Activity(name="한강 자전거", hours=2), Activity(name="미술관", hours=1.5)])


async def get_feedback(node_input: ActivitiesList):
    lines = "\n".join(f"- {a.name} ({a.hours}h)" for a in node_input.activities)
    yield RequestInput(
        message=f"추천 일정입니다:\n{lines}\n마음에 드는 항목은?",
        payload=node_input.model_dump(),  # UI에 표시할 데이터
        response_schema=UserFeedback,
    )


def finalize(node_input):
    try:  # response_schema 는 강제가 아니므로 직접 검증
        fb = UserFeedback.model_validate(node_input)
    except ValidationError:
        fb = UserFeedback(liked=[str(node_input)], comment="(자유 형식 응답)")
    return Event(message=f"최종 일정: {', '.join(fb.liked)} / 메모: {fb.comment or '-'}")


root_agent = Workflow(name="feedback", edges=[("START", recommend, get_feedback, finalize)])
