from pydantic import BaseModel, Field
from typing import (
    List, Dict, Literal,
    Any, Optional,
    TypedDict, Annotated
)

import operator

def update_dict(current: dict,
                new_data: dict) -> dict:
    '''
    description:
        - 기존 딕트에 새 데이터를 병합(Merge)하는 리듀서
    '''
    if not current:
        return new_data
    
    return {
        **current,
        **new_data
    }

# ==============================================================================
# 🗃️ Pydantic 정의
# ==============================================================================
# ==============================================================================
# 📚 Topic 설명, 입론 추천용
# ==============================================================================
class TopicBriefing(BaseModel):
    '''
    description:
        - Topic 요약 1문장
        - 각 측 입론 추천 2가지
    '''
    description: str = Field(
        description = '참가자들이 주제를 이해하기 쉽게 1문장'
    )

    pro_args: List[str] = Field(
        description = '찬성 입론을 위한 핵심 논거 2가지'
    )

    con_args: List[str] = Field(
        description = '반대 입론을 위한 핵심 논거 2가지'
    )

# ==============================================================================
# 👨‍⚖️ 중재자 AI 출력 제한용
# ==============================================================================
class RefereeDecision(BaseModel):
    '''
    description:
        1. 사용자의 context를 확인
        2. 비속어, 비방, 논점 이탈 시 warning
    '''
    has_issue: bool = Field(
        description = '발언에 위반 사항(비속어, 인신공격, 논점 이탈)이 있으면 True, 없으면 False'
    )

    issue_type: Optional[Literal['profanity', 'personal_attack', 'off_topic']] = Field(
        description = '위반 유형 (profanity: 비속어, personal_attack: 인신공격, off_topic: 주제 이탈). 위반이 없으면 None'
    )

    message: str = Field(
        description = '위반 시 사용자에게 전달할 경고 메시지. 위반이 없으면 빈 문자열'
    )

# ==============================================================================
# 🎙️ 사회자 AI 출력 제한용
# ==============================================================================
#   📊 [Sub Schema] 평가 항목별 세부 점수
# ==============================================================================
class ScoreDetail(BaseModel):
    '''
    description:
        - 각 평가 항목에 대한 세부 점수 (각 항목 만점 기준 상이함)
    '''
    clarity: int = Field(...,
                         description = "주장 명확성 (0~25점)")

    evidence: int = Field(...,
                          description = "근거 적합성 (0~30점)")

    interaction: int = Field(...,
                             description = "상호작용/반응 (0~25점)")

    attitude: int = Field(...,
                          description = "토론 태도 (0~20점)")

    @property
    def total(self) -> int:
        return self.clarity + self.evidence + self.interaction + self.attitude

# ==============================================================================
#   🏆 [Sub Schema] 팀별 종합 평가 (점수 + 팀 피드백)
# ==============================================================================
class TeamEvaluation(BaseModel):
    '''
    description:
        - 한 팀(찬성 / 반대)에 대한 종합 평가 결과
    '''
    total_score: int = Field(...,
                             description = "총점 (100점 만점)")
    
    scores: ScoreDetail = Field(...,
                                description = "항목별 세부 점수")
    # {
    #     "clarity": 22,
    #     "evidence": 25,
    #     "interaction": 20,
    #     "attitude": 18
    # }
    
    feedback_text: str = Field(...,
                               description = """해당 팀에 대한 상세 평가 리포트 전문.
                                요약하지 말고, [주장 명확성], [근거 적합성], [상호작용], [태도] 각 항목별 상세 평가와 
                                Fact-check 결과, 구체적인 근거를 모두 포함한 '긴 줄글(Markdown)' 형태로 작성할 것.
                                """)
    
    fact_check_result: Optional[str] = Field(None,
                                             description = "주요 주장에 대한 팩트체크 결과 (문제없으면 None)")

# ==============================================================================
#   👨‍⚖️ [Main Schema] 사회자 최종 리포트 (DB 저장용 Root)
# ==============================================================================
class ModeratorReport(BaseModel):
    '''
    description:
        - 사회자(Moderator)의 최종 분석 결과 리포트.
        - 이 obj 하나를 DB의 JSON컬럼에 저장하거나, Front-end로 전송해서 사용
    '''
    # 1. 전체 총평
    general_summary: str = Field(...,
                                 description = "전체 토론에 대한 총평 및 요약")
    
    # 2. 팀별 평가 (구조화 데이터)
    pro_eval: TeamEvaluation = Field(...,
                                     description = "[찬성] 팀 평가 결과")
    con_eval: TeamEvaluation = Field(...,
                                     description = "[반대] 팀 평가 결과")
    
    # 3. MVP 선정 (Optional)
    best_player: Optional[str] = Field(None,
                                       description = "MVP(최우수 토론자)가 있다면 선정")

# ==============================================================================
# 📊 개인 feedback AI 출력 제한용
# ==============================================================================
#   📊 [Sub Schema] 심층 개인 feedback point
# ==============================================================================
class DeepFeedbackPoint(BaseModel):
    '''
    description:
        - 개인 feedback용 포인트를 제한하는 sub schema
    '''
    turn: int = Field(
        ...,
        description = "해당 발언이 있었던 턴 번호"
    )

    original_text: str = Field(
        ...,
        description = "사용자의 원래 발언 내용 (일부 발췌)"
    )

    critique: Optional[str] = Field(
        description = "비판 및 교정 내용 (논리적 오류, 표현 등)",
        default = "분석 내용 없음"
    )

    suggestion: Optional[str] = Field(
        description = "개선된 표현 제안",
        default = "제안 내용 없음"
    )


# ==============================================================================
#   📊 [Main Schema] 심층 개인 feedback coaching 최종 리포트 (DB 저장용 Root)
# ==============================================================================
class PersonalCoachingReport(BaseModel):
    '''
    description:
        - DeepFeedbackPoint를 받아 DB용 root를 만드는 main schema
    '''
    user_id: str = Field(
        ...,
        description = "대상 user_id"
    )

    strength: List[str] = Field(
        ...,
        description = "발견된 강점 3가지"
    )

    weakness: List[str] = Field(
        ...,
        description = "보완할 점 3가지"
    )

    detailed_points: List[DeepFeedbackPoint] = Field(
        ...,
        description = "발언별 디테일 코칭"
    )

    recommended_reading: Optional[str] = Field(
        None,
        description = "추천 학습 자료나 키워드"
    )

# ============================================
# State 정의
# ============================================
class DebateState(TypedDict):
    '''
    discription:
        - 실전 토론 플랫폼 State (Agent + Chain LLM 통합용)
    '''
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 기본 정보
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    room_id: int                # 토론방 ID
    topic: str                  # 토론 주제
    # [
    #   {'topic': ' ... ', 'pro': ' ... ', 'con': ' ... '},
    #   {'topic': ' ... ', .....}, 반복
    # ]
    topic_analysis: Optional[TopicBriefing]
    level: Optional[str]

    #     LEVEL_MAPPING = {
    #         "elementary_low": "초등_저학년",
    #         "elementary_high": "초등_고학년",
    #         "middle": "중학생",
    #         "high": "고등학생",
    #         "all": None  # 'all'인 경우 필터링을 하지 않도록 처리 필요
    #     }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 각 팀별 참가자 정보
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    pro_users: List[Dict[str, str]]             # [찬성] 팀 사용자 목록
    # [
    #   {'user_id': 'user_A', 'user_name': '김철수', 'is_premium': True},
    #   {'user_id': 'user_B', 'user_name': '이민수', 'is_premium': False},
    #   {'user_id': 'user_C', 'user_name': '박지영', 'is_premium': False},
    # ]

    con_users: List[Dict[str, str]]             # [반대] 팀 사용자 목록
    # [
    #   {'user_id': 'user_D', 'user_name': '최영희', 'is_premium': False},
    #   {'user_id': 'user_E', 'user_name': '강동욱', 'is_premium': True},
    #   {'user_id': 'user_F', 'user_name': '정수아', 'is_premium': False},
    # ]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 토론 진행
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Node return에서
    # {'messages': [새_메시지]} -> 기존 리스트 뒤에 추가 됨!!!!
    messages: Annotated[List[Dict[str, Any]], operator.add] # 전체 대화 기록 list 객체
    # [
    #   {
    #       'turn': 1,
    #       'role': 'pro',
    #       'user_id': 'user_A',
    #       'user_name': '김철수',  # nick_name
    #       'content': '최저임금 인상은...'
    #   },
    #   {
    #       'turn': 1,
    #       'role': 'con',
    #       'user_id': 'user_D',
    #       'user_name': '최영희',  # nick_name
    #       'content': '하지만 부작용이 큽니다...'
    #   },
    # ]
    current_turn: int           # 현재 턴
    max_turns: int              # 최대 턴

    summary_history: Annotated[List[str], operator.add]  # 매 턴마다 summary ai가 요약한 메시지 이력

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 실시간 중재 (referee_ai)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    referee_warnings: Annotated[List[Dict[str, Any]], operator.add] # 경고 내역 list 객체
    # [
    #   {
    #       'turn': 1,
    #       'user_id': 'user_A',
    #       'type': 'profanity, # or 'off_topic',
    #       'message': '비속어 감지됨' 
    #   }
    # ]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 토론 종료 후 사회자 분석
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    moderator_report: Optional[ModeratorReport] # 전체 총평
                                                # 상세내용 하기 pydantic 참조

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 💎 [Premium] 유료 사용자 전용 심층 피드백
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    premium_feedbacks: Annotated[Dict[str, PersonalCoachingReport], update_dict]
    # Key: User ID (예: "user_A")
    # Value: PersonalCoachingReport 객체 (아래는 구조 예시)
    # {
    #   "user_id": "user_A",
    #   "strength": [
    #       "논리적 구조가 매우 탄탄합니다.",
    #       "적절한 비유를 사용하여 청중의 이해를 도왔습니다.",
    #       "상대방의 발언을 경청하는 태도가 돋보입니다."
    #   ],
    #   "weakness": [
    #       "발언 속도가 다소 빨라 전달력이 떨어질 수 있습니다.",
    #       "통계 자료의 출처를 명확히 밝히지 않았습니다.",
    #       "반박 시 감정적인 단어 선택이 보입니다."
    #   ],
    #   "detailed_points": [
    #       {
    #           "turn": 1,
    #           "original_text": "솔직히 그건 말이 안 된다고 생각하고요...",
    #           "critique": "감정적이고 공격적인 표현('말이 안 된다')은 설득력을 낮춥니다.",
    #           "suggestion": "그 부분은 현실적인 여건을 고려했을 때 다소 무리가 있다고 생각합니다."
    #       },
    #       {
    #           "turn": 3,
    #           "original_text": "대다수의 사람들이 그렇게 생각합니다.",
    #           "critique": "'대다수'라는 모호한 표현보다는 구체적인 수치를 제시하는 것이 좋습니다.",
    #           "suggestion": "2024년 통계청 자료에 따르면, 약 70%의 시민이 이에 동의했습니다."
    #       }
    #   ],
    #   "recommended_reading": "키워드: '비폭력 대화법', '로지컬 씽킹'"
    # }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 추후 사용할 가능성이 있는 것들
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    user_input: str             # 사용자 입력
    latest_pro_message: str     # 찬성 최신 발언
    latest_con_message: str     # 반대 최신 발언
    needs_search: bool          # 검색 필요 여부 (판단 결과)
    search_result: str          # 검색 결과
    final_response: str         # 최종 응답
    current_date: str           # 현재 날짜 명시적 전달용

# 📌 설명:
# 실전 토론 플랫폼에 필요한 모든 데이터를 담는 State
# 
# 핵심:
# - messages: user_id 포함해서 누가 말했는지 추적
# - pro_users, con_users: 각 팀 사용자 목록
# - referee_warnings: 실시간 경고
# - pro_feedbacks, con_feedbacks: 개인별 맞춤 피드백