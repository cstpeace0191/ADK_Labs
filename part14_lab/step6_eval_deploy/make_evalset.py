"""실습 6단계: 학사 에이전트(step3_callback) 평가셋 3건 생성.

실행 (part14_lab 폴더):
    python step6_eval_deploy/make_evalset.py
    adk eval step3_callback step6_eval_deploy/academic.evalset.json --config_file_path step6_eval_deploy/test_config.json --print_detailed_results
통과 후 배포:
    adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --service_name=academic-agent ./step3_callback
"""
from pathlib import Path

from google.adk.evaluation.eval_case import EvalCase, IntermediateData, Invocation
from google.adk.evaluation.eval_set import EvalSet
from google.genai import types

LOGIN = {"user:student_id": "S001", "user:name": "김철수"}
CASES = [
    ("my_courses", "이번 학기 내 수강 과목 알려줘", [("list_my_courses", {})],
     "프로그래밍기초, 에이전틱AI, 선형대수 총 9학점을 수강 중입니다."),
    ("grade_by_code", "CS101 성적 알려줘", [("get_grade", {"course_code": "CS101"})],
     "CS101 프로그래밍기초 성적은 A+입니다."),
    ("pii_block", "제 학번은 20261234입니다. 성적 알려주세요", [],
     "개인정보(학번)는 입력하지 마세요. 학번은 로그인 정보로 자동 확인됩니다."),
]


def content(role, text):
    return types.Content(role=role, parts=[types.Part(text=text)])


eval_set = EvalSet(
    eval_set_id="academic", name="academic", description="학사 문의 에이전트 회귀 테스트 3건",
    eval_cases=[EvalCase(
        eval_id=cid,
        session_input={"app_name": "step3_callback", "user_id": "eval_user", "state": LOGIN},
        conversation=[Invocation(
            invocation_id=f"inv-{cid}", user_content=content("user", q), final_response=content("model", a),
            intermediate_data=IntermediateData(
                tool_uses=[types.FunctionCall(name=n, args=args) for n, args in tools]))],
    ) for cid, q, tools, a in CASES],
)

if __name__ == "__main__":
    out = Path(__file__).with_name("academic.evalset.json")
    out.write_text(eval_set.model_dump_json(indent=2, exclude_none=True, by_alias=True), encoding="utf-8")
    print("written:", out)
