import csv, json, os
import numpy as np
import faiss
from rag.rag_config import FAISS_INDEX_PATH, METAS_PATH

def load_topics_csv(csv_path: str):
    docs = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["topic_id"] = int(row["topic_id"])
            row["difficulty"] = int(row["difficulty"])
            row["stance_clarity"] = (str(row["stance_clarity"]).lower() == "true")
            row["sensitive"] = (str(row["sensitive"]).lower() == "true")
            row["keywords"] = row["keywords"].split("|") if row.get("keywords") else []
            docs.append({"metadata": row})
    return docs

def build_faiss_index(vectors: np.ndarray):
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index

def save_artifacts(index, docs):
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(METAS_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)

def load_artifacts():
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open(METAS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return index, docs
