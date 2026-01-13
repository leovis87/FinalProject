'''
description:
    - LLM 설정, 공통 도구, 환경 변수 설정
'''
import os
import logging
from dotenv import load_dotenv

# LangChain
from langchain.agents import create_agent

# LangChain Core
from langchain_google_genai import ChatGoogleGenerativeAI # Gemini 전용
from langchain_google_genai import HarmBlockThreshold, HarmCategory # 안전 설정용 가드레일
from langchain_core.runnables import (
    ConfigurableField, # ✅ LLM에 유연성 부여
    RunnableConfig     # IDE 자동 완성 / 설정 관리
)    
from langchain_core.callbacks import StreamingStdOutCallbackHandler

# LangChain Tools
from langchain_community.tools.tavily_search import TavilySearchResults # Tavily를 이용한 검색 툴

load_dotenv()


# ============================================
# 🤖 Model mapping
# ============================================
# 지원 모델 맵
GEMINI_MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3-pro-preview"
}


# ============================================
# 🤖 Model parameters
# ============================================
TEMPERATURE = {
    'basic': 0.7,
    'strict': 0.3,
    'checker': 0.0
}

MAX_TOKENS = {
    'low': 512,
    'mid': 1024,
    'high': 2048
}


# ============================================
# 🔎 Set langchain tools
#   - Tool 생성
# ============================================
# Tavily searching tool 생성
TAVILY_SEARCH = TavilySearchResults(
    max_results = 3,
    topic = 'general',
    include_answer = True,      # AI 요약 포함
    search_depth = 'advanced',  # 'basic' 또는 'advanced'
)


# ============================================
# 2. 🤖 동적 설정이 가능한 메인 LLM (Gemini)
#   - invoke 시 config={'configurable': {'temp': 0.9}} 등으로 제어 가능
#   - ⚠️ 직관적이진 않음. 사용 시 주의
# ============================================
llm_g_real_non_harm = ChatGoogleGenerativeAI(
    model = GEMINI_MODELS['flash'],
    google_api_key = os.environ.get('GOOGLE_API_KEY'),
    temperature = TEMPERATURE['checker'],
    streaming = True,

    # ai debator용
    top_p = 0.95, # Gemini 기본값
    top_k = 40,   # Gemini 기본값
    max_output_tokens = MAX_TOKENS['high'],
    # 안전 설정 해제 (욕설도 읽어야 분석 가능)
    # 📌 설명(차단 강도 (HarmBlockThreshold)):
    #   - BLOCK_NONE: 차단 안함 => 💡 사회자/분석자용
    #   - BLOCK_ONLY_HIGH: 매우 심한 내용만 차단 => 일반 챗본 (느슨)
    #   - BLOCK_MEDIUM_AND_ABOVE: 중간 수위(Default값) => 일반 챗본 (보통)
    #   - BLOCK_LOW_AND_ABOVE: 조금이라도 위험하면 차단 => 💡 어린이용 서비스
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
).configurable_fields(
    # 1. 왼쪽 변수명은 실제 클래스 인자 이름(temperature)이어야 함
    temperature = ConfigurableField(
        id = 'temp',                     # 중요: 실행 시 config에서 사용할 key
        name = 'LLM Temperature',        # LangSmith/LangServe Ui용 이름
        description = 'LLM의 창의성 설정' # UI용 설명
    ),
    # 2. 모델 설정
    model = ConfigurableField(
        id = 'model',
        name = 'LLM model',
        description = 'LLM의 모델 설정'
    ),
    # 3. 토큰 설정
    max_output_tokens = ConfigurableField(
        id = 'token',
        name = 'LLM Max_tokens',
        description = 'LLM의 Max 토큰 설정'
    ),
    # 4. stream 출력 설정
    streaming = ConfigurableField(
        id = 'is_stream',
        name = 'LLM output',
        description = 'LLM의 output 방식 설정'
    ),
    # 5. ai debator용 top_k, top_p 설정
    # top_k: 확률 순위 ⭐ 상위 K개만 남기고 자름
    #   - 40이 가장 성능이 좋음
    # top_p: 확률 합계가 ⭐ **P%**가 될 때까지만 남기고 남기고 자름
    #   - 논리적 일관성 안전장치 (0.9 ~ 0.95)
    # temperature: 확률 분포를 평평하게(다양하게) or 뾰족하게(확실하게)
    # 📌 설명:
    #   - 창의적인 글쓰기나 자연스러운 대화를 원할 때는 Temperature를 높이고,
    #   - Top_p로 안전장치를 거는 조합이 국룰(Standard).
    top_k = ConfigurableField(
        id = 'top_k',
        name = 'LLM top_k | lank K',
        description = 'LLM의 확률 순위 상위 K개만 필터링'
    ),
    top_p = ConfigurableField(
        id = 'top_p',
        name = 'LLM top_p | lank P%',
        description = 'LLM의 논리적 일관성 안전장치. %로 필터링'
    )
)

# ============================================
# 4. 헬퍼 함수
# ============================================
# Search tool 선택 함수
def get_search_tool(use_tavily: bool = False):
    """
    description:
        - 검색 tool 선택 함수
    
    Args:
        - use_tavily: True == Tavily | False == DuckDuckGo
    
    Returns:
        - 선택된 search tool
    """
    if use_tavily:
        logging.info('🔎 Tavily search tool 사용')
        return TAVILY_SEARCH


# Config & Callback 재조립 함수
def create_run_config(base_config: RunnableConfig,
                      is_structured_mode: bool = False) -> RunnableConfig:
    '''
    description:
        - 실행용 config 생성 헬퍼
        - is_structured_mode=True일 경우, 콘솔 출력 핸들러(StreamingStdOut)를 제외함 (에러 방지)
    '''
    # ============================================
    # 🏗️ config 재설정 & Callback 재조립
    #   1. 기존 config copy == config 복사본
    #   2. 기존 callback copy == callback 복사본
    #   3. config 복사본에 streming 핸들러 추가 == streming 모드 ON
    #   4. callback 복사본에 config 복사본 추가
    # ============================================
    # 1. Config 복사 (원본 보호)
    run_config = base_config.copy() if base_config else {}
    
    # 2. Configurable 안전하게 가져오기
    user_config = run_config.get('configurable', {})
    enable_streaming = user_config.get('is_stream', False)

    # 3. Callback 재조립 (기존 + 신규)
    existing_callbacks = run_config.get('callbacks', [])
    new_callbacks = []

    # 3-1. 기존 콜백 옮겨 담기
    if existing_callbacks:
        if isinstance(existing_callbacks, list):
            new_callbacks.extend(existing_callbacks)
        elif hasattr(existing_callbacks, 'handlers'):
            new_callbacks.extend(existing_callbacks.handlers)
        else:
            new_callbacks.append(existing_callbacks)

    # 4. 스트리밍 핸들러 추가
    # 스트리밍이 켜져 있더라도, '구조화 모드(JSON)'이라면 콘솔 핸들러를 붙이지 않음
    if enable_streaming and not is_structured_mode:
        new_callbacks.append(StreamingStdOutCallbackHandler())
    
    # 5. 최종 콜백 덮어쓰기
    run_config['callbacks'] = new_callbacks
    
    return run_config