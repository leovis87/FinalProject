import enum

# ?�셜 로그??
class AuthProvider(str, enum.Enum):
    TEST = "test"
    KAKAO = "kakao"
    NAVER = "naver"

# ?�론 ?�이??
class DebateLevel(str, enum.Enum):
    ELEMENTARY_LOW = "elementary_low"   # �??�?�년)
    ELEMENTARY_HIGH = "elementary_high" # �?고학??
    MIDDLE = "middle"                   # �?
    HIGH = "high"                       # �?
    ALL = "all"                         # ?�체

# ?�론 과목 카테고리
class DebateCategory(str, enum.Enum):
    KOREAN = "korean"       # �?��
    SOCIAL = "social"       # ?�회
    MORAL = "moral"         # ?�덕
    ETHICS = "ethics"       # ?�리

# ?�론�??�태
class DebateStatus(str, enum.Enum):
    WAITING = "waiting"                 # ?��?
    IN_PROGRESS_INTRO = "in_progress_intro"           # ?�론 �?
    IN_PROGRESS_REBUTTAL = "in_progress_rebuttal"     # 반론 �?
    IN_PROGRESS_REREBUTTAL = "in_progress_rerebuttal" # ?�반�?�?
    IN_PROGRESS_CONCLUSION = "in_progress_conclusion" # 최종 발언 �?
    IN_PROGRESS_VOTING = "in_progress_voting"         # ?��? �?
    FINISHED = "finished"               # ??

# ?�론 진영
class DebateRole(str, enum.Enum):
    PRO = "pro"             # 찬성
    CON = "con"             # 반�?
    OBSERVER = "observer"   # 관?�자

# 배�? 종류
# Debate result per participant
class DebateResult(str, enum.Enum):
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"

# Decision source for results
class DebateDecisionBy(str, enum.Enum):
    AI = "ai"
    ADMIN = "admin"
    SYSTEM = "system"

class BadgeType(str, enum.Enum):
    NOVICE = "novice"
    BLOOMING = "blooming"
    PASSIONATE = "passionate"
    POPULAR = "popular"
    KING = "king"

class DebateStatus(str, enum.Enum):
    WAITING = "waiting"              # ?��?�?
    PROCEEDING = "proceeding"        # 진행 �?(추�???
    IN_PROGRESS_INTRO = "intro"      # ?�론
    IN_PROGRESS_REBUTTAL = "rebuttal" # 반론
    IN_PROGRESS_REREBUTTAL = "rerebuttal" # ?�반�?
    IN_PROGRESS_CONCLUSION = "conclusion" # 결론
    FINISHED = "finished"            # 종료


class BadgeType(str, enum.Enum):
    SEED = "씨앗 토론가"      # 신규 가입
    SPROUT = "새싹 토론가"    # 첫 토론 참여
    BLOOMING = "피어나는 토론가" # 토론 참여 20회
    PASSIONATE = "열혈 토론가"  # 토론 참여 100회
    POPULAR = "인기 토론가"    # 좋아요 30개
    KING = "토론왕"          # 최근 20판 승률 70%