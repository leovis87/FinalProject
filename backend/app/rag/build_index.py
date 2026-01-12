from config import DATA_CSV_PATH
from indexer import load_topics_csv, build_faiss_index, save_artifacts
from textify import make_text_for_embedding
from embedder import embed_texts

def build():
    docs = load_topics_csv(DATA_CSV_PATH)
    texts = [make_text_for_embedding(d["metadata"]) for d in docs]
    vectors = embed_texts(texts)
    index = build_faiss_index(vectors)
    save_artifacts(index, docs)
    print("✅ Built artifacts:", "faiss.index, metas.json")

if __name__ == "__main__":
    build()
