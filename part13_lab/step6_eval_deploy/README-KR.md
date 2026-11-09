# step6_eval_deploy — 6단계: 학사 에이전트 품질 평가 벤치마크

개발된 학사 에이전트의 응답 품질과 도구 호출 정확도를 골든 데이터셋(`academic.evalset.json`)을 통해 검증하는 평가 리소스 모음입니다.

---

## 1. 파일 구성

- `academic.evalset.json`:
  - 학사 문의 대표 질문 3종(성적 조회, 수강 과목 조회, 개인정보 유출 방지 질의)과 각 질의별 기대 출력
- `test_config.json`:
  - ROUGE-1 점수 및 도구 궤적 일치 여부를 측정하기 위한 평가 지표 설정
- `make_evalset.py`:
  - 대화 세션 로그로부터 평가용 데이터셋을 자동 추출/생성하는 유틸리티

---

## 2. 평가 실행 방법

`part13_lab` 상위 폴더에서 실행합니다:

```bash
cd part13_lab
adk eval step3_callback step6_eval_deploy/academic.evalset.json --config_file_path step6_eval_deploy/test_config.json
```

### 기대 출력 예시
```text
Evaluation Results:
  Total test cases: 3
  Tests passed: 3
  Tests failed: 0
```

