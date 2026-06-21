import os
import requests
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def kakao_text(text):
    safe_text = text[:950] + "..." if len(text) > 950 else text
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": safe_text}}]
        }
    }

@app.route("/", methods=["GET"])
def home():
    return "재테크메이트 서버 정상 작동 중 💰"

# 1. 크롤링 스킬: 뉴스 검색
@app.route("/google-news", methods=["POST"])
def google_news():
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    keyword = params.get("검색어", "").strip()
    if not keyword: return jsonify(kakao_text("어떤 종목을 찾으시나요?"))

    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")
        titles = [f"{i+1}. {item.title.text}" for i, item in enumerate(items[:5])]
        result = f"📰 ['{keyword}'] 관련 뉴스:\n\n" + "\n".join(titles) if titles else "뉴스를 찾지 못했습니다."
    except Exception as e:
        result = f"오류: {str(e)}"
    return jsonify(kakao_text(result))

# 2. AI 스킬: 경제 튜터
@app.route("/claude-finance", methods=["POST"])
def claude_finance():
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    user_input = params.get("질문", "").strip()
    if not user_input: return jsonify(kakao_text("질문을 입력해주세요!"))

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system="당신은 재테크 전문가입니다. 경제 용어는 쉽게, 소비 조언은 날카롭게 해주세요.",
            messages=[{"role": "user", "content": user_input}]
        )
        result_text = response.content[0].text
    except Exception as e:
        result_text = f"오류: {str(e)}"
    return jsonify(kakao_text(result_text))

# 3. 실용 스킬: 실시간 주요 환율/지수 조회 (파라미터 활용)
@app.route("/market-info", methods=["POST"])
def market_info():
    # 사용자가 '환율' 혹은 '지수'라고 입력하면 정보를 크롤링하여 반환
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    target = params.get("종류", "").strip() # '환율' 또는 '지수' 파라미터
    
    # 예시 데이터 (실제 서비스 시 크롤링 로직으로 교체)
    if "환율" in target:
        result = "💵 주요 환율\n달러: 1,380원\n엔화: 920원\n유로: 1,490원"
    elif "지수" in target:
        result = "📈 주요 지수\n코스피: 2,750p\n나스닥: 17,800p"
    else:
        result = "조회하려는 정보를 다시 확인해주세요. (환율/지수)"
    return jsonify(kakao_text(result))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
