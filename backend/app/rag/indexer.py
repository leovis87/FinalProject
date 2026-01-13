"""로컬 주제풀을 ?? ??? 인덱스로 변환/로드하는 모듈.

??-?? 파이프라인의 기반이 되는 "로컬 지식베이스"를 관리하며,
?? ?? → 벡터화 → 인덱스 저장/로드 흐름을 담당합니다.
"""
import csv, json, os
import numpy as np
import faiss
from rag.rag_config import FAISS_INDEX_PATH, METAS_PATH

def load_topics_csv(csv_path: str):
    """?? ??에서 주제 메타데이터를 로딩합니다.

    - 숫자/불리언/키워드 타입을 정규화해 검색 필터링에 쓰기 좋게 만듭니다.
    - 반환된 docs는 {"metadata": row} 구조로 유지됩니다.
    """
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
    """?? ??? 인덱스를 생성합니다.

    내적 기반(IndexFlatIP)을 사용해 코사인 유사도 검색이 가능하도록 구성합니다.
    """
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index

def save_artifacts(index, docs):
    """인덱스와 메타데이터를 디스크에 저장합니다.

    발표/운영 환경에서 로딩 속도를 높이기 위해
    사전 빌드된 아티팩트를 파일로 보관합니다.
    """
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(METAS_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)

def load_artifacts():
    """저장된 ?? ??? 인덱스와 메타데이터를 로드합니다."""
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open(METAS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return index, docs
