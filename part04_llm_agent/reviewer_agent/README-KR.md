# reviewer_agent — 구조화 출력 코드 리뷰어 에이전트

Pydantic 모델을 활용하여 모델의 출력을 특정 JSON 스키마로 강제하고, 그 결과를 세션 State에 자동 저장하는 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **구조화 스키마 (`output_schema`)**:
  ```python
  class Review(BaseModel):
      score: int = Field(description="1~5점")
      summary: str
      risks: list[str]

  root_agent = Agent(
      name="code_reviewer",
      output_schema=Review,  # 응답 스키마 강제
      output_key="review",   # 결과를 session.state["review"]에 저장
  )
  ```
  LLM 응답이 일반 텍스트 대신 `Review` Pydantic 모델 검증을 통과한 JSON으로 생성되며, Runner가 세션 상태의 `state['review']`에 자동으로 딕셔너리로 저장합니다.

---

## 2. 실행 방법

`part04_llm_agent` 폴더에서 실행합니다:

```bash
cd part04_llm_agent
uv run run_with_runner.py reviewer
```

### 기대 출력 예시
```text
state['review'] = {'risks': ['0으로 나누는 경우 ZeroDivisionError 발생 가능'], 'score': 3, 'summary': '기본적인 나눗셈 함수이지만 예외 처리가 부족합니다.'}
```


