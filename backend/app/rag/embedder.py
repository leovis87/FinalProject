import numpy as np
from sentence_transformers import SentenceTransformer

# 예시 모델: 한국어도 어느 정도 되는 멀티링구얼
# 필요하면 다른 모델로 교체
_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_embedder = SentenceTransformer(_MODEL_NAME)

def embed_texts(texts: list[str]) -> np.ndarray:
    vecs = _embedder.encode(
        texts,
        normalize_embeddings=True,  # cosine용
        batch_size=32,
        show_progress_bar=True
    )
    return vecs.astype("float32")

def embed_query(query: str) -> np.ndarray:
    v = _embedder.encode([query], normalize_embeddings=True)
    return v.astype("float32")  # shape: (1, dim)
