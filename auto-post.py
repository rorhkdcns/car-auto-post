import base64
import datetime
import html
import json
import os
import pickle
import random
import re
import subprocess
import sys
import time
import urllib.parse
import warnings

# [추가] 보기 싫은 구글 API 파이썬 버전 경고문 강제 차단
warnings.filterwarnings("ignore", category=FutureWarning)

# [1단계] 라이브러리 자동 설치 및 검증
required_modules = [
    "google-auth-oauthlib", 
    "google-auth-httplib2", 
    "google-api-python-client", 
    "google-genai"  
]

print("🔄 깃허브 액션 서버 환경 내 라이브러리 자동 설치 시작...")
for module in required_modules:
    try:
        if module == "google-genai":
            import google.genai
        else:
            __import__(module.replace('-', '_'))
    except ImportError:
        print(f"📦 {module} 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", module])
        time.sleep(1)

print("✅ 모든 라이브러리 설치 및 인식 완료! 본 코드를 시작합니다.")
print("-" * 60)

from googleapiclient.discovery import build
from google import genai 
from google.genai import types  

# =====================================================================
# ⚙️ 고유 설정 정보 【★ 아래 3개는 형이 직접 채워야 함 ★】
# =====================================================================
BLOG_ID = "8172138309834961611"
CAR_TEST_URL = "https://car.gwangchoon.com/2026/07/car-test.html"
GOOGLE_ADSENSE_SLOT = "5317754949"

GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157"

CAR_KEYWORDS = [
    # ── 구매/계약 ──
    "신차 구매 절차", "신차 출고 대기기간", "자동차 계약금 환불", "신차 할인 시기", 
    "자동차 리스 장단점", "장기렌트 리스 차이", "자동차 할부 금리", "잔가보장 리스란", 
    "신차 검수 체크리스트", "탁송 직접출고 차이", "자동차 구매 부대비용", "취등록세 계산", 
    "자동차 채권 환급", "전기차 보조금 신청", "하이브리드 세제혜택", "경차 혜택 총정리", 
    "다자녀 자동차 혜택", "법인차 번호판 기준", "자동차 개소세 기준", "신차 잔가율 높은 차", 
    # ── 중고차 ──
    "중고차 살때 확인사항", "성능점검기록부 보는법", "침수차 구별법", "사고차 확인 방법", 
    "중고차 감가율", "중고차 허위매물 피하는법", "중고차 이전등록 방법", "리스 승계란", 
    "중고 전기차 배터리 확인", "인증중고차 장단점", "내차 비싸게 파는법", "중고차 시세 조회", 
    "주행거리 조작 확인", "중고차 계약서 주의사항", "중고차 보증보험", "단기렌트카 비교", 
    # ── 유지/정비 ──
    "엔진오일 교환주기", "타이어 교체시기", "타이어 위치교환 주기", "브레이크패드 교환주기", 
    "냉각수 보충 방법", "와이퍼 교체 방법", "배터리 방전 대처법", "점프스타트 하는법", 
    "에어컨필터 교체주기", "미션오일 교환주기", "겨울철 차량관리", "여름철 차량관리", 
    "장마철 차량관리", "차유리 김서림 제거", "엔진경고등 원인", "타이어 적정 공기압", 
    "셀프세차 순서", "차량 실내 냄새 제거", "블랙박스 방전 예방", "자동차 잔기스 제거", 
    "하부세차 필요성", "유리막코팅 광택 차이", "썬팅 농도 추천", "휠얼라인먼트 증상", 
    "엔진 떨림 원인", "냉각수 온도 경고등", "머플러 물 떨어짐", "시동 안걸릴때 원인", 
    # ── 보험/세금/법규 ──
    "자동차보험 싸게 드는법", "자동차보험 특약 추천", "운전자보험 필요성", "자차 자기부담금", 
    "보험 할증 기준", "대물 한도 추천", "자동차세 연납 할인", "자동차세 계산 방법", 
    "과태료 범칙금 차이", "신호위반 벌점 기준", "속도위반 과태료 조회", "주정차위반 과태료", 
    "어린이보호구역 과태료", "자동차 검사 주기", "종합검사 정기검사 차이", "검사 지연 과태료", 
    "번호판 교체 방법", "자동차 명의이전 서류", "폐차 절차 보상금", "자동차 압류 확인", 
    # ── 운전/실전 ──
    "초보운전 연수 꿀팁", "주차 잘하는법", "평행주차 요령", "고속도로 운전 요령", 
    "빗길 운전 요령", "눈길 운전 체인", "블랙아이스 대처법", "졸음운전 예방법", 
    "연비 높이는 운전법", "하이패스 등록 방법", "통행료 미납 조회", "긴급출동 서비스 비교", 
    "타이어 펑크 대처법", "접촉사고 대처 순서", "사고 과실비율 기준", "보험사 사고접수 방법", 
    "주차장 문콕 대처", "대리운전 보험 확인", "차량 침수시 대처", "터널 사고 대처법", 
    # ── 차종/트렌드 ──
    "전기차 장단점 현실", "전기차 충전요금 비교", "완속 급속 충전 차이", "아파트 충전기 설치", 
    "하이브리드 장단점", "LPG차 장단점", "요소수 보충 방법", "경차 유지비 현실", 
    "패밀리카 고르는 기준", "첫차 고르는 기준", "세컨카 조건", "캠핑카 개조 규정", 
    "차박 가능한 차 조건", "SUV 세단 장단점", "수입차 유지비 현실", "신차급 중고차란", 
    "자율주행 레벨 정리", "차량 구독 서비스란", "OTA 업데이트란", "전기차 겨울 주행거리", 
    # ── 용품/편의 ──
    "블랙박스 고르는 기준", "차량용 공기청정기 효과", "카시트 의무 기준", "카시트 설치 방법", 
    "차량용 소화기 의무화", "겨울 차량용품 필수", "차량 무선충전 발열", "HUD 종류 비교", 
    "타이어 공기주입기 사용법", "차량용 냉장고 전력"
]

# 【핵심】 계산기 모음판 → 자동차 추천 테스트 유도 박스로 교체
CAR_TEST_BOARD_CODE = f"""
<div id="car-test-top" class="car-test-board" style="margin: 35px 0; padding: 26px 20px; background: linear-gradient(135deg, #16337F, #2B5CE6); border-radius: 14px; text-align: center;">
    <p style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700; color: #BBD0FF; letter-spacing: 0.08em;">CAR MATCH TEST</p>
    <p style="margin: 0 0 14px 0; font-size: 20px; font-weight: 800; color: #ffffff; line-height:1.4;">🚗 나에게 딱 맞는 차는 뭘까?</p>
    <p style="margin: 0 0 18px 0; font-size: 16px; color: #DDE7FF; line-height: 1.7;">
        15가지 질문으로 예산·가족·라이프스타일을 분석해<br>
        150여 종 차량 중 <b>내게 맞는 TOP 5</b>를 찾아드립니다.
    </p>
    <a href="{CAR_TEST_URL}" style="display: inline-block; background: #ffffff; color: #16337F; font-weight: 800; font-size: 16px; padding: 13px 32px; border-radius: 10px; text-decoration: none;">⚡ 2분 자동차 테스트 시작</a>
</div>
"""

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

CTA_CODE = f"""
<div class="cta-box" style="border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; background-color: #f8fafc; margin-top: 40px; text-align: center;">
    <p style="font-size: 17px; color: #334155; font-weight: 700; margin-bottom: 8px; display: inline-block; background: #e2e8f0; padding: 4px 12px; border-radius: 6px;">🚘 카라이프 가이드 안내</p>
    <p style="font-size: 16px; color: #475569; line-height: 1.7; margin: 0 0 15px 0; font-weight: 500;">
        차는 사는 순간보다 타는 동안의 선택이 더 중요합니다.<br>
        지금 다음 차를 고민 중이라면, 본문의 <b>[자동차 맞춤 추천 테스트]</b>로 나에게 맞는 방향부터 잡아보시기 바랍니다.
    </p>
    <a href="#car-test-top" style="display: inline-block; background: #334155; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 16px; transition: background 0.2s;">🚗 자동차 추천 테스트로 이동하기</a>
</div>
"""

# =====================================================================
# 🛠️ 보조 함수들
# =====================================================================
def format_paragraphs(text):
    if not text or not text.strip(): return ""
    
    # 마크다운 볼드체(**)를 HTML 강조 태그로 안전 변환
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:#2563eb;">\1</strong>', text)
    
    processed_chunks = []
    in_table = False
    table_html = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                in_table = True
                table_html = ['<div style="overflow-x:auto; margin: 20px 0;"><table style="width:100%; border-collapse:collapse; border:1px solid #cbd5e1;">']
            if not re.match(r'^\|(?:[\s\-:]+\|)+$', line):
                tds = ''.join([f'<td style="border:1px solid #cbd5e1; padding:10px; font-size:16px;">{c.strip()}</td>' for c in line.split('|')[1:-1]])
                table_html.append(f'<tr>{tds}</tr>')
        else:
            if in_table:
                in_table = False
                table_html.append('</table></div>')
                processed_chunks.append("".join(table_html))
                table_html = []
            processed_chunks.append(f'<p style="margin-bottom:20px; line-height:1.7; font-size:17px; color:#334155;">{line}</p>')
    if in_table:
        table_html.append('</table></div>')
        processed_chunks.append("".join(table_html))
    return "".join(processed_chunks)

# 목차(TOC) 박스 생성
def build_toc_html(sub1, sub2, sub3):
    return f'''
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:20px 24px; margin:25px 0;">
    <p style="font-weight:700; font-size:17px; color:#1e293b; margin:0 0 12px 0;">📋 목차</p>
    <ul style="margin:0; padding-left:20px; font-size:16px; color:#334155; line-height:2;">
        <li><a href="#sec1" style="color:#2563eb; text-decoration:none;">{sub1}</a></li>
        <li><a href="#sec2" style="color:#2563eb; text-decoration:none;">{sub2}</a></li>
        <li><a href="#sec3" style="color:#2563eb; text-decoration:none;">{sub3}</a></li>
        <li><a href="#faq" style="color:#2563eb; text-decoration:none;">자주 묻는 질문</a></li>
        <li><a href="#conclusion" style="color:#2563eb; text-decoration:none;">결론</a></li>
    </ul>
</div>
'''

# 섹션별 "✅ 요약" 박스
def make_section_summary(text):
    if not text or not text.strip(): return ""
    return f'''
<div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:14px 18px; margin:15px 0 30px 0;">
    <p style="margin:0; font-size:16px; color:#1e3a8a; font-weight:700;">✅ 요약</p>
    <p style="margin:6px 0 0 0; font-size:16px; color:#334155; line-height:1.6;">{text}</p>
</div>
'''

# FAQ 섹션
def build_faq_html(faq_list):
    if not faq_list: return ""
    items = ""
    for item in faq_list:
        q = (item.get("question") or "").strip()
        a = (item.get("answer") or "").strip()
        if not q or not a: continue
        items += f'''
        <div style="margin-bottom:18px;">
            <p style="font-weight:700; font-size:17px; color:#1e293b; margin:0 0 6px 0;">Q. {q}</p>
            <p style="font-size:16px; color:#475569; line-height:1.7; margin:0;">A. {a}</p>
        </div>'''
    if not items: return ""
    return f'''
<h2 id="faq" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:45px; font-size:21px;">자주 묻는 질문</h2>
<div style="margin-top:20px;">{items}</div>
'''

# 결론 섹션
def build_conclusion_html(conclusion_text):
    if not conclusion_text or not conclusion_text.strip(): return ""
    return f'<h2 id="conclusion" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:45px; font-size:21px;">결론</h2>{format_paragraphs(conclusion_text)}'

def get_unique_target_keyword(blogger, blog_id):
    recent_titles = []
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=30).execute()
        for item in posts.get('items', []):
            clean_title = re.sub(r'\s+', '', item.get('title', ''))
            recent_titles.append(clean_title)
    except: pass
    shuffled_keywords = CAR_KEYWORDS.copy()
    random.shuffle(shuffled_keywords)
    for keyword in shuffled_keywords:
        short_keyword = keyword.split(" ")[0]
        if not any(re.sub(r'\s+', '', short_keyword) in r_title for r_title in recent_titles):
            return keyword
    return random.choice(CAR_KEYWORDS)

def calculate_scheduled_time():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst) + datetime.timedelta(minutes=5) 
    today = now.date()
    # 하루 2회 발행: 오전 10시 / 저녁 7시
    candidates = [datetime.datetime.combine(today, datetime.time(h, random.randint(1, 15)), tzinfo=kst) for h in [10, 19]]
    scheduled_time = next((c for c in candidates if c > now), None)
    if not scheduled_time:
        scheduled_time = datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(10, random.randint(1, 15)), tzinfo=kst)
    return scheduled_time.strftime('%Y-%m-%dT%H:%M:%S+09:00')

def generate_blog_content(target_keyword):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(api_key=api_key_direct, http_options=types.HttpOptions(api_version="v1beta"))
    
    prompt = (
        f"[{target_keyword}]에 대해 검색한 운전자가 체류 시간을 길게 유지할 수 있도록, 정확하고 실용적인 '자동차 정보 가이드'를 작성해줘.\n\n"
        "[필수 작성 지침]\n"
        "1. [제목]: 핵심 키워드가 맨 앞에 오도록 배치하고 클릭률을 높이는 구체적인 이득을 명시하라. (예: '엔진오일 교환주기, 제조사 권장 vs 현실 기준 총정리')\n"
        "2. [분량 및 깊이 강화]: 블로그 상위 노출을 위해 각 소제목 본문(body_1, body_2, body_3)은 각각 최소 450자~600자 이상으로 매우 길고 상세하게 작성하라. 원리 설명뿐만 아니라 '실제 운전/정비 상황에서의 예시'와 '구체적인 비용·수치'를 반드시 포함하라.\n"
        "3. [모바일 가독성]: 문장은 25자 내외로 호흡을 짧게 끊고 접속사는 삭제하라. 정보 나열은 글머리기호(-, 1. 2.)를 쓰고 비교 분석은 마크다운 표(|구분|내용|)로 구현하라.\n"
        "4. [인트로]: intro 항목에는 이 글을 왜 읽어야 하는지, 어떤 고민을 해결해주는지 3~4문장으로 자연스럽게 작성하라.\n"
        "5. [한글 핵심 요약]: global_summary 항목에는 '바쁜 운전자를 위한 핵심 요약 3줄'을 한글로 작성하라.\n"
        "6. [섹션별 요약]: summary_1, summary_2, summary_3에는 각 섹션 내용을 2줄(60~80자)로 압축한 핵심 요약을 작성하라. 본문을 그대로 반복하지 말고 결론만 짚어라.\n"
        "7. [FAQ]: faq 항목에는 이 주제에 대해 운전자들이 실제로 궁금해할 만한 질문 4개와 각 답변(2~3문장)을 작성하라.\n"
        "8. [결론]: conclusion 항목에는 전체 내용을 마무리하는 문단(200~300자)을 작성하라. 핵심 포인트 재확인 + 실천 조언으로 끝내라.\n"
        "9. [금지어]: '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램', '단계별 전략' 절대 금지.\n"
        "10. [핵심 단어 강조]: 중요한 키워드나 수치는 반드시 마크다운 볼드체(**강조할 단어**)로 감싸서 작성하라.\n"
        "11. [URL 슬러그 생성]: 이 글의 웹 주소(URL)로 쓸 자동차 관련 소문자 영어 단어 2~3개를 하이픈(-)으로 연결하여 'slug' 값에 작성하라. (예: 'engine-oil-change')\n\n"
        "반드시 아래의 JSON 규격에 맞춰서 작성하고, JSON 데이터 외에 다른 설명 텍스트나 마크다운 문법은 일절 출력하지 마라.\n"
        "{\n"
        '  "title": "키워드 앞배치 SEO 최적화 제목",\n'
        '  "slug": "engine-oil-change",\n'
        '  "intro": "글을 시작하는 인트로 3~4문장",\n'
        '  "global_summary": "한글 핵심 요약 3줄 내용",\n'
        '  "tags": ["자동차", "카라이프", "관련키워드"],\n'
        '  "sub_title_1": "1단계 소제목 (개념/기준 완벽 이해하기)",\n'
        '  "body_1": "1단계 본문 내용 (최소 450자 이상 길고 상세하게 작성)",\n'
        '  "summary_1": "1단계 핵심 요약 2줄",\n'
        '  "sub_title_2": "2단계 소제목 (실전 상황별 비교 분석)",\n'
        '  "body_2": "2단계 본문 내용 (비교 분석용 마크다운 표 반드시 삽입 및 상세 설명)",\n'
        '  "summary_2": "2단계 핵심 요약 2줄",\n'
        '  "sub_title_3": "3단계 소제목 (실전 비용 절약/관리 팁)",\n'
        '  "body_3": "3단계 본문 내용 (구체적인 비용 절약 매뉴얼 상세 제시)",\n'
        '  "summary_3": "3단계 핵심 요약 2줄",\n'
        '  "faq": [\n'
        '    {"question": "질문1", "answer": "답변1"},\n'
        '    {"question": "질문2", "answer": "답변2"},\n'
        '    {"question": "질문3", "answer": "답변3"},\n'
        '    {"question": "질문4", "answer": "답변4"}\n'
        '  ],\n'
        '  "conclusion": "전체 내용을 마무리하는 결론 문단"\n'
        "}"
    )
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.7
    )
    
    for model in ['gemini-2.5-flash', 'gemini-2.5-pro']:
        for attempt in range(3):
            try:
                print(f"🤖 Gemini API 고밀도 원고 생성 중... (모델: {model}, 시도: {attempt+1}/3)")
                response = client.models.generate_content(model=model, contents=prompt, config=config)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"⚠️ 지연 발생: {e}")
                if attempt < 2: time.sleep(10)
    raise RuntimeError("🚨 데이터 생성 실패")

def check_already_posted(blogger, blog_id):
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=10).execute()
        count = sum(1 for item in posts.get('items', []) if item.get('published', '').startswith(now.strftime('%Y-%m-%d')))
        # 하루 2회 발행 상한
        if count >= 2: return True
    except: pass
    return False

# =====================================================================
# 🚀 메인 실행 함수
# =====================================================================
def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))

    if "여기에" in BLOG_ID or "여기에" in CAR_TEST_URL or "여기에" in GOOGLE_ADSENSE_SLOT:
        print("🚨 [설정 미완료] 파일 상단의 BLOG_ID / CAR_TEST_URL / 광고슬롯 3개를 먼저 채워주세요!")
        return

    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token: return
    blogger = build('blogger', 'v3', credentials=pickle.loads(base64.b64decode(b64_token)))
    
    if check_already_posted(blogger, BLOG_ID): return
    
    try:
        posts = blogger.posts().list(blogId=BLOG_ID, maxResults=1).execute()
        if posts.get('items'):
            last_pub_time = datetime.datetime.fromisoformat(posts['items'][0].get('published', '').replace('Z', '+00:00')).astimezone(kst)
            if (datetime.datetime.now(kst) - last_pub_time).total_seconds() < 3600: return 
    except: pass
    
    target_keyword = get_unique_target_keyword(blogger, BLOG_ID)
    print(f"🎯 오늘의 타겟 키워드: '{target_keyword}'")
    ai_json_response = generate_blog_content(target_keyword)
    
    try:
        clean_json = ai_json_response.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
    except Exception as e:
        raise ValueError(f"🚨 JSON 파싱 대참사 발생! AI가 규격을 어겼습니다.\n[에러]: {e}\n[AI가 보낸 원본]:\n{ai_json_response[:500]}")

    title = data.get("title", f"{target_keyword} 완벽 가이드")
    tags = data.get("tags", ["자동차", "카라이프"])
    intro = data.get("intro", "")
    
    sub1 = data.get("sub_title_1", "핵심 개념 이해하기")
    body1 = data.get("body_1", "")
    summary_1 = data.get("summary_1", "")
    
    sub2 = data.get("sub_title_2", "실전 비교 분석")
    body2 = data.get("body_2", "")
    summary_2 = data.get("summary_2", "")
    
    sub3 = data.get("sub_title_3", "실전 관리 팁")
    body3 = data.get("body_3", "")
    summary_3 = data.get("summary_3", "")
    
    global_summary = data.get("global_summary", "")
    faq_list = data.get("faq", [])
    conclusion = data.get("conclusion", "")

    raw_slug = data.get("slug", "car-life-guide").lower()
    slug = re.sub(r'[^a-z0-9\-]', '', raw_slug).strip('-')
    if not slug:
        slug = "car-tip-guide"

    if len(body1) < 15 or len(body2) < 15:
        raise ValueError(f"🚨 본문 실종 에러! 껍데기 파싱은 성공했으나 본문 내용이 비어있습니다.\n[body1]: {body1}\n[body2]: {body2}")

    gs_html = format_paragraphs(global_summary) if global_summary else ""
    overview_summary_html = f'<div style="background:#eff6ff; border-left:4px solid #2563eb; padding:18px; margin:20px 0; border-radius:0 8px 8px 0;"><p style="margin:0 0 8px 0; font-size:15px; font-weight:bold; color:#1e40af;">💡 핵심 요약</p><div style="font-size:16px; color:#334155;">{gs_html}</div></div>' if gs_html else ""

    toc_html = build_toc_html(sub1, sub2, sub3)
    intro_html = format_paragraphs(intro) if intro else ""
    faq_html = build_faq_html(faq_list)
    conclusion_html = build_conclusion_html(conclusion)

    final_html = toc_html + intro_html + overview_summary_html + ADSENSE_CODE + \
                 f'<h3 id="sec1" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub1}</h3>{format_paragraphs(body1)}{make_section_summary(summary_1)}' + \
                 CAR_TEST_BOARD_CODE + \
                 f'<h3 id="sec2" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub2}</h3>{format_paragraphs(body2)}{make_section_summary(summary_2)}' + ADSENSE_CODE + \
                 f'<h3 id="sec3" style="border-left:5px solid #3b82f6; padding-left:10px; margin-top:35px; font-size:20px;">{sub3}</h3>{format_paragraphs(body3)}{make_section_summary(summary_3)}' + \
                 faq_html + ADSENSE_CODE + conclusion_html + CTA_CODE

    scheduled_pub_time = calculate_scheduled_time()

    # [3연타 분할 전송] 라이브 등록 -> 한글 제목 먼저 박제 -> 마지막에 미래 시간 유배
    try:
        print(f"🔗 [1연타] 영어 퍼머링크 굳히기 발행 중... (Target URL: /{slug}.html)")
        res_insert = blogger.posts().insert(
            blogId=BLOG_ID, 
            body={'title': slug, 'content': final_html, 'labels': tags}, 
            isDraft=False
        ).execute()
        
        created_post_id = res_insert.get('id')
        
        time.sleep(1.5)
        
        print(f"✍️ [2연타] 한글 정식 제목('{title}') 먼저 안전하게 박제 중...")
        blogger.posts().patch(
            blogId=BLOG_ID, 
            postId=created_post_id, 
            body={
                'title': title,
                'content': final_html, # 본문 삭제 버그 방어
                'labels': tags
            }
        ).execute()

        time.sleep(1.0)

        print(f"⏰ [3연타] 예약 대기열({scheduled_pub_time})로 최종 유배 전송 중...")
        blogger.posts().patch(
            blogId=BLOG_ID, 
            postId=created_post_id, 
            body={
                'published': scheduled_pub_time
            }
        ).execute()

        print(f"✅ <카라이프> 포스팅 규격화 완벽 발행 성공! ({title})")
    except Exception as e:
        print(f"❌ 발행 에러: {e}")

if __name__ == "__main__":
    main()
