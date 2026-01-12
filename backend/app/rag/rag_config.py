import os
from dotenv import load_dotenv

load_dotenv()

# 현재 rag_config.py 파일이 있는 위치를 기준으로 절대 경로 계산
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 기본 경로를 'app/rag/artifacts' 및 'app/rag/data'가 되도록 설정
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", os.path.join(CURRENT_DIR, "artifacts"))
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", os.path.join(CURRENT_DIR, "data", "topics.csv"))

FAISS_INDEX_PATH = os.path.join(ARTIFACT_DIR, "faiss.index")
METAS_PATH = os.path.join(ARTIFACT_DIR, "metas.json")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")