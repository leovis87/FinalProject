'''
description:
    - LangGraph 전체 조합용 (like main.py)

Args:
    - config: LLM설정, 공통 도구, 환경 변수 설정
    - schemas: State, Pydandic 설정
    - nodes: LangGraph의 각종 Node + 로직 함수

Return:
    - LangGraph 완성품
'''
# 기본 설정
import os
import logging
import time
from datetime import datetime
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # LangGraph용 Memory -> 자동 기억장치 (RAM)
from langgraph.checkpoint.postgres import PostgresSaver # PostgreSQL용 Memory -> 자동 기억장치 (서버)

# State, Pydantic
from .schemas import (
    DebateState
)

# Node, Func
from .nodes import (
    analyze_topic_node, # Topic 설명 + 입론 2가지 추천
    pro_turn_node_user, pro_turn_node_ai, # 찬성측
    con_turn_node_user, con_turn_node_ai, # 반대측
    referee_node_ai, # 중재자 (비방, 욕설, 논점이탈)
    summary_node, # 찬 -> 반 -> 중재 -> 요약
    moderator_shared_node, # 사회자
    pro_feedback_node, con_feedback_node, # 개개인 feedback
    # 분기 처리
    should_continue_debate, # 찬->반 loop 분기
    debate_end_node, router_for_feedback, # 분기 처리용 fack 함수
)

# 🛠️ Test 단계에서만 활용. 추후 삭제 예정
from .config import GEMINI_MODELS

load_dotenv()


# ============================================
# 📂 logging 설정
# ============================================
logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.INFO,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'debate_mvp.log',
    encoding = 'utf-8'
)

# ============================================
# DB 설정
# ⚠️ Localhost, 사용자 정보에 맞춰 변경 필수
# ============================================
# 1. DB 연결 정보 (URI)
USER = os.getenv("USER", "user")
PASSWORD = os.getenv("PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "db_name")

# 1. DB 연결 정보
DB_URI = f"postgresql://{USER}:{PASSWORD}@localhost:5432/{DB_NAME}"

# 2. Connection Pool 생성 (Context Manager 권장)
def create_app_with_db():
    # pool은 일반적으로 앱 시작 시 1번만 만듦.
    pool = ConnectionPool(conninfo = DB_URI,
                          max_size = 20)
    
    # 3. PostgreSQL Checkpointer 인스턴스 생성
    postgre_checkpointer = PostgresSaver(pool)

    # 최초 1회 실행 시 테이블 자동 생성 (checkpoints, checkpoint_writes 등)
    postgre_checkpointer.setup()

    # 4. 컴파일
    return workflow.compile(checkpointer = postgre_checkpointer)

# ============================================
# Graph 구축
# ============================================
# StateGraph 인스턴스 생성
workflow = StateGraph(DebateState)

# ============================================
# Node 추가
# ============================================
# ai vs ai 용 node
# workflow.add_node('pro', pro_turn_node_ai)
# workflow.add_node('con', con_turn_node_ai)

# user_team vs user_tema 용 node
workflow.add_node('analyze_topic', analyze_topic_node)  # [Agent] topic 요약 및 입론 추천 
workflow.add_node('pro_turn', pro_turn_node_user)  # [찬성] 측 유져 턴
workflow.add_node('con_turn', con_turn_node_user)  # [반대] 측 유져 턴
workflow.add_node('referee_check_pro', referee_node_ai)  # [Chain LLM] 찬성 검사
workflow.add_node('referee_check_con', referee_node_ai)  # [Chain LLM] 반대 검사
workflow.add_node('summary', summary_node)  # [Chain LLM] 찬성, 반대 측 내용 정리 + 턴 증가
workflow.add_node('debate_end', debate_end_node)  # 분기 처리용 fack 함수

# 공통 분석 노드 (사회자 AI)
workflow.add_node('moderator_shared', moderator_shared_node)

# 프리미엄 회원: 개개인 피드백 💸 노드
workflow.add_node('pro_feedback', pro_feedback_node)
workflow.add_node('con_feedback', con_feedback_node)

# ============================================
# 시작점 설정
# ============================================
workflow.set_entry_point('analyze_topic')
# 입력 -> analyze_topic Node부터 시작

# ============================================
# Edge 연결: 토론 진행 (순서)
# ============================================
# ai vs ai 용 edge 연결
# workflow.add_edge('pro', 'con')
# workflow.add_edge('con', 'summary')

# [주제분석] ➔ [찬성🗣️] ➔ [심판⚖️] ➔ [반대🗣️] ➔ [심판⚖️] ➔ [요약📝]
# 1. 분석 -> 찬성 발언
workflow.add_edge('analyze_topic', 'pro_turn')

# 2. 찬성 발언 -> 찬성 검사
workflow.add_edge('pro_turn', 'referee_check_pro')

# 3. 찬성 검사 -> 반대 발언
workflow.add_edge('referee_check_pro', 'con_turn')

# 4. 반대 발언 -> 반대 검사
workflow.add_edge('con_turn', 'referee_check_con')

# 5. 반대 검사 -> 요약 (턴 증가 or 턴 종료)
workflow.add_edge('referee_check_con', 'summary')

# ============================================
# 분기 제어:
# ============================================
# Loop 제어
workflow.add_conditional_edges(
    'summary',                            # 출발 == 분기 시작점
    should_continue_debate,               # 조건 == 분기 로직
    {
        'continue': 'pro_turn',           # Loop
        'end': 'debate_end'               # 가상 노드 (분기용)
    }
)

# 토론 종료 -> 공통 분석
workflow.add_edge('debate_end', 'moderator_shared')

# 공통 분석 후 분기 (각 팀 개개인 feedback: 💎 프리미엄 회원)
workflow.add_conditional_edges(
    "moderator_shared",                   # 출발 == 분기 시작점
    router_for_feedback,                  # 조건 == 분기 로직 (유료 / 무료)

    # 🗺️ 매핑 (Router가 뱉는 문자열 -> 실제 노드 이름)
    # 리스트를 뱉을 땐, 굳이 매핑 안 해도 되지만 명시적으로 적어주는 게 안전함.
    {
        "pro_feedback": "pro_feedback",
        "con_feedback": "con_feedback",
        "debate_end": "debate_end"
    }
    # 💡 팁: 사실 노드 이름과 리턴값이 같으면 이 딕셔너리 생략 가능.
)

# 피드백 완료 후 종료
workflow.add_edge('pro_feedback', END)
workflow.add_edge('con_feedback', END)

# ============================================
# 6-6. 컴파일
# ============================================
# Graph 컴파일 시 checkpointer 추가
# 💡 추후 DB (PostgreSQL checkpointer로 연결 => 휘발 메모리 + DB 완성)
memory = MemorySaver()  # Ram 저장 == 휘발 but 빠름!!
debate_app = workflow.compile(checkpointer = memory,
                              
                              # ⭐ [Option] 노드의 key 값 (예: 'pro_turn')을 넣으면,
                              #    해당 노드에서 멈춤!
                              #    추가로 멈추게 하려면 추가도 가능함.
                              #    🤖 vs 🤖는 interrupt_before를 없애면 됨!
                              interrupt_before = [
                                  'pro_turn',
                                  'con_turn'
                                ]
                            )

# ✅ PostgreSQL Saver 사용하여 실행 시
# debate_app_with_postgres = create_app_with_db()


# 📌 Flow:
# 
#    START
#      ↓
#  [analyze]
#      ↓
#  [pro_turn] → [referee] → [con_turn] → [referee] → [summary]
#      ↑                                                  ↓
#      └─────────────────────────── continue ─────────────┘
#                                       ↓ end
#                                  [debate_end]
#                                       ↓
#                               [shared_moderator]
#                            free ↙          ↘ premium
#                              END    ┌────────┴────────┐
#                                     │                 │
#                               [pro_feedback]  [con_feedback]
#                                     │                 │
#                                     └────────┬────────┘
#                                              ↓ click
#                                       [deep_research]
#                                              ↓
#                                             END



# ============================================
# 🛠️. 테스트!
# ============================================
if __name__ == '__main__':
    logging.info("🎭 토론 시뮬레이션 (Loop)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 초기 State 설정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    start_time1 = time.time()

    initial_state = {
        'room_id': 'room_001',
        'topic': "교내 스마트폰 소지 및 사용 금지",
        
        # 1. 참가자 (is_premium 플래그 포함)
        'pro_users': [
            {'user_id': 'user_A', 'user_name': '김철수', 'is_premium': True},  # 💎
            {'user_id': 'user_B', 'user_name': '이민수', 'is_premium': False}, # 🆓
            {'user_id': 'user_C', 'user_name': '박지영', 'is_premium': False},
        ],
        'con_users': [
            {'user_id': 'user_D', 'user_name': '최영희', 'is_premium': False},
            {'user_id': 'user_E', 'user_name': '강동욱', 'is_premium': True},  # 💎
            {'user_id': 'user_F', 'user_name': '정수아', 'is_premium': False},
        ],

        # 2. 토론 진행
        'messages': [],
        'current_turn': 1,
        'max_turns': 3,    # 테스트용 짧게
        'summary_history': [],

        # 3. 실시간 중재
        'referee_warnings': [],

        # 4. 종료 후 분석 (변경 사항 반영!)
        'moderator_report': None,      # 공통 성적표
        'premium_feedbacks': {},       # 유료 심층 피드백
        'topic_analysis': None,        # 주제 분석 결과

        # 5. Latest messages (토론자용)
        'latest_pro_message': '',
        'latest_con_message': ''
    }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 실행
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    result = debate_app.invoke(
        initial_state,              # 방 생성시 필요한 내용들을 여기에 넣음.
        config = {
            'configurable': {
                'thread_id': 'debate_room_001',
                'temp': 0.0,
                'model': GEMINI_MODELS['flash'],
                'token': 2048,
                'is_stream': True
            },
            'callbacks': []
        }
    )
    print(dir(result))
    print(result.values())
    for k, v in result.items():
        print("Key: ", k)
        print("Value: ", v)