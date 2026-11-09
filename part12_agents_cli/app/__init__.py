"""agents-cli 프로젝트의 에이전트 패키지. adk 서버는 이 패키지의 `app`(App) 또는 `root_agent` 를 찾는다."""
from . import agent  # noqa: F401  (adk web/run 이 app.agent.root_agent 를 찾도록)
from .agent import app

__all__ = ["app"]
