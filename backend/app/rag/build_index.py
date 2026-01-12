"""로컬 주제풀을 인덱스로 빌드하는 스크립트.

?? ?? → 텍스트 구성 → 임베딩 → ?? ??? 인덱스 저장 흐름을 수행합니다.
"""
from rag.rag_config import DATA_CSV_PATH
from indexer import load_topics_csv, build_faiss_index, save_artifacts
from textify import make_text_for_embedding
from embedder import embed_texts

def build():
    """주제 ?? ??를 읽어 ?? ??? 인덱스를 생성하고 저장합니다."""
    docs = load_topics_csv(DATA_CSV_PATH)
    texts = [make_text_for_embedding(d["metadata"]) for d in docs]
    vectors = embed_texts(texts)
    index = build_faiss_index(vectors)
    save_artifacts(index, docs)
    # ?? ??? ???? ?? ?????.
    print("✅ Built artifacts:", "faiss.index, metas.json")

if __name__ == "__main__":
    build()
