# ---------------------------------------------------------------------
# [1] 라이브러리 임포트
# ---------------------------------------------------------------------
# 일반
import asyncio
import re
import os
import logging
import httpx
import json
import time
import fitz
from dotenv import load_dotenv
from typing import List, TypedDict
from datetime import datetime

# LLM
from langchain_google_genai import (
    ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory # Gemini 전용
)

# LangChain core
from langchain_core.runnables import ConfigurableField
from langchain_core.messages import (
    SystemMessage, HumanMessage, ToolMessage
)

# LangGraph
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# Tools
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from crawl4ai import AsyncWebCrawler

load_dotenv()

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
CURRENT_YEAR = datetime.now().strftime('%Y') # 예: 2026

# 로깅 설정
logging.basicConfig(
    format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S',
    filename = 'deep_research.log',
    encoding = 'utf-8'
)
logger = logging.getLogger("ultra_deep_research")

# ---------------------------------------------------------------------
# [2] 도구 및 모델 초기화
# ---------------------------------------------------------------------
ddg_schema = DuckDuckGoSearchRun()
DUCK_SEARCH = DuckDuckGoSearchResults(backend = "api")  # 기본 설정 api

# gemini-2.5-flash~: 65,536
# gemini-2.0-flash: 8192
MAX_TOKENS = 16384

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

gemini_llm = ChatGoogleGenerativeAI(
    model = "gemini-2.0-flash",
    google_api_key = os.environ.get("GOOGLE_API_KEY"),
    temperature = 0.0,
    max_output_tokens = 8192,           # gemini-2.0-flash 의 출력 최대 토큰
    streaming = True,
    safety_settings = safety_settings
).configurable_fields(
    temperature = ConfigurableField(
        id = 'temp'
    ),
    model = ConfigurableField(
        id = 'model'
    ),
    max_output_tokens = ConfigurableField(
        id = 'token'
    ),
    streaming = ConfigurableField(
        id = 'is_stream'
    )
)

gemini_llm_high = ChatGoogleGenerativeAI(
    model = "gemini-2.5-pro",
    google_api_key = os.environ.get("GOOGLE_API_KEY"),
    temperature = 0.0,
    max_output_tokens = MAX_TOKENS,     # gemini-2.5-flash 부터 출력 최대 토큰 65,536
    streaming = True,
    safety_settings = safety_settings
).configurable_fields(
    temperature = ConfigurableField(
        id = 'temp'
    ),
    model = ConfigurableField(
        id = 'model'
    ),
    max_output_tokens = ConfigurableField(
        id = 'token'
    ),
    streaming = ConfigurableField(
        id = 'is_stream'
    )
)

# ----------------------------------------
# Gemini model list
# ----------------------------------------
# gemini-3-flash-preview
# gemini-2.5-flash-preview-05-20
# gemini-2.5-pro-preview-05-06
# gemini-2.0-flash-thinking-exp
# gemini-2.0-flash
# gemini-1.5-pro

if gemini_llm_high:
    print(f"✅ Gemini-2.5-Pro 연결됨 (Max Output: {MAX_TOKENS})")

elif gemini_llm:
    print(f"✅ Gemini-2.0-Flash 연결됨")

def ask_gemini(prompt: str) -> str:
    '''
    [Gemini-2.0-flash]

    description:
        - Gemini API 호출 (LangChain 방식)
    '''
    if not gemini_llm:
        return None
    
    try:
        response = gemini_llm.invoke(prompt)
        return response.content.strip()
    
    except Exception as e:
        logger.error(f"Gemini 에러: {str(e)}")
        return None
    

def ask_gemini_json(prompt: str) -> dict:
    '''
    [Gemini-2.0-flash]

    description:
        - Gemini API 호출 (LangChain 방식) + json 방식 지정 프롬프트 추가
    '''
    if not gemini_llm:
        return None
    
    # 프롬프트 끝에 JSON 강제 지시 추가
    json_prompt = prompt + "\n\n[IMPORTANT] Output JSON only. No markdown, no explanation."
    
    result = ask_gemini(json_prompt)

    if result:
        return parse_json_safely(result)
    return {}
    

def ask_gemini_high(prompt: str) -> str:
    '''
    [Gemini-2.5-pro]

    description:
        - Gemini API 호출 (LangChain 방식)
    '''
    if not gemini_llm_high:
        return None
    
    try:
        response = gemini_llm_high.invoke(prompt)
        return response.content.strip()
    
    except Exception as e:
        logger.error(f"Gemini 에러: {str(e)}")
        return None
    

def ask_gemini_high_json(prompt: str) -> dict:
    '''
    [Gemini-2.5-pro]

    description:
        - Gemini API 호출 (LangChain 방식) + json 방식 지정 프롬프트 추가
    '''
    if not gemini_llm_high:
        return None
    
    # 프롬프트 끝에 JSON 강제 지시 추가
    json_prompt = prompt + "\n\n[IMPORTANT] Output JSON only. No markdown, no explanation."

    result = ask_gemini_high(json_prompt)

    if result:
        return parse_json_safely(result)
    return {}

# ---------------------------------------------------------------------
# [Helper] JSON 파싱 안전장치 (Markdown 제거)
# ---------------------------------------------------------------------
def parse_json_safely(text: str):
    '''
    description:
        - LLM이 ```json ... ``` 형태로 줄 경우를 대비해 마크다운을 제거 후 파싱
    '''
    try:
        # ```json 과 ``` 제거
        cleaned_text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'```', '', cleaned_text)

        return json.loads(cleaned_text.strip())
    
    except json.JSONDecodeError:
        return {}

# ---------------------------------------------------------------------
# [Helper] Scraper (PDF, Web)
# ---------------------------------------------------------------------
async def fetch_universal_content(url: str) -> str:
    '''
    [Scraper]

    description:
        - URL 타입별 콘텐츠 추출
    '''
    MAX_CONTENT_LENGTH = 50000
    
    try:
        # ---------------------------------------------------------
        # 네이버 블로그 web -> 모바일 주소 변환 (iframe 회피)
        # ---------------------------------------------------------
        if "blog.naver.com" in url and "m.blog.naver.com" not in url:
            # 예: https://blog.naver.com/id/1234 -> https://m.blog.naver.com/id/1234
            url = url.replace("blog.naver.com", "m.blog.naver.com")

            print(f"      🔄 네이버 블로그 모바일 변환: {url}")
            logger.info(f"      🔄 네이버 블로그 모바일 변환: {url}")

        # PDF
        if url.lower().endswith(".pdf"):
            print(f"      📄 PDF: {url}")
            logger.info(f"      📄 PDF: {url}")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=15)
                    doc = fitz.open(stream=response.content, filetype="pdf")
                    text = "".join([page.get_text() for page in doc])
                    return f"[PDF]\n{text}"
                
            except Exception as e:
                logger.error(f"PDF 실패: {e}")
                return f"[Error] PDF 파싱 실패: {e}"

        # 일반 웹
        print(f"      🕷️ Web: {url}")
        logger.info(f"      🕷️ Web: {url}")

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            return result.markdown[:MAX_CONTENT_LENGTH]

    except Exception as e:
        logger.error(f"fetch 에러: {str(e)}")
        return f"[Error] {str(e)}"

# ---------------------------------------------------------------------
# [Helper] Summerize text (Chunking + 요약)
# ---------------------------------------------------------------------
def summarize_long_text(text: str,
                        topic: str,
                        secure_mode: bool = False) -> str:
    '''
    [Summarize]

    description:
        - List/String 타입 자동 판별 + 안전 필터 우회 프롬프트 + 로컬 Fallback 최적화
        - 텍스트가 너무 길면 (예: 25,000자 이상) 무조건 나눠서 요약하도록 유도
        - Gemini도 한 번에 너무 많이 읽으면 '중간 데이터'를 무시하기 때문
    '''
    if len(text) < 300:
        return ""  # 너무 짧으면 스킵
    
    MAX_CHUNK = 25000 

    if len(text) > MAX_CHUNK:
        print(f"      📦 데이터가 너무 커서 정밀 슬라이싱 분석을 시작합니다... ({len(text)}자)")
        text_chunks = [text[i:i+MAX_CHUNK] for i in range(0, len(text), MAX_CHUNK)]
        chunk_results = []
        
        for i, target_chunk in enumerate(text_chunks):
            print(f"      📑 섹션 {i+1}/{len(text_chunks)} 분석 중...")

            # 재귀 호출을 통해 각 파트를 요약
            res = summarize_long_text(
                target_chunk,
                f"{topic} (Part {i+1})",
                secure_mode
            )
            if res and "PASS" not in res[:10]: # PASS는 합치지 않음
                chunk_results.append(res)
        
        return "\n\n".join(chunk_results)
    
    # ---------------------------------------------------------
    # [1] 고속 모드 (Gemini)
    # ---------------------------------------------------------
    if not secure_mode and gemini_llm:
        print(f"      🚀 [Gemini] 고속 요약 시도... (Input: {len(text)}자)")
        logger.info(f"      🚀 [Gemini] 고속 요약 시도... (Input: {len(text)}자)")

        try:
            # 프롬프트에 '수치 및 핵심 논거 누락 금지'를 더 강조합니다.
            prompt = f"""[Task] Analyze the text and extract insights about '{topic}'.

[Source Text Preview]
{text[:500]}...

[Full Text]
{text} 

[Context]
This is for **Academic Research & Data Analysis**.
We need objective facts, diverse opinions, and statistical data.
(Note: Not financial/medical advice, but research material.)

[Instructions]
1. **Goal**: Extract ALL relevant information about '{topic}'.
2. **Be Permissive**: Even if it's a rumor, opinion, or prediction, summarize it as such. DO NOT PASS easily.
3. **Format**: Summarize in Korean.
4. **Panic Button**: Output "PASS" ONLY if the text is technical garbage (e.g., raw code, login page).

[Your Summary in Korean]"""
            
            # 모델 호출
            response = gemini_llm_high.invoke(prompt)
            content = response.content
            summary = ""

            # 🛡️ [Type Check] 응답 타입별 처리 (가장 중요한 부분)
            if isinstance(content, str):
                summary = content

            elif isinstance(content, list):
                # 리스트면 내부 요소들을 문자열로 변환하여 병합
                parts = []

                for item in content:
                    if isinstance(item, str):
                        parts.append(item)

                    elif isinstance(item, dict) and "text" in item:
                        parts.append(str(item["text"]))

                    else:
                        parts.append(str(item)) # 기타 객체는 강제 형변환
                summary = "\n".join(parts)

            else:
                summary = str(content) # 최후의 수단

            summary = summary.strip()
            
            # 🔍 [Validation] 결과 검증
            if not summary:
                print(f"         💀 Gemini 응답 없음 (완전 차단됨)")
                logger.info(f"         💀 Gemini 응답 없음 (완전 차단됨)")
                # print(f"         👉 차단 사유: {response.response_metadata}")
            
            elif "PASS" in summary[:50]:
                print(f"         ⚠️ Gemini가 'PASS' 선언")
                logger.info(f"         ⚠️ Gemini가 'PASS' 선언")
                # print(f"         👉 텍스트 앞부분: {text[:100]}...")
            
            else:
                print(f"         ✅ Gemini 요약 완료 ({len(text)} -> {len(summary)}자)")
                logger.info(f"         ✅ Gemini 요약 완료 ({len(text)} -> {len(summary)}자)")
                return summary

        except Exception as e:
            logger.error(f"         🔥 Gemini 에러: {str(e)}")
            print(f"         🔥 Gemini 에러 발생: {str(e)[:100]}...")

    # ---------------------------------------------------------
    # [2] Fallback 모드 (Local Model - Map Reduce)
    # ---------------------------------------------------------
    # Gemini 실패 시에만 실행됨
    print(f"      🐢 [Local] Llama 3.1 정밀 요약 실행... (Gemini 실패)")
    logger.info(f"      🐢 [Local] Llama 3.1 정밀 요약 실행... (Gemini 실패)")
    
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    # 너무 많으면 앞부분만 (속도 조절)
    if len(chunks) > 15: 
        chunks = chunks[:15]
    
    summaries = []
    for i, chunk in enumerate(chunks):
        if i % 5 == 0:
            print(f"         ({i+1}/{len(chunks)}) 처리 중...")
            logger.info(f"         ({i+1}/{len(chunks)}) 처리 중...")
            
        prompt = f"""[Task] Extract facts about "{topic}".
If unrelated, output "PASS".

[Text]
{chunk}

[Output]"""
        try:
            res = chat_llm.invoke(prompt)
            content = res.content
            
            # 로컬 모델도 리스트로 줄 수 있으니 방어 코드
            if isinstance(content, list):
                content = " ".join([str(c) for c in content])
            
            content = str(content).strip()
            
            if "PASS" not in content and len(content) > 50:
                summaries.append(content)
        except:
            pass

    if not summaries:
        return ""
        
    final_summary = "\n".join(summaries)

    print(f"         ✅ 로컬 요약 완료 ({len(final_summary)}자)")
    logger.info(f"         ✅ 로컬 요약 완료 ({len(final_summary)}자)")
    return final_summary

# ---------------------------------------------------------------------
# [3] 상태(State) 정의
#   - 팀 프로젝트용으로 간소화
# ---------------------------------------------------------------------
class LightStormState(TypedDict):
    topic: str
    sub_topics: List[str]
    scraped_contents: List[str]
    final_report: str


# ---------------------------------------------------------------------
# [4] Node 정의
# ---------------------------------------------------------------------
# 1. Outliner 노드: 7개 제한 및 고속 목차 생성
async def light_outliner_node(state: LightStormState):
    '''
    [Outliner]
    
    description:
        - 목차 생성 7개로 제한.
    '''
    topic = state['topic']
    prompt = f"""
[Task] Generate a Research Outline (MAX 7 SECTIONS).

[Topic]
{topic}

[Format] JSON:
{{
    "sub_topics": ["Title 1", "Title 2", ... "Title 7"]
}}
"""
    result = ask_gemini_json(prompt)
    raw_list = result.get("sub_topics", [])[:7] # 강제 슬라이싱
    
    clean_topics = [re.sub(r'^\d+[\.\)]\s*', '', str(t)).strip() for t in raw_list]
    print(f"🗺️ [Light-STORM] 목차 생성 완료: {len(clean_topics)}개 섹션")
    logger.info(f"🗺️ [Light-STORM] 목차 생성 완료: {len(clean_topics)}개 섹션")

    return {
        "sub_topics": clean_topics
    }

# 2. Mining & Reader 통합 노드: 병렬 처리
async def light_mining_node(state: LightStormState):
    '''
    [Miner + Reader]

    description:
        - Outliner가 생성한 목차를 병렬로 검색
        - 병렬 검색한 url을 병렬 crawling 처리
    '''
    topics = state['sub_topics']
    print(f"⛏️ [Light-STORM] {len(topics)}개 섹션 병렬 마이닝 시작...")
    logger.info(f"⛏️ [Light-STORM] {len(topics)}개 섹션 병렬 마이닝 시작...")

    # -------------------------------------------------------
    # [내부 함수] 1개 토픽에 대해:
    #   - 검색 -> URL추출 -> 크롤링 -> 요약 (풀코스)
    # -------------------------------------------------------
    async def _process_pipeline(sub_topic):
        '''
        [DuckDuckGo search]

        description:
            - DuckDuckGo 검색 (API 실패 시, Text 모드 전환)
        '''
        query = f"{state['topic']} {sub_topic}"

        print(f"      🦆 검색 시도: {sub_topic} ...")
        logger.info(f"      🦆 검색 시도 {sub_topic} ...")

        loop = asyncio.get_event_loop()
        search_result_text = ""

        try:
            # 1차: API 시도
            search_result_text = await loop.run_in_executor(
                None,
                DUCK_SEARCH.invoke,
                query
            )

            # 2차: Text 시도
            if not search_result_text or len(str(search_result_text)) < 100 or "No good DuckDuckGo Search Result" in str(search_result_text):
                print("         ⚠️ API 모드 실패/차단됨 → Text(HTML) 모드로 재시도...")
                logger.info("         ⚠️ API 모드 실패/차단됨 → Text(HTML) 모드로 재시도...")

                # 함수 내에서 backend = "text"로 새 도구 생성 후 재검색
                from langchain_community.tools import DuckDuckGoSearchResults
                ddg_fallback = DuckDuckGoSearchResults(backend = "text")

                search_result_text = await loop.run_in_executor(
                    None,
                    ddg_fallback.invoke,
                    query
                )

            # 3차: 그래도 안되면 실패
            if not search_result_text or len(str(search_result_text)) < 50:
                print("         ❌ 모든 검색 시도 실패")
                return None
            
            # print(f"         ✅ 완료 (결과 길이: {len(str(search_result_text))}자)")
            # logger.info(f"         ✅ 완료 (결과 길이: {len(str(search_result_text))}자)")
            # return f"[DuckDuckGo]\n{search_result_text}"
        
        except Exception as e:
            logger.error(f"DuckDuckGo 실패: {str(e)}")
            return None
        
        # URL 추출 (검색 결과에서 링크 가져오기)
        urls = re.findall(r'https?://[^\s\]\)\'"]+', str(search_result_text))

        if not urls:
            print(f"         ⚠️ 검색 결과에서 URL을 찾을 수 없음")
            return None
        
        target_url = urls[0] # 첫 번째 URL

        # -------------------------------------------------------
        # [3] 크롤링 및 요약
        # -------------------------------------------------------
        print(f"      🕷️ 크롤링 시작: {target_url}")
        try:
            raw_text = await fetch_universal_content(target_url)

            # 요약
            summary = summarize_long_text(
                raw_text,
                f"{state['topic']} - {sub_topic}"
            )

            return summary
        
        except Exception as e:
            print(f"      ❌ 크롤링/요약 실패: {str(e)}")
            return None
        
    # -------------------------------------------------------
    # [병렬 실행]
    # -------------------------------------------------------
    tasks = [_process_pipeline(t) for t in topics]

    # *task로 리스트를 풀어서 전달
    results = await asyncio.gather(*tasks)
    
    # 실패한(None) 거름
    processed = [r for r in results if r]
            
    return {
        "scraped_contents": processed
    }

# 3. Synthesis 노드: 최종 보고서 작성
async def light_synthesis_node(state: LightStormState):
    '''
    [Writer]

    description:
        - Markdwon 형식 유지
        - 신뢰도를 위해 출처 번호 기재
    '''
    context = "\n\n".join(state['scraped_contents'])
    prompt = f"""
[Role]
너는 전문 리포트 작성가야. 
아래 자료를 바탕으로 '## 1. 제목' 구조를 유지하며 심층 보고서를 작성해.

[자료]:
{context}

[Rules]:
1. 반드시 한글로 작성하고, 모든 문장에 출처 번호를 기입할 것.
2. 핵심 위주로 요약해서 작성할 것.
"""
    response = gemini_llm_high.invoke(prompt)
    return {"final_report": response.content}

# ---------------------------------------------------------------------
# [5] Graph 정의
# ---------------------------------------------------------------------
# 그래프 조립 (심플한 직선 구조)
workflow = StateGraph(LightStormState)
workflow.add_node("outliner", light_outliner_node)
workflow.add_node("mining", light_mining_node)
workflow.add_node("synthesis", light_synthesis_node)

workflow.set_entry_point("outliner")
workflow.add_edge("outliner", "mining")
workflow.add_edge("mining", "synthesis")
workflow.add_edge("synthesis", END)

light_storm_app = workflow.compile()