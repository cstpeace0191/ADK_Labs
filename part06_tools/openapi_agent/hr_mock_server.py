"""hr_api.yaml 스펙을 구현한 로컬 목업 서버.

실행 (part06_tools 폴더):  python openapi_agent/hr_mock_server.py
"""
import os

import uvicorn
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="HR mock")
EMPLOYEES = {"E1001": ("김철수", 11.5), "E1002": ("이영희", 3.0)}
API_KEY = os.getenv("HR_API_KEY", "demo-hr-key")


@app.get("/employees/{employee_id}/leave-balance")
def leave_balance(employee_id: str, x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "invalid api key")
    if employee_id not in EMPLOYEES:
        raise HTTPException(404, "not found")
    name, days = EMPLOYEES[employee_id]
    return {"employee_id": employee_id, "name": name, "remaining_days": days}


@app.get("/holidays")
def holidays():
    return [{"date": "2026-12-25", "name": "성탄절"}, {"date": "2026-12-31", "name": "창립기념일"}]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8077)
