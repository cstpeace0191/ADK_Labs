"""야외 활동 판단 (결정론적 코드: 같은 입력이면 항상 같은 결과).

사용: python outdoor_rule.py --condition 맑음 --temp 18
출력: {"condition": "맑음", "temp": 18.0, "verdict": "가능", "reason": "..."}
"""
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--condition", required=True)
parser.add_argument("--temp", required=True)
a = parser.parse_args()

temp = float(str(a.temp).replace("°C", "").strip())
if temp >= 33:
    verdict, reason = "불가", "폭염(33°C 이상)"
elif temp <= -10:
    verdict, reason = "불가", "한파(-10°C 이하)"
elif any(w in a.condition for w in ("비", "눈", "뇌우")):
    verdict, reason = "불가", f"강수({a.condition})"
elif "흐림" in a.condition:
    verdict, reason = "주의", "흐림"
elif any(w in a.condition for w in ("맑음", "구름 조금")):
    verdict, reason = "가능", a.condition
else:
    verdict, reason = "판단 보류", f"기준에 없는 날씨({a.condition})"

print(json.dumps({"condition": a.condition, "temp": temp, "verdict": verdict, "reason": reason},
                 ensure_ascii=False))
