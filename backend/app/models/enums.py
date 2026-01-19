import enum

# 소셜 로그인
class AuthProvider(str, enum.Enum):
    TEST = "test"
    KAKAO = "kakao"
    NAVER = "naver"

# 토론 난이도
class DebateLevel(str, enum.Enum):
    ELEMENTARY_LOW = "elementary_low"   # 초(저학년)
    ELEMENTARY_HIGH = "elementary_high" # 초(고학년)
    MIDDLE = "middle"                   # 중
    HIGH = "high"                       # 고
    ALL = "all"                         # 전체

# 토론 과목 카테고리
class DebateCategory(str, enum.Enum):
    KOREAN = "korean"       # 국어
    SOCIAL = "social"       # 사회
    MORAL = "moral"         # 도덕
    ETHICS = "ethics"       # 윤리

# 토론방 상태
class DebateStatus(str, enum.Enum):
    WAITING = "waiting"                 # 대기
    IN_PROGRESS_INTRO = "in_progress_intro"           # 입론 중
    IN_PROGRESS_REBUTTAL = "in_progress_rebuttal"     # 반론 중
    IN_PROGRESS_REREBUTTAL = "in_progress_rerebuttal" # 재반론 중
    IN_PROGRESS_CONCLUSION = "in_progress_conclusion" # 최종 발언 중
    IN_PROGRESS_VOTING = "in_progress_voting"         # 평가 중
    FINISHED = "finished"               # 끝

# 토론 진영
class DebateRole(str, enum.Enum):
    PRO = "pro"             # 찬성
    CON = "con"             # 반대
    OBSERVER = "observer"   # 관전자

# 배지 종류
class BadgeType(str, enum.Enum):
    NOVICE = "새싹 토론가"
    BLOOMING = "피어나는 토론가"
    PASSIONATE = "열혈 토론가"
    POPULAR = "인기 토론가"
    KING = "토론왕"

class DebateStatus(str, enum.Enum):
    WAITING = "waiting"              # 대기 중
    PROCEEDING = "proceeding"        # 진행 중 (추가됨)
    IN_PROGRESS_INTRO = "intro"      # 입론
    IN_PROGRESS_REBUTTAL = "rebuttal" # 반론
    IN_PROGRESS_REREBUTTAL = "rerebuttal" # 재반론
    IN_PROGRESS_CONCLUSION = "conclusion" # 결론
    FINISHED = "finished"            # 종료