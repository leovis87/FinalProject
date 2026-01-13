"""문장 임베딩 생성 모듈.

로컬 주제풀과 사용자 질의를 벡터로 변환해
?? ??? 유사도 검색이 가능하도록 합니다.
"""
import numpy as np
from sentence_transformers import SentenceTransformer

# 예시 모델: 한국어도 어느 정도 되는 멀티링구얼
# 필요하면 다른 모델로 교체
# 기본 임베딩 모델: 다국어 문장 임베딩에 안정적인 공개 모델을 사용합니다.
# TODO: 도메인 특화 모델로 교체 시 성능 비교/평가 필요.
_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_embedder = SentenceTransformer(_MODEL_NAME)

def embed_texts(texts: list[str]) -> np.ndarray:
    """문서(주제풀) 임베딩을 생성합니다."""
    vecs = _embedder.encode(
        texts,
        normalize_embeddings=True,  # ??? ??? ?? ??? ?? ???
        batch_size=32,
        show_progress_bar=True
    )
    return vecs.astype("float32")

def embed_query(query: str) -> np.ndarray:
    """단일 질의 임베딩을 생성합니다."""
    v = _embedder.encode([query], normalize_embeddings=True)
    return v.astype("float32")  # ??: (1, ??)
