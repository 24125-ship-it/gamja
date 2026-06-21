import os
import random
import requests
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import anthropic  # OpenAI 대신 anthropic 사용
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Anthropic 클라이언트 초기화 (환경변수 ANTHROPIC_API_KEY 사용)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def kakao_text(text):
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
    return "Server is running (Claude Version)."

# [수정] Claude API 연동 스킬
@app.route("/claude-chat", methods=["POST"])
def claude_chat():
    data = request.get_json(silent=True) or {}
    tt = data.get("action", {}).get("params", {}).get("파라미터", "").strip()

    if not tt:
        return jsonify(kakao_text("질문을 입력해주세요."))

    if not os.getenv("ANTHROPIC_API_KEY"):
        return jsonify(kakao_text("API 키가 설정되지 않았습니다."))

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307", # 또는 claude-3-5-sonnet-20240620
            max_tokens=500,
            messages=[{"role": "user", "content": tt}]
        )
        result_text = message.content[0].text
    except Exception as e:
        result_text = f"Claude 호출 중 오류: {str(e)}"

    return jsonify(kakao_text(result_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
