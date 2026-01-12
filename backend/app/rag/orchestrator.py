"""??-?? 오케스트레이션 레이어.

?? ??-?? → ? ??-?? → ??? 순서로 검색/게이트/모드 결정을 수행하고,
?? 호출은 llm.py로 위임합니다. 이렇게 분리하면 검색 계층과 생성 계층을
독립적으로 교체/테스트할 수 있습니다.
"""
import json
from dataclasses import dataclass
from typing import List, Literal, Optional

from tavily import TavilyClient

from rag.guard import guard_user_query
from rag.llm import generate_topics_with_gemini
from rag.rag_config import (
    LOCAL_TOPK,
    MIN_LOCAL_HITS,
    MIN_WEB_HITS,
    TAVILY_API_KEY,
    TAVILY_SEARCH_DEPTH,
    WEB_TOPN,
)
from rag.retriever import retrieve_service

# 모드 라벨은 ??-?? 사용 여부를 외부에 명확히 노출하기 위한 계약입니다.
Mode = Literal["LOCAL_RAG", "WEB_RAG", "NO_RETRIEVAL"]


# 로컬/웹 검색 결과를 동일 구조로 다루기 위한 데이터 모델입니다.
@dataclass
class RetrievedDoc:
    doc_id: str
    title: str
    snippet: str
    source: Literal["local", "web"]
    url: Optional[str] = None
    score: Optional[float] = None
    meta: Optional[dict] = None


def to_context(docs: List[object]) -> str:
    """검색 결과를 ?? 입력용 컨텍스트로 변환합니다.

    - 로컬 ??-?? 문서: 메타데이터 중심 요약
    - 웹 ??-?? 문서: 제목/스니펫/?? 중심 요약

    이 단계에서 근거를 구조화해두면 ??이 참고자료를
    명시적으로 인식하기 쉬워집니다.
    """
    lines = []
    for doc in docs:
        if isinstance(doc, dict) and "metadata" in doc:
            meta = doc["metadata"]
            keywords = "/".join(meta.get("keywords", []))
            lines.append(
                f"- (id:{meta.get('topic_id')}) "
                f"[{meta.get('level')}/{meta.get('subject')}/{meta.get('difficulty')}] "
                f"topic:{meta.get('topic_text')} | context:{meta.get('one_line_context')} | "
                f"keywords:{keywords}"
            )
        else:
            doc_id = getattr(doc, "doc_id", None) or (doc.get("doc_id") if isinstance(doc, dict) else None)
            title = getattr(doc, "title", None) or (doc.get("title") if isinstance(doc, dict) else None)
            snippet = getattr(doc, "snippet", None) or (doc.get("snippet") if isinstance(doc, dict) else None)
            source = getattr(doc, "source", None) or (doc.get("source") if isinstance(doc, dict) else None)
            url = getattr(doc, "url", None) or (doc.get("url") if isinstance(doc, dict) else None)
            lines.append(
                f"- (id:{doc_id}) [{source}] title:{title} | snippet:{snippet} | url:{url}"
            )
    return "\n".join(lines)


def build_web_query(*, user_query: str, level: str, subject: str, allow_sensitive: bool) -> str:
    """웹 검색 쿼리를 생성합니다.

    민감 주제 허용 여부에 따라 검색어를 조정해
    안전성과 관련성을 균형 있게 맞추는 것이 목적입니다.
    """
    base = f"{subject} debate topic {level}"
    if allow_sensitive:
        return f"{base} pros cons {user_query}".strip()
    return f"{base} classroom debate".strip()


def web_retrieve(*, query: str, top_n: int) -> List[RetrievedDoc]:
    """??? 기반 웹 검색을 수행합니다.

    TODO: 캐싱, 중복 제거, 언어/도메인 필터링, 신뢰도 평가 추가.
    """
    if not TAVILY_API_KEY:
        return []

    client = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        result = client.search(
            query=query,
            max_results=top_n,
            search_depth=TAVILY_SEARCH_DEPTH,
            include_answer=False,
            include_raw_content=False,
            include_images=False,
        )
    except Exception:
        return []

    docs: List[RetrievedDoc] = []
    for item in result.get("results", []):
        docs.append(
            RetrievedDoc(
                doc_id=item.get("url"),
                title=item.get("title"),
                snippet=item.get("content") or item.get("snippet"),
                source="web",
                url=item.get("url"),
                score=item.get("score"),
                meta=item,
            )
        )
    return docs


def filter_docs(*, docs: List[RetrievedDoc], allow_sensitive: bool, subject: str) -> List[RetrievedDoc]:
    """검색 결과를 정책에 맞게 정제합니다.

    현재는 MVP 단계라 통과시키지만, 향후 규칙을 확장합니다.
    TODO: 민감 주제 필터, 과목 무관 문서 제거, 광고/중복 제거.
    """
    return docs


def _build_sources(docs: List[object]) -> List[dict]:
    """응답에 포함될 출처 메타데이터를 구성합니다.

    평가/로그에서 "어떤 근거를 사용했는지"를 보여주기 위한 데이터입니다.
    """
    sources: List[dict] = []
    for doc in docs:
        if isinstance(doc, dict) and "metadata" in doc:
            meta = doc["metadata"]
            sources.append(
                {
                    "id": meta.get("topic_id"),
                    "source": "local",
                    "title": meta.get("topic_text"),
                    "snippet": meta.get("one_line_context"),
                    "url": None,
                }
            )
        else:
            sources.append(
                {
                    "id": getattr(doc, "doc_id", None) if not isinstance(doc, dict) else doc.get("doc_id"),
                    "source": getattr(doc, "source", None) if not isinstance(doc, dict) else doc.get("source"),
                    "title": getattr(doc, "title", None) if not isinstance(doc, dict) else doc.get("title"),
                    "snippet": getattr(doc, "snippet", None) if not isinstance(doc, dict) else doc.get("snippet"),
                    "url": getattr(doc, "url", None) if not isinstance(doc, dict) else doc.get("url"),
                }
            )
    return sources


def local_retrieve(
    *,
    user_query: str,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    index,
    docs,
    embed_query,
    top_k: int,
    min_score: float,
    candidate_k: int,
) -> List[dict]:
    """로컬 벡터DB 검색을 호출합니다.

    실제 검색 로직은 retriever.retrieve_service에 위임합니다.
    """
    return retrieve_service(
        user_query=user_query,
        top_k=top_k,
        level=level,
        subject=subject,
        diff_min=diff_min,
        diff_max=diff_max,
        allow_sensitive=allow_sensitive,
        index=index,
        docs=docs,
        embed_query=embed_query,
        min_score=min_score,
        candidate_k=candidate_k,
    )


def generate_topics_with_fallback(
    *,
    user_query: str,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    n_topics: int,
    index,
    docs,
    embed_query,
    min_score: float,
    candidate_k: int,
    top_k: Optional[int] = None,
    model_name: Optional[str] = None,
) -> dict:
    guard = guard_user_query(
        user_query=user_query,
        level=level,
        subject=subject,
        allow_sensitive=allow_sensitive,
    )
    if guard.decision == "REJECT":
        return {
            "mode": "REJECTED",
            "reason_ko": guard.reason_ko,
            "examples_ko": guard.recommended_examples_ko,
            "topics": [],
        }

    if guard.decision == "FALLBACK":
        effective_query = f"{subject} 토론 주제 {level}"
    elif guard.decision == "REFINE":
        effective_query = guard.refined_query_ko or user_query
    else:
        effective_query = user_query

    local_docs = local_retrieve(
        user_query=effective_query,
        level=level,
        subject=subject,
        diff_min=diff_min,
        diff_max=diff_max,
        allow_sensitive=allow_sensitive,
        index=index,
        docs=docs,
        embed_query=embed_query,
        top_k=top_k or LOCAL_TOPK,
        min_score=min_score,
        candidate_k=candidate_k,
    )

    if len(local_docs) >= MIN_LOCAL_HITS:
        used_docs = local_docs[:MIN_LOCAL_HITS]
        return _generate_with_mode(
            mode="LOCAL_RAG",
            rag_used="local",
            docs=used_docs,
            user_query=effective_query,
            level=level,
            subject=subject,
            diff_min=diff_min,
            diff_max=diff_max,
            allow_sensitive=allow_sensitive,
            n_topics=n_topics,
            model_name=model_name,
        )

    web_query = build_web_query(
        user_query=effective_query,
        level=level,
        subject=subject,
        allow_sensitive=allow_sensitive,
    )
    web_docs = web_retrieve(query=web_query, top_n=WEB_TOPN)
    web_docs = filter_docs(docs=web_docs, allow_sensitive=allow_sensitive, subject=subject)

    if len(web_docs) >= MIN_WEB_HITS:
        used_docs = web_docs[:MIN_WEB_HITS]
        return _generate_with_mode(
            mode="WEB_RAG",
            rag_used="web",
            docs=used_docs,
            user_query=effective_query,
            level=level,
            subject=subject,
            diff_min=diff_min,
            diff_max=diff_max,
            allow_sensitive=allow_sensitive,
            n_topics=n_topics,
            model_name=model_name,
        )

    return {
        "mode": "NO_RETRIEVAL",
        "rag_used": "none",
        "n_retrieved": 0,
        "sources": [],
        "used_source_ids": [],
        "topics": [],
        "error": "주제 후보 부족",
    }

def _generate_with_mode(
    *,
    mode: Mode,
    rag_used: Literal["local", "web"],
    docs: List[object],
    user_query: str,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    n_topics: int,
    model_name: Optional[str],
) -> dict:
    context = to_context(docs)
    json_text = generate_topics_with_gemini(
        user_query=user_query,
        level=level,
        subject=subject,
        diff_min=diff_min,
        diff_max=diff_max,
        allow_sensitive=allow_sensitive,
        context=context,
        n_topics=n_topics,
        model_name=model_name,
    )
    payload = json.loads(json_text)
    topics = payload.get("topics", [])
    sources = _build_sources(docs)
    used_source_ids = [s.get("id") for s in sources]
    return {
        "mode": mode,
        "rag_used": rag_used,
        "n_retrieved": len(docs),
        "sources": sources,
        "used_source_ids": used_source_ids,
        "topics": topics,
    }
