# part13_lab — 종합 실습: 학사 문의 AI 에이전트 단계별 개발

> 강의노트 **Part 13 · 13. 실습과 종합** (슬라이드 139 "실습: 학사 문의 에이전트를 단계별로 키우기")과 짝을 이룬다.

강의에서 배운 모든 ADK 기능(기본 LLM → 도구 연동 → 가드레일 → 워크플로우 → HITL/재시도 → 평가)을 하나의 학사 문의 시스템으로 완성해가는 1~6단계 점진적 개발 프로젝트입니다.

---

## 1. 단계별 폴더 구성

```text
part13_lab/
├── step1_basic/         # 1단계: 기본 학사 안내 LLM 에이전트
├── step2_tools/         # 2단계: 학생 학사 데이터베이스(성적/수강) 조회 도구 연동
├── step3_callback/      # 3단계: 개인정보(주민등록번호 등) 입력 차단 가드레일 콜백
├── step4_workflow/      # 4단계: 질의 유형별 자동 라우팅 그래프 워크플로우 (🟢 오프라인)
├── step5_hitl_retry/    # 5단계: 성적 정정 신청 HITL 승인 게이트 및 일시적 장애 재시도 (🟢 오프라인)
├── step6_eval_deploy/   # 6단계: academic.evalset.json 기반 adk eval 품질 평가
├── run_lab.py           # 각 단계별 통합 실행 러너 스크립트
└── README-KR.md            # 현재 문서
```

---

## 2. 단계별 학습 목표

| 단계 | 주요 구현 내용 | 실행 명령 (part13_lab 폴더) |
|---|---|---|
| **Step 1** | 기본 에이전트 지시문 및 모델 설정 | `uv run run_lab.py 1` (🔑) |
| **Step 2** | `get_grades`, `get_courses` 파이썬 도구 연동 | `uv run run_lab.py 2` (🔑) |
| **Step 3** | `before_model_callback`으로 주민번호 PII 유출 차단 | `uv run run_lab.py 3` (🔑) |
| **Step 4** | 학사 규정 / 성적 / 수강 조회 분기 그래프 | `uv run run_lab.py 4` (🟢) |
| **Step 5** | 성적 정정 요청 시 교수/담당자 승인 HITL 게이트 | `uv run run_lab.py 5` (🟢) |
| **Step 6** | `academic.evalset.json` 벤치마크 평가 | `adk eval step3_callback step6_eval_deploy/academic.evalset.json ...` |

---

## 3. 실행 방법

`part13_lab` 폴더에서 실행합니다:

```bash
cd part13_lab

# 1~5단계 전체 순차 실행
uv run run_lab.py all

# 특정 단계만 실행
uv run run_lab.py 1
uv run run_lab.py 4   # 🟢 오프라인 실행 가능
uv run run_lab.py 5   # 🟢 오프라인 실행 가능

# 6단계: adk eval 품질 벤치마크 평가 실행 (3건 평가)
adk eval step3_callback step6_eval_deploy/academic.evalset.json --config_file_path step6_eval_deploy/test_config.json

# 웹 개발 UI 실행
adk web --port 8000
```



