"""
검색/필터링과 분리하여 프롬프트 구성과 스키마 강제만 담당합니다.
이렇게 분리하면 ?? 교체/테스트가 쉬워집니다.
"""
import os, json
from google import genai
from google.genai import types
from groq import Groq
from rag.rag_config import GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
from dotenv import load_dotenv

# ? 키/모델명 등 런타임 설정을 .env에서 로딩합니다.

load_dotenv()  # ???? ??(?/???? ?? ???? ??).

# ???? 클라이언트: 스키마 강제 출력이 필요한 주제 생성에 사용합니다.
client = genai.Client(
    api_key=GEMINI_API_KEY
)

# ?? 클라이언트: ??? 모드를 통해 구조화 결과를 받습니다.
groq_client = Groq(
    api_key=GROQ_API_KEY
)

# 출력 스키마를 고정해 결과 구조를 안정화합니다.
TOPIC_GEN_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic_text": {"type": "string"},
                    "one_line_context": {"type": "string"},
                    "stance_clarity": {"type": "boolean"},
                    "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "sensitive": {"type": "boolean"},
                },
                "required": ["topic_text","one_line_context","stance_clarity","difficulty","keywords","sensitive"],
            },
        }
    },
    "required": ["topics"],
}

def to_context(retrieved_docs):
    """로컬 ??-?? 검색 결과를 프롬프트용 문자열로 변환합니다.

    - 입력값: retriever가 반환한 metadata 리스트
    - 처리 흐름: 핵심 필드만 요약해 ?? 컨텍스트에 주입
    - 반환값: 줄바꿈으로 구성된 컨텍스트 문자열

    오케스트레이터에서 별도 to_context를 사용하지만,
    기존 호출부 호환을 위해 유지되는 함수입니다.
    """
    lines = []
    for r in retrieved_docs:
        m = r["metadata"]
        lines.append(
            f"- (id:{m['topic_id']}) [{m['level']}/{m['subject']}/난이도{m['difficulty']}] "
            f"주제:{m['topic_text']} | 상황:{m['one_line_context']} | 키워드:{'/'.join(m['keywords'])}"
        )
    return "\n".join(lines)

def generate_topics_with_gemini(
    *,
    user_query: str,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    context: str,
    n_topics: int = 5,
    model_name: str | None = None
):
    """Gemini 기반 주제 생성 함수.

    입력값:
    - user_query/level/subject/diff_min/diff_max/allow_sensitive: 사용자 조건
    - context: RAG 결과를 요약한 텍스트
    - n_topics: 생성할 주제 수
    - model_name: 사용할 모델명(없으면 기본 모델)

    처리 흐름:
    1) 모델명 정규화(잘못된 기본값 방지)
    2) 시스템/사용자 프롬프트 구성
    3) JSON 스키마 강제 호출

    반환값:
    - JSON 문자열(text) 형태의 결과

    설계 의도:
    - 검색/필터링과 분리해 ?? 교체가 쉽도록 합니다.
    """
    if (model_name is None) or (model_name.strip() == "") or (model_name.strip().lower() == "string"):
        model_name = GEMINI_MODEL

    system = (
    "You are an educational debate topic generator. "
    "You must strictly follow the given input conditions "
    "(grade level, subject, difficulty range, and sensitivity allowance). "
    "Using the provided reference candidates, generate NEW debate topics "
    "that are similar in tone and structure but not copied. "
    "All outputs MUST be written in Korean."
    )

    prompt = f"""
    [User Request]
    {user_query}

    [Constraints]
    - grade level: {level}
    - subject: {subject}
    - difficulty range: {diff_min} to {diff_max}
    - sensitive topics allowed: {allow_sensitive}
    - number of topics to generate: {n_topics}

    [Reference Candidates (RAG Search Results)]
    {context}

    [Generation Rules]
    - If the reference candidates are insufficient (fewer than 3) or the section is empty,
      return a JSON object with an empty topics array: {{"topics": []}}.
    - Output MUST be written in Korean.
    - topic_text must be a single Korean sentence that clearly allows a PRO vs CON debate.
    - one_line_context must be one Korean sentence that helps students immediately understand the situation.
    - keywords must be 3 to 6 Korean keywords.
    - sensitive must be set according to the given condition.
    - stance_clarity should usually be true; set it to false only if the topic is inherently ambiguous.
    """
    print(f'user_query :',user_query)
    print(f'context :',context)

    # 스키마 강제: 평가/발표에서 구조 일관성을 확보하기 위함입니다.
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=TOPIC_GEN_SCHEMA
        )
    )
    return resp.text


def generate_topics_with_groq(
    *,
    user_query: str,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    context: str,
    n_topics: int = 5,
    model_name: str | None = None
):
    """Groq 기반 주제 생성 함수.

    Gemini와 동일한 입력/출력 계약을 유지해
    호출부에서 모델을 쉽게 교체할 수 있도록 설계했습니다.
    """
    if (model_name is None) or (model_name.strip() == "") or (model_name.strip().lower() == "string"):
        model_name = GROQ_MODEL

    system = (
    "You are an educational debate topic generator. "
    "You must strictly follow the given input conditions "
    "(grade level, subject, difficulty range, and sensitivity allowance). "
    "Using the provided reference candidates, generate NEW debate topics "
    "that are similar in tone and structure but not copied. "
    "All outputs MUST be written in Korean."
    )

    prompt = f"""
    [User Request]
    {user_query}

    [Constraints]
    - grade level: {level}
    - subject: {subject}
    - difficulty range: {diff_min} to {diff_max}
    - sensitive topics allowed: {allow_sensitive}
    - number of topics to generate: {n_topics}

    [Reference Candidates (RAG Search Results)]
    {context}

    [Generation Rules]
    - Output MUST be a JSON object with a top-level "topics" array of objects.
    - Each topic object must include: topic_text (string), one_line_context (string),
      stance_clarity (boolean), difficulty (integer 1-5), keywords (array of strings),
      sensitive (boolean).
    - Do not wrap the JSON in markdown fences or additional text.
    - Output MUST be written in Korean.
    - topic_text must be a single Korean sentence that clearly allows a PRO vs CON debate.
    - one_line_context must be one Korean sentence that helps students immediately understand the situation.
    - keywords must be 3 to 6 Korean keywords.
    - sensitive must be set according to the given condition.
    - stance_clarity should usually be true; set it to false only if the topic is inherently ambiguous.
    """
    print(f'context :',context)

    # ??는 프롬프트 규칙 + ??? 모드로 구조를 통제합니다.
    resp = groq_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return resp.choices[0].message.content
