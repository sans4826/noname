from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import random
import ssl

app = Flask(__name__)

# 네이버 차단 방지용 공통 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.naver.com"
}

@app.route("/", methods=["GET"])
def home():
    return "Server is running."

# 1. 랜덤 숫자 테스트
@app.route("/text", methods=["GET", "POST"])
def text_skill():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": str(random.randint(1, 10))}}]
        }
    }
    return jsonify(response)

# 2. 이미지 테스트
@app.route("/image", methods=["GET", "POST"])
def image_skill():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleImage": {
                    "imageUrl": "https://t1.daumcdn.net/friends/prod/category/M001_friends_ryan2.jpg",
                    "altText": "hello I'm Ryan"
                }
            }]
        }
    }
    return jsonify(response)

# 3. 에코 (발화 그대로 돌려주기)
@app.route("/echo", methods=["POST"])
def echo_skill():
    data = request.get_json(silent=True) or {}
    user_input = data.get("userRequest", {}).get("utterance", "입력값이 없습니다.")
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": user_input}}]}
    })

# 4. [수정됨] 네이버 뉴스 검색 기능
@app.route("/naver-news", methods=["POST"])
def naver_news_skill():
    data = request.get_json(silent=True) or {}
    utterance = data.get("userRequest", {}).get("utterance", "").strip()

    # "뉴스"라는 단어를 제거해서 검색어만 추출 (예: "삼성 뉴스" -> "삼성")
    search_keyword = utterance.replace("뉴스", "").strip()

    if not search_keyword:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "뉴스 뒤에 검색어를 입력해주세요!\n예) 뉴스 경제"}}] }
        })

    query = urllib.parse.quote(search_keyword)
    url = f"https://search.naver.com/search.naver?where=news&query={query}"

    try:
        # requests를 사용하여 차단 방지 헤더 적용
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(".news_tit")

        titles = []
        for item in items[:5]:
            titles.append(item.get_text(strip=True))

        if titles:
            result_text = f"🔎 '{search_keyword}' 관련 뉴스:\n\n"
            result_text += "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        else:
            result_text = f"'{search_keyword}'에 대한 검색 결과를 찾지 못했습니다."

    except Exception as e:
        result_text = f"뉴스 조회 중 오류 발생: {str(e)}"

    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": result_text[:1000]}}]}
    })

# 5. [수정됨] 울산 날씨 크롤링 (requests 방식으로 통일)
@app.route("/ulsan-weather", methods=["GET", "POST"])
def ulsan_weather_skill():
    url = "https://search.naver.com/search.naver?query=%EC%9A%B8%EC%82%B0%20%EB%82%A0%EC%94%A8"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        temps = soup.find("div", class_="temperature_text")
        summary = soup.find("p", class_="summary")

        if temps and summary:
            # "현재 온도" 같은 불필요한 텍스트 정리
            temp_val = temps.get_text(strip=True).replace("현재 온도", "")
            result_text = f"☁️ 울산 현재 날씨: {temp_val}\n💬 {summary.get_text(strip=True)}"
        else:
            result_text = "날씨 정보를 찾을 수 없습니다."

    except Exception as e:
        result_text = f"날씨 조회 오류: {str(e)}"

    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": result_text}}]}
    })

if __name__ == "__main__":
    # Render 배포를 위해 PORT 환경변수 대응
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
