import re

GENRE_WORDS = [
    "토론","찬반","논쟁","반박","입론","재반박","쟁점",
    "요약","설득","논리","비판","비난","예의","담론",
    "발표","대화","경청","말하기","표현","의사소통","소통",
    "글쓰기","독서","비판적읽기","평가",
    "수업","질문","학습","과정","성찰","SNS","미디어","공적발언","사적발언",
]

def normalize_query(q: str) -> str:
    q2 = q
    for w in GENRE_WORDS:
        q2 = q2.replace(w, "주제")
    q2 = re.sub(r"(주제\s+)+", "주제 ", q2)
    q2 = re.sub(r"\s+", " ", q2).strip()
    return q2

def make_text_for_embedding(m: dict) -> str:
    # 임베딩 텍스트에는 '토론' 같은 장르 단어를 굳이 넣지 않는 편이 안정적
    kw = m.get("keywords", [])
    return (
        f"{m['level']} {m['subject']} "
        f"{m['topic_text']} {m['one_line_context']} "
        f"키워드: {', '.join(kw)}"
    )
