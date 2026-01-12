from sqlalchemy import select
from typing import (List, Dict, Tuple,
                    Union, Optional, Generator)
from .database import (SessionLocal, get_db)
from src.models import Message
import anthropic
import os
# ─────────────────────────────────────
# 📊 한국인 토론 예상 규모
# [보통 토론]
# - 10턴 × 4명 × 평균 100자 = 4,000자
# - 토큰: ~2,000개
# ─────────────────────────────────────
# [매우 활발한 토론]  
# - 20턴 × 4명 × 평균 200자 = 16,000자
# - 토큰: ~8,000개
# ─────────────────────────────────────
# [극단적으로 긴 토론]
# - 50턴 × 4명 × 평균 300자 = 60,000자  
# - 토큰: ~30,000개
# ─────────────────────────────────────
# 방법 A: 한 번에 전송 (간단)
# 60,000자 토론 → Claude Haiku 1회 호출
# 입력: 30,000 토큰 × $0.25 / 1M = $0.0075
# 출력: 2,000 토큰 × $1.25 / 1M = $0.0025
# ─────────────────────────────────────
# 총 비용: $0.01 (약 13원)
# ─────────────────────────────────────
# 방법 B: 3청크로 나눠서
# 청크1 요약: 10,000 토큰 입력 + 1,000 출력 = $0.0037
# 청크2 요약: 10,000 토큰 입력 + 1,000 출력 = $0.0037  
# 청크3 요약: 10,000 토큰 입력 + 1,000 출력 = $0.0037
# 최종 판정: 3,000 토큰 입력 + 2,000 출력 = $0.0032
# ─────────────────────────────────────
# 총 비용: $0.0143 (약 19원)
# ─────────────────────────────────────
# 결론: 청크 방법이 43% 더 비쌉니다! 😱

"""
LLM API (default: Claude['haiku'])
❌ (fetch == HTML)
✅ requests, httpx
    - user (prompt): 사람이 모델에게 요청하는 입력.
    - assistant (output): 모델이 응답을 생성할 때 붙는 역할.
    - system (rule): 모델의 동작 지침, 규칙, 스타일 -> 대화 시작 시 설정
"""
#─────────────────────────────────────
# 마지막 요약 및 판정용 토큰 설정
MAX_TOKENS = 2048

# 마지막 요약용 모델 설정 (haiku, sonnet, opus 택1)
MODEL = 'haiku'
# ─────────────────────────────────────

db = SessionLocal()

def set_prompt(role: str,
               content: str) -> Dict:
    """
    API에게 prompt를 주입하기 위한 메시지 구조 생성
    ⭐ Claude API를 기준으로 role이 되어있습니다.
    role:
        - "user", "assistant", "system" 중 하나
    content:
        - 메시지 텍스트
    """

    return {
        "role": role,
        "content": content
    }

async def set_claude(model: str = 'haiku',
                     max_tokens: int = 2048,
                     role: str = "user",
                     content: str = ""):
    # ===== API Key 호출 =====
    # ⚠️ 개인의 API_KEY를 사용해야 합니다...
    # ========================
    client = anthropic.Anthropic(
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    )

    # ===== Model map =====
    models = {
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-3-5-haiku-20241022",
        "opus": "claude-opus-4-20250514"
    }

    # ===== Prompt set =====
    prompt = set_prompt(role, content)

    # ===== Set client (상세 모델 지정) =====
    response = client.messages.create(
        model = models[model],
        max_tokens = max_tokens,
        messages = [prompt]
    )

    return response

# async def get_ai_turn_change_message():
#     pass


# async def is_turn_complete():
#     pass

# async def is_debate_finished():
#     pass

def format_messages(messages: List[Dict]) -> str:
    """
    전체 message를 읽기 좋게 포맷
        - Message 객체 리스트를 텍스트로 변환
    """
    clear_messages = "\n".join([
        f"{msg.content}"
        for msg in messages
    ])
    
    return clear_messages

# async def chunk_summary():
#     """

#     """

#     pass

# 요약 및 판정 기능 합본
async def summary_and_judgment(db,
                           room_id: int) -> Dict:
    """
    유져의 side (예: 찬성 / 반대) 별로 토론 요약 및 판정
    """
    # 1. 찬성 축 주장
    pro_messages = db.query(Message).filter(
        Message.room_id == room_id,
        Message.side == '찬성'
    ).order_by(Message.created_at).all()

    # 2. 반대 측 주장
    con_messages = db.query(Message).filter(
        Message.room_id == room_id,
        Message.side == '반대'
    ).order_by(Message.created_at).all()

    # 3. LLM API에 전달할 프롬프트 (content) 생성
    content = f"""양측의 토론 주장을 요약하고, 승자를 판정 해줘.
    [찬성 측 주장]
    {format_messages(pro_messages)}

    [반대 측 주장]
    {format_messages(con_messages)}

    판정 기준:
    1. 논리적 일관성
    2. 근거의 타당성
    3. 반박의 효과성

    출력 형식:
    {{
        "pro_summary": "찬성 측 주장 요약",
        "con_summary": "반대 측 주장 요약",
        "winner": "찬성" or "반대",
        "reason": "판정 이유 설명"
    }}
"""

    response = set_claude(model = MODEL,
                          max_tokens = MAX_TOKENS,
                          role = 'user',
                          content = content)
    
    return response.content[0].text


# 판정 기능을 나누어 구현할 때 사용
# async def final_judgment(room_id):
    # message = ...