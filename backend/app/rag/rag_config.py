"""??-?? 관련 설정 값을 관리하는 모듈.

환경변수로 오버라이드 가능한 기본값을 제공하며,
로컬 인덱스 경로/?? 키/웹 검색 설정을 중앙에서 관리합니다.
"""
import os
from dotenv import load_dotenv

# 실행 환경(.env)에서 설정 값을 로딩합니다.
load_dotenv()

# 로컬 ??-?? 아티팩트 경로(인덱스/메타데이터) 기본값
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "rag/artifacts")
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", "data/topics.csv")

# ?? ??? 인덱스와 메타데이터 저장 경로
FAISS_INDEX_PATH = os.path.join(ARTIFACT_DIR, "faiss.index")
METAS_PATH = os.path.join(ARTIFACT_DIR, "metas.json")

# ?? 키/모델 설정(환경변수로 주입)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# 폴백 게이트 조건(환경변수로 조정 가능)
MIN_LOCAL_HITS = int(os.getenv("MIN_LOCAL_HITS", "3"))
LOCAL_TOPK = int(os.getenv("LOCAL_TOPK", "8"))
MIN_WEB_HITS = int(os.getenv("MIN_WEB_HITS", "3"))
WEB_TOPN = int(os.getenv("WEB_TOPN", "6"))

# 웹 검색(???) 설정
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
