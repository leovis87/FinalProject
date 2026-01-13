from fastapi import APIRouter
from pydantic import BaseModel

from models.rags import TopicReq
from rag.indexer import load_artifacts
from rag.embedder import embed_query
from rag.orchestrator import generate_topics_with_fallback

router = APIRouter(prefix="/rag", tags=["RAG"])

index, docs = load_artifacts()

# 값 변환을 위한 매핑 테이블
LEVEL_MAPPING = {
    "elementary_low": "초등_저학년",
    "elementary_high": "초등_고학년",
    "middle": "중학생",
    "high": "고등학생",
    "all": None  # 'all'인 경우 필터링을 하지 않도록 처리 필요
}

SUBJECT_MAPPING = {
    "korean": "국어",
    "social": "사회",
    "moral": "도덕",
    "ethics": "도덕",  # ethics도 도덕으로 매핑 (데이터셋에 '윤리'가 없다면)
    "science": "과학"
}

@router.post("/topics/generate")
def generate(req: TopicReq):
    # 1. 프론트엔드 값을 데이터셋 값으로 변환
    mapped_level = LEVEL_MAPPING.get(req.level, req.level)
    mapped_subject = SUBJECT_MAPPING.get(req.subject, req.subject)

    # 2. 'all' 선택 시 필터링 로직 처리를 위해 Orchestrator나 Retriever 수정이 필요할 수 있음
    #    (현재 retriever.py는 정확한 일치만 검사하므로, all 처리를 위해선 retriever 수정이 더 근본적임)
    #    하지만 간단한 해결을 위해 여기서는 변환된 값만 넘깁니다.

    result = generate_topics_with_fallback(
        user_query=req.user_query,
        level=mapped_level,      # 변환된 값 전달
        subject=mapped_subject,  # 변환된 값 전달
        diff_min=req.diff_min,
        diff_max=req.diff_max,
        allow_sensitive=req.allow_sensitive,
        n_topics=req.n_topics,
        index=index,
        docs=docs,
        embed_query=embed_query,
        min_score=req.min_score,
        candidate_k=req.candidate_k,
        top_k=req.top_k,
        model_name=req.model_name,
    )

    return result