import json
from fastapi import APIRouter
from pydantic import BaseModel

from models.rags import TopicReq
from rag.indexer import load_artifacts
from rag.embedder import embed_query
from rag.retriever import retrieve_service
from rag.llm import generate_topics_with_gemini

router = APIRouter(prefix="/rag", tags=["RAG"])

index, docs = load_artifacts()

@router.post("/topics/generate")
def generate(req: TopicReq):
    retrieved = retrieve_service(
        user_query=req.user_query,
        top_k=req.top_k,
        level=req.level,
        subject=req.subject,
        diff_min=req.diff_min,
        diff_max=req.diff_max,
        allow_sensitive=req.allow_sensitive,
        index=index,
        docs=docs,
        embed_query=embed_query,
        min_score=req.min_score,
        candidate_k=req.candidate_k,
    )

    json_text = generate_topics_with_gemini(
        user_query=req.user_query,
        level=req.level,
        subject=req.subject,
        diff_min=req.diff_min,
        diff_max=req.diff_max,
        allow_sensitive=req.allow_sensitive,
        retrieved_docs=retrieved,
        n_topics=req.n_topics,
        model_name=req.model_name,
    )

    return json.loads(json_text)
