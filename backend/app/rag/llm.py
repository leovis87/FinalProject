import os, json
from google import genai
from google.genai import types
from rag.rag_config import GEMINI_API_KEY, GEMINI_MODEL
from dotenv import load_dotenv

load_dotenv()  # ⭐ 반드시 필요

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY", "")
)

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
    retrieved_docs: list[dict],
    n_topics: int = 5,
    model_name: str | None = None
):
    context = to_context(retrieved_docs)
    model_name = model_name or GEMINI_MODEL

    system = (
        "너는 교육용 토론 주제 생성기다. "
        "입력 조건(학년/과목/난이도/민감여부)을 반드시 지키고, "
        "제공된 참고 후보들과 유사한 결로 새로운 주제를 생성하라."
    )

    prompt = f"""
[사용자 요청]
{user_query}

[조건]
- level: {level}
- subject: {subject}
- difficulty: {diff_min}~{diff_max}
- sensitive 허용: {allow_sensitive}
- 생성 개수: {n_topics}

[참고 후보(RAG 검색 결과)]
{context}

[생성 규칙]
- topic_text는 찬반 토론이 가능하게 한 문장 형태로 작성
- one_line_context는 학생이 바로 상황을 이해할 수 있게 1문장
- keywords는 3~6개
- sensitive는 조건에 맞게 설정
- stance_clarity는 보통 true (애매하면 false)
"""

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
