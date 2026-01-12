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
from langchain_openai import ChatOpenAI # OpenAI (Gemini용)
from langchain_core.prompts import (ChatPromptTemplate, # Chain LLM용 prompt
                                    SystemMessagePromptTemplate, # Caching
                                    MessagesPlaceholder) # Chain용 prompt, memory
from langchain_core.messages import HumanMessage, AIMessage # 수동 기억장치 (history)
from langchain_core.messages import SystemMessage # ✅ Prompt Caching 활성화
from langchain_core.runnables import (ConfigurableField, # ✅ LLM에 유연성 부여
                                      RunnableConfig)    # IDE 자동 완성 / 설정 관리
from langchain_core.callbacks import StreamingStdOutCallbackHandler

# ✅ 최신 langchain-tavily 클래스명으로 수정
from langchain_tavily import TavilySearch 
# ✅ 중앙 설정 객체 임포트 (경로 에러 방지를 위해 core.config 사용)
from core.config import settings 

load_dotenv()


# ============================================
# 🤖 Model mapping
# ============================================
# ✅ nodes.py 에러 방지를 위해 빈 객체로 유지
CLAUDE_MODELS = {}

GEMINI_MODELS = {
    "flash": "gemini-1.5-flash",
    "pro": "gemini-1.5-pro"
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
# ============================================
# ✅ DuckDuckGo 제거 및 TavilySearch로 클래스명 수정
TAVILY_SEARCH = TavilySearch(
    max_results = 3,
    topic = 'general',
    include_answer = True,      # AI 요약 포함
    search_depth = 'advanced',  # 'basic' 또는 'advanced'
)


# ============================================
# 2-1. 🤖 Claude (삭제됨)
# ============================================
# ✅ nodes.py 에러 방지를 위해 None으로 유지
llm_c_configured = None


# ============================================
# 2-2. 🤖 동적 설정이 가능한 메인 LLM (Gemini)
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
    logging.info('🔎 Tavily search tool 사용 (DuckDuckGo 제거됨)')
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