# Google ADK `Event` 객체 구조 및 역할 가이드

`direct-adk-simple-async.py`와 같이 `runner.run_async()` 또는 `runner.run()`을 실행할 때 반환되는 스트림 요소인 **`Event` 객체**에 대한 상세 설명서입니다.

`Event`는 Google ADK에서 에이전트 실행 주기 동안 발생하는 대화 기록 및 상태 전이의 기본 단위이며, 세션 저장소(`session.events`)에 영구 기록되는 데이터 모델입니다. 내부적으로 `LlmResponse`(모델 응답)를 상속받아 확장한 구조입니다.

---

## 1. 주요 필드 구성 (google-adk 기준)

### ① 식별 및 추적 메타데이터 (Event 고유 필드)
| 필드명 | 타입 | 설명 및 역할 |
| :--- | :--- | :--- |
| `id` | `str` | 이벤트 고유 식별자 (UUID) |
| `invocation_id` | `str` | 단일 사용자 요청(턴) 단위의 고유 실행 ID. 한 번의 요청에서 발생한 여러 이벤트는 동일한 `invocation_id`를 공유함 |
| `author` | `str` | 이벤트를 생성한 주체 (`"user"` 또는 에이전트 이름, 예: `"memory_assistant"`) |
| `timestamp` | `float` | 이벤트가 생성된 시각 (Unix epoch 초 단위) |
| `branch` | `str \| None` | 멀티 에이전트 또는 서브 에이전트 실행 시의 계층 경로 (예: `"root.sub"`) |

### ② 메시지 본문: `content` (`types.Content`)
모델의 응답 또는 사용자의 입력 본문이 담기는 핵심 영역입니다.
- **`content.role`**: `"model"` 또는 `"user"`
- **`content.parts`**: `types.Part` 객체의 리스트. 각 Part에는 다음 중 하나가 포함됩니다:
  - `part.text`: 모델이 생성한 일반 텍스트 응답
  - `part.function_call`: 모델이 도구를 호출하기 위해 내보낸 요청 정보 (함수명, 인자값)
  - `part.function_response`: 로컬 도구 실행 결과 (함수명, 반환값)
  - `part.thought = True`: 모델의 추론/사고 과정 (Gemini Thinking / Planner 활성화 시)

### ③ 상태 및 제어 부수 효과: `actions` (`EventActions`)
이벤트가 발생하면서 세션이나 워크플로우 제어 흐름에 가한 변경 사항입니다.
| 필드명 | 설명 |
| :--- | :--- |
| `state_delta` | 이번 이벤트로 인해 변경되거나 새로 추가된 세션 State 딕셔너리 (`output_key` 저장 또는 도구 내부의 State 수정값) |
| `artifact_delta` | 파일이나 바이너리 데이터 등 아티팩트의 생성/수정 내역 |
| `transfer_to_agent` | 다른 서브 에이전트로 제어권을 넘길 때 대상 에이전트의 이름 |
| `escalate` | 루프 종료 또는 상위 에이전트로의 제어권 반환/에스컬레이션 신호 |
| `requested_tool_confirmations` | Human-in-the-Loop(HITL) 사용자 승인 대기 요청 |
| `end_of_agent` | 현재 에이전트의 실행이 완료되었음을 알리는 플래그 |

### ④ 모델 응답 세부 정보 (`LlmResponse` 상속 필드)
| 필드명 | 설명 |
| :--- | :--- |
| `partial` | 스트리밍 중간 조각(chunk)인지 여부 (SSE 스트리밍 모드에서 중간 텍스트는 `True`) |
| `turn_complete` | 한 번의 턴이 완료되었는지 여부 |
| `finish_reason` | 모델 생성 종료 사유 (`"STOP"`, `"MAX_TOKENS"`, `"SAFETY"` 등) |
| `usage_metadata` | 토큰 사용량 정보 (`prompt_token_count`, `candidates_token_count`, `total_token_count`) |
| `model_version` | 실제 호출에 사용된 모델의 세부 버전 |
| `grounding_metadata` / `citation_metadata` | 검색 증강(Grounding) 또는 인용 출처 메타데이터 |

---

## 2. 자주 사용하는 헬퍼 메서드

- **`event.is_final_response()` (`bool`)**:
  - 사용자에게 보여줄 최종 텍스트 응답인지 판별합니다.
  - 도구 호출(`function_call`)이나 도구 결과(`function_response`)가 아니고, 스트리밍 중간 조각(`partial=True`)이 아닐 때 `True`를 반환합니다.
- **`event.get_function_calls()`**:
  - 이벤트에 포함된 도구 호출 요청(`function_call`) 목록만 추출합니다.
- **`event.get_function_responses()`**:
  - 이벤트에 포함된 도구 실행 결과(`function_response`) 목록만 추출합니다.

---

## 3. 에이전트 유형별 이벤트 발생 패턴

### 패턴 A: 도구가 없는 단순 LLM 에이전트 (`direct-adk-simple-async.py`)
도구 호출 과정이 없으므로 모델이 생성한 최종 텍스트를 담은 **단 1개의 이벤트**만 반환됩니다.
```text
Event(
  author='memory_assistant',
  content=Content(role='model', parts=[Part(text='The sky is blue because of Rayleigh scattering...')]),
  partial=False,
  finish_reason='STOP',
  usage_metadata=UsageMetadata(prompt_token_count=..., total_token_count=...),
  actions=EventActions(state_delta={})
)
=> is_final_response() == True
```

### 패턴 B: 도구가 있는 에이전트 (Tool Calling Agent)
도구 호출 요청, 도구 실행 결과, 최종 응답까지 단계별로 순차적인 이벤트가 생성됩니다.
```text
① [Event 1] author='agent', function_call('get_weather', {'city': 'Seoul'})
   => is_final_response() == False
② [Event 2] author='agent', function_response('get_weather', {'temp': 18, 'condition': 'Clear'})
   => is_final_response() == False
③ [Event 3] author='agent', text("현재 서울의 날씨는 맑으며 기온은 18°C입니다.")
   => is_final_response() == True
```

---

## 4. 이벤트 모니터링 코드 예시

`print(event)`를 직접 실행하면 방대한 내부 필드가 모두 출력되므로, 다음과 같이 필요한 정보만 필터링하여 출력하는 것을 권장합니다:

```python
async for event in runner.run_async(
    user_id=user_id,
    session_id=session1.id,
    new_message=user_message
):
    kinds = []
    if event.content and event.content.parts:
        for p in event.content.parts:
            if p.text:
                kinds.append(f"text({len(p.text)} chars)")
            if p.function_call:
                kinds.append(f"call:{p.function_call.name}")
            if p.function_response:
                kinds.append(f"result:{p.function_response.name}")
            if getattr(p, "thought", False):
                kinds.append("thought")
                
    tokens = event.usage_metadata.total_token_count if event.usage_metadata else "-"
    print(f"[{event.author}] {kinds} | Final={event.is_final_response()} | StateDelta={event.actions.state_delta} | Tokens={tokens}")

    if event.is_final_response():
        if event.content and event.content.parts:
            final_text = "".join(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
            print("최종 응답:\n", final_text)
```

