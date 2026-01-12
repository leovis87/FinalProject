import os

ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "artifacts")
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", "data/topics.csv")

FAISS_INDEX_PATH = os.path.join(ARTIFACT_DIR, "faiss.index")
METAS_PATH = os.path.join(ARTIFACT_DIR, "metas.json")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
