"""로컬 벡터DB 검색(?? ???) 래퍼.

??-?? 파이프라인의 "?? ??-??" 단계에서 사용되며,
입력 쿼리를 정규화한 뒤 유사도 검색과 조건 필터링을 수행합니다.
"""
from .textify import normalize_query

def retrieve_service(
    *,
    user_query: str,
    top_k: int,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    index,
    docs,
    embed_query,
    min_score: float = 0.55,
    candidate_k: int = 80,
):
    """로컬 벡터DB에서 조건에 맞는 문서를 검색합니다.

    입력값:
    - user_query: 사용자가 입력한 요청문
    - top_k: 반환할 최대 문서 수
    - level/subject/diff_min/diff_max/allow_sensitive: 필터 조건
    - index/docs: FAISS 인덱스와 메타데이터
    - embed_query: 쿼리 임베딩 함수
    - min_score/candidate_k: 검색 게이트 조건

    처리 흐름:
    1) 질의 정규화(normalize_query)
    2) 임베딩 후 유사도 검색
    3) 메타데이터 조건 필터링

    반환값:
    - score와 metadata를 포함한 문서 리스트
    """
    q = normalize_query(user_query)
    q_vec = embed_query(q)
    D, I = index.search(q_vec, candidate_k)

    # 필터 조건을 통과한 문서만 반환합니다(근거 품질 유지 목적).
    out = []
    for score, idx in zip(D[0], I[0]):
        meta = docs[int(idx)]["metadata"]

        if meta["level"] != level:
            continue
        if meta["subject"] != subject:
            continue
        if not (diff_min <= meta["difficulty"] <= diff_max):
            continue
        if (not allow_sensitive) and meta["sensitive"]:
            continue
        if float(score) < min_score:
            continue

        out.append({"score": float(score), "metadata": meta})
        if len(out) >= top_k:
            break

    return out
