import enum

# ?åÏÖú Î°úÍ∑∏??
class AuthProvider(str, enum.Enum):
    TEST = "test"
    KAKAO = "kakao"
    NAVER = "naver"

# ?†Î°† ?úÏù¥??
class DebateLevel(str, enum.Enum):
    ELEMENTARY_LOW = "elementary_low"   # Ï¥??Ä?ôÎÖÑ)
    ELEMENTARY_HIGH = "elementary_high" # Ï¥?Í≥†Ìïô??
    MIDDLE = "middle"                   # Ï§?
    HIGH = "high"                       # Í≥?
    ALL = "all"                         # ?ÑÏ≤¥

# ?†Î°† Í≥ºÎ™© Ïπ¥ÌÖåÍ≥†Î¶¨
class DebateCategory(str, enum.Enum):
    KOREAN = "korean"       # Íµ?ñ¥
    SOCIAL = "social"       # ?¨Ìöå
    MORAL = "moral"         # ?ÑÎçï
    ETHICS = "ethics"       # ?§Î¶¨

# ?†Î°†Î∞??ÅÌÉú
class DebateStatus(str, enum.Enum):
    WAITING = "waiting"                 # ?ÄÍ∏?
    IN_PROGRESS_INTRO = "in_progress_intro"           # ?ÖÎ°† Ï§?
    IN_PROGRESS_REBUTTAL = "in_progress_rebuttal"     # Î∞òÎ°† Ï§?
    IN_PROGRESS_REREBUTTAL = "in_progress_rerebuttal" # ?¨Î∞òÎ°?Ï§?
    IN_PROGRESS_CONCLUSION = "in_progress_conclusion" # ÏµúÏ¢Ö Î∞úÏñ∏ Ï§?
    IN_PROGRESS_VOTING = "in_progress_voting"         # ?âÍ? Ï§?
    FINISHED = "finished"               # ??

# ?†Î°† ÏßÑÏòÅ
class DebateRole(str, enum.Enum):
    PRO = "pro"             # Ï∞¨ÏÑ±
    CON = "con"             # Î∞òÎ?
    OBSERVER = "observer"   # Í¥Ä?ÑÏûê

# Î∞∞Ï? Ï¢ÖÎ•ò
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
    WAITING = "waiting"              # ?ÄÍ∏?Ï§?
    PROCEEDING = "proceeding"        # ÏßÑÌñâ Ï§?(Ï∂îÍ???
    IN_PROGRESS_INTRO = "intro"      # ?ÖÎ°†
    IN_PROGRESS_REBUTTAL = "rebuttal" # Î∞òÎ°†
    IN_PROGRESS_REREBUTTAL = "rerebuttal" # ?¨Î∞òÎ°?
    IN_PROGRESS_CONCLUSION = "conclusion" # Í≤∞Î°†
    FINISHED = "finished"            # Ï¢ÖÎ£å
