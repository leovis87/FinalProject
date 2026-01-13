'''
description:
    - LLM 설정, 공통 도구, 환경 변수 설정 (Tavily 전용 버전)
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
from core.config import settings 

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
    # ✅ os.environ 대신 settings 객체에서 API 키 참조
    google_api_key = settings.GEMINI_API_KEY, 
    temperature = TEMPERATURE['checker'],
    streaming = True,

    # ai debator용
    top_p = 0.95, # Gemini 기본값
    top_k = 40,   # Gemini 기본값
    max_output_tokens = MAX_TOKENS['high'],
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
).configurable_fields(
    temperature = ConfigurableField(
        id = 'temp',
        name = 'LLM Temperature',
        description = 'LLM의 창의성 설정'
    ),
    model = ConfigurableField(
        id = 'model',
        name = 'LLM model',
        description = 'LLM의 모델 설정'
    ),
    max_output_tokens = ConfigurableField(
        id = 'token',
        name = 'LLM Max_tokens',
        description = 'LLM의 Max 토큰 설정'
    ),
    streaming = ConfigurableField(
        id = 'is_stream',
        name = 'LLM output',
        description = 'LLM의 output 방식 설정'
    ),
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

# ✅ nodes.py 호환용 추가 변수
llm_g_real_normal_harm = llm_g_real_non_harm

# ============================================
# 4. 헬퍼 함수
# ============================================
# Search tool 선택 함수
def get_search_tool(use_tavily: bool = True):
    """
    description:
        - 검색 tool 선택 함수
        - DuckDuckGo가 제거되어 항상 Tavily를 사용합니다.
    """
    if use_tavily:
        logging.info('🔎 Tavily search tool 사용')
        return TAVILY_SEARCH


# Config & Callback 재조립 함수
def create_run_config(base_config: RunnableConfig,
                      is_structured_mode: bool = False) -> RunnableConfig:
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
    if enable_streaming and not is_structured_mode:
        new_callbacks.append(StreamingStdOutCallbackHandler())
    
    # 5. 최종 콜백 덮어쓰기
    run_config['callbacks'] = new_callbacks
    
    return run_config