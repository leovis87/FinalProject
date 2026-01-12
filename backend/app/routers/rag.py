from fastapi import APIRouter
from pydantic import BaseModel

from models.rags import TopicReq
from rag.indexer import load_artifacts
from rag.embedder import embed_query
from rag.orchestrator import generate_topics_with_fallback

router = APIRouter(prefix="/rag", tags=["RAG"])

index, docs = load_artifacts()

@router.post("/topics/generate")
def generate(req: TopicReq):
    result = generate_topics_with_fallback(
        user_query=req.user_query,
        level=req.level,
        subject=req.subject,
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
