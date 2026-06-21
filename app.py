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

# 1. 파라미터 확인용 스킬
@app.route("/params-check", methods=["POST"])
def params_check():
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    text = f"전달받은 파라미터:\n{params}"
    return jsonify(kakao_text(text))

# 2. 크롤링 스킬 (범용성 강화)
@app.route("/google-news", methods=["POST"])
def google_news():
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    # 사용자가 말한 단어를 '검색어' 파라미터로 받음
    keyword = params.get("검색어", "").strip()

    if not keyword:
        return jsonify(kakao_text("어떤 종목이나 경제 키워드를 찾으시나요? (예: 테슬라 뉴스)"))

    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")
        titles = [f"{i+1}. {item.title.text}" for i, item in enumerate(items[:5])]
        
        if titles:
            result = f"📰 ['{keyword}'] 관련 뉴스:\n\n" + "\n".join(titles)
        else:
            result = f"['{keyword}']에 대한 뉴스를 찾지 못했습니다."
    except Exception as e:
        result = f"오류 발생: {str(e)}"
    return jsonify(kakao_text(result))

# 3. AI 경제 튜터 스킬
@app.route("/claude-finance", methods=["POST"])
def claude_finance():
    data = request.get_json(silent=True) or {}
    params = data.get("action", {}).get("params", {})
    user_input = params.get("질문", "").strip()

    if not user_input:
        return jsonify(kakao_text("궁금한 경제 용어나 고민을 말씀해주세요!"))

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system="당신은 냉철한 재테크 전문가입니다. 경제 용어는 쉽게 설명하고, 소비 고민은 뼈 때리는 조언을 해주세요.",
            messages=[{"role": "user", "content": user_input}]
        )
        result_text = response.content[0].text
    except Exception as e:
        result_text = f"AI 분석 오류: {str(e)}"
    return jsonify(kakao_text(result_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
