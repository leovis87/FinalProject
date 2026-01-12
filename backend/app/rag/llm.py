import os, json
from google import genai
from google.genai import types
from rag.rag_config import GEMINI_API_KEY, GEMINI_MODEL
from dotenv import load_dotenv

load_dotenv()  # ⭐ 반드시 필요

client = genai.Client(
    api_key=GEMINI_API_KEY
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
    - Output MUST be written in Korean.
    - topic_text must be a single Korean sentence that clearly allows a PRO vs CON debate.
    - one_line_context must be one Korean sentence that helps students immediately understand the situation.
    - keywords must be 3 to 6 Korean keywords.
    - sensitive must be set according to the given condition.
    - stance_clarity should usually be true; set it to false only if the topic is inherently ambiguous.
    """
    print(f'context :',context)

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
