import enum

# 소셜 로그인
class AuthProvider(str, enum.Enum):
    KAKAO = "kakao"
    NAVER = "naver"

# 토론 난이도
class DebateLevel(str, enum.Enum):
    ELEMENTARY_LOW = "elementary_low"   # 초(저학년)
    ELEMENTARY_HIGH = "elementary_high" # 초(고학년)
    MIDDLE = "middle"                   # 중
    HIGH = "high"                       # 고
    ALL = "all"                         # 전부

# 토론방 상태
class DebateStatus(str, enum.Enum):
    WAITING = "waiting"                 # 대기
    IN_PROGRESS_INTRO = "in_progress_intro"           # 입론 중
    IN_PROGRESS_REBUTTAL = "in_progress_rebuttal"     # 반론 중
    IN_PROGRESS_REREBUTTAL = "in_progress_rerebuttal" # 재반론 중
    IN_PROGRESS_CONCLUSION = "in_progress_conclusion" # 최종 발언 중
    IN_PROGRESS_VOTING = "in_progress_voting"         # 평가 중
    FINISHED = "finished"               # 끝