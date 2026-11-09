"""강의노트 Part 11 슬라이드 121: Agent Runtime 은 gcloud run deploy 가 아니라 ADK CLI · agents-cli · Python SDK 로 올린다.

이 스크립트는 세 번째 길(Python SDK, google-cloud-aiplatform)을 보여 준다.
  기본(dry-run, 🟢 키·GCP 불필요): 로컬에서 AdkApp 을 만들어 보고, 배포 설정만 출력한다.
  --deploy (GCP 필요)          : client.agent_engines.create(...) 로 실제 배포한다.

실행 (part11_eval_deploy 폴더에서):
  python deploy/deploy_agent_runtime_sdk.py
  GOOGLE_CLOUD_PROJECT=<id> GOOGLE_CLOUD_LOCATION=us-central1 STAGING_BUCKET=gs://<bucket> \\
      python deploy/deploy_agent_runtime_sdk.py --deploy

같은 일을 CLI 로:  adk deploy agent_engine --project=... --region=... --display_name=weather-agent ./weather_agent
                    (deploy_agent_runtime.sh runtime)

참고: Google Cloud 문서의 client.runtimes.create 는 Dockerfile(image_spec)·컨테이너 이미지(container_spec)도 받는다
      (google-cloud-aiplatform ≥ 1.144, 이미지는 Agent Runtime 런타임 계약을 따라야 함). gcloud 로 만든 이미지를
      Agent Runtime 에 올리려면 이 경로를 쓴다 — gcloud run deploy 는 Cloud Run 서비스만 만든다.
"""
import argparse
import os
import sys
from pathlib import Path

PART10 = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PART10.parent), str(PART10)]
import common.bootstrap  # noqa: E402,F401  (.env, 콘솔 UTF-8)

REQUIREMENTS = ["google-cloud-aiplatform[agent_engines,adk]"]


def sdk_info() -> tuple[str, bool]:
    from importlib.metadata import version
    v = version("google-cloud-aiplatform")
    major, minor = (int(x) for x in v.split(".")[:2])
    return v, (major, minor) >= (1, 144)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true", help="실제로 Agent Runtime 에 배포 (GCP 필요)")
    args = ap.parse_args()

    from vertexai.agent_engines import AdkApp
    from weather_agent.agent import root_agent

    app = AdkApp(agent=root_agent)             # 에이전트를 Agent Runtime 실행 단위로 감싼다
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "<project-id>")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    bucket = os.getenv("STAGING_BUCKET", "gs://<staging-bucket>")
    config = {
        "requirements": REQUIREMENTS,
        "staging_bucket": bucket,
        "display_name": "weather-agent",
        "description": "ADK_Labs part11 weather_agent (SDK 배포)",
    }

    v, has_runtimes = sdk_info()
    print(f"google-cloud-aiplatform {v}")
    print(f"  AdkApp(agent={root_agent.name}) 생성: {type(app).__name__}")
    print(f"  client = vertexai.Client(project={project!r}, location={location!r})")
    print("  client.agent_engines.create(agent=app, config={")
    for k, val in config.items():
        print(f"      {k!r}: {val!r},")
    print("  })")
    print(f"  Dockerfile(image_spec) · 이미지(container_spec) 배포: "
          f"{'이 SDK 에서 client.runtimes.create 로 가능' if has_runtimes else '≥ 1.144 필요 (현재 버전에는 없음)'}")
    print("  배포 후 상태: 플랫폼이 서버를 호스팅하고 관리형 세션(VertexAiSessionService)·Memory Bank 를 붙인다")

    if not args.deploy:
        print("\n(dry-run) --deploy 를 주면 실제로 배포한다.")
        return
    for name in ("GOOGLE_CLOUD_PROJECT", "STAGING_BUCKET"):
        if not os.getenv(name):
            sys.exit(f"{name} 환경변수가 필요합니다.")

    import vertexai
    client = vertexai.Client(project=project, location=location)
    remote = client.agent_engines.create(agent=app, config=config)
    name = remote.api_resource.name
    print(f"\n배포 완료: {name}")
    print(f"호출 URL: https://{location}-aiplatform.googleapis.com/v1/{name}:query")


if __name__ == "__main__":
    main()
