import os
import requests
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import anthropic
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

app = Flask(__name__)

# Anthropic(Claude) 클라이언트 초기화
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def kakao_text(text):
    """카카오톡 텍스트 응답 규격 생성 (1000자 제한 안전장치)"""
    safe_text = text[:950] + "..." if len(text) > 950 else text
    return {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": safe_text
                }
            }]
        }
    }

@app.route("/", methods=["GET"])
def home():
    return "재테크메이트 (Claude Version) is running 💰"

# 1. 파라미터 확인용 스킬 (블록 10 연결용)
@app.route("/params-check", methods=["POST"])
def params_check():
    data = request.get_json(silent=True) or {}
    user_request = data.get("userRequest", {})
    action = data.get("action", {})
    params = action.get("params", {})

    b = user_request.get("utterance", "입력된 발화 없음")
    c = params.get("종목명", "종목명 파라미터 없음")
    d = params.get("질문", "질문 파라미터 없음")

    text = f"🗣️ 사용자 발화: {b}\n📈 인식된 종목: {c}\n❓ 인식된 질문: {d}"
    return jsonify(kakao_text(text))

# 2. 구글 뉴스 크롤링 스킬 (블록 6 연결용 - 관심 종목 뉴스)
@app.route("/google-news", methods=["POST"])
def google_news():
    data = request.get_json(silent=True) or {}
    company = data.get("action", {}).get("params", {}).get("종목명", "").strip()

    if not company:
        return jsonify(kakao_text("어떤 종목의 뉴스를 찾으시나요? 종목명을 정확히 입력해 주세요. (예: 삼성전자 뉴스)"))

    query = urllib.parse.quote(company)
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")

        titles = []
        for item in items[:5]:
            title = item.title.text
            if title:
                titles.append(title)

        if titles:
            result = f"📰 ['{company}'] 최신 주가/경제 뉴스:\n\n" + "\n\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        else:
            result = f"['{company}']에 대한 최신 뉴스를 찾지 못했습니다."
            
    except Exception as e:
        result = f"뉴스 조회 중 오류 발생: {str(e)}"

    return jsonify(kakao_text(result))

# 3. Claude AI 경제 선생님 스킬 (블록 11, 12, 13 연결용)
@app.route("/claude-finance", methods=["POST"])
def claude_finance():
    data = request.get_json(silent=True) or {}
    user_input = data.get("action", {}).get("params", {}).get("질문", "").strip()

    if not user_input:
        return jsonify(kakao_text("경제 용어를 물어보시거나, 오늘의 소비 내역을 고백해 보세요!"))

    if not os.getenv("ANTHROPIC_API_KEY"):
        return jsonify(kakao_text("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다."))

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.7,
            system="당신은 냉철하고 똑똑한 재테크 전문가이자 경제 선생님입니다. 사용자가 경제 용어를 물어보면 초등학생도 이해할 수 있게 비유해서 설명하고, 돈을 썼다거나 과소비를 했다고 하면 뼈 때리는 조언(팩트폭력)을 짧고 굵게 해주세요. 답변은 모바일 메신저에 맞게 간결하고 가독성 좋게 작성하세요.",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )
        result_text = response.content[0].text
        
    except Exception as e:
        result_text = f"AI 분석 중 오류 발생: {str(e)}"

    return jsonify(kakao_text(result_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
