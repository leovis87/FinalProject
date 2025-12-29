"""
Claude API 토론 응답 테스트
- 실제 WebSocket/DB 없이
- Claude API만 테스트
"""

import asyncio
import os
from anthropic import Anthropic

# ========================================
# 설정
# ========================================

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ========================================
# 테스트 데이터 (실제 토론 시뮬레이션)
# ========================================

# 토론 주제
DEBATE_TOPIC = "학교 급식을 유기농으로 전환해야 한다"

# 5개 발언 (찬성/반대 번갈아가며)
MESSAGES = [
    {
        "side": "찬성",
        "nickname": "철수",
        "content": "학교 급식을 유기농으로 전환하는 것은 학생들의 건강을 위해 필수적입니다. 현재 급식에는 농약 성분이 검출되는 경우가 많고, 이는 성장기 아이들에게 악영향을 미칠 수 있습니다. 비용이 다소 증가하더라도 우리 아이들의 건강이 더 중요합니다."
    },
    {
        "side": "반대",
        "nickname": "영희",
        "content": "유기농 전환은 비용이 너무 많이 듭니다. 현실적으로 학교 예산으로는 감당하기 어렵고, 결국 학부모 부담으로 이어질 것입니다. 현재 급식도 철저한 검수를 거치기 때문에 안전성에는 문제가 없습니다."
    },
    {
        "side": "찬성",
        "nickname": "민수",
        "content": "예산 문제는 정부 지원으로 해결할 수 있습니다. 실제로 유럽 여러 나라에서는 학교 급식을 유기농으로 전환했고, 학생들의 건강 지표가 개선되었다는 연구 결과가 있습니다. 장기적으로 보면 의료비 절감 효과도 있습니다."
    },
    {
        "side": "반대",
        "nickname": "지연",
        "content": "유럽과 한국은 상황이 다릅니다. 우리나라는 학생 수가 많고 급식 규모가 크기 때문에 유기농 농산물 공급 자체가 어렵습니다. 또한 유기농이라고 해서 무조건 더 건강한 것도 아닙니다."
    },
    {
        "side": "찬성",
        "nickname": "준호",
        "content": "공급 문제는 지역 농가와 계약 재배로 해결할 수 있습니다. 실제로 일부 학교에서는 이미 성공적으로 운영 중입니다. 유기농 전환이 지역 농업 발전에도 도움이 되고, 학생들에게 올바른 먹거리 교육도 가능합니다."
    }
]

# ========================================
# AI 프롬프트 생성 함수
# ========================================

def format_messages_for_ai(messages):
    """메시지 목록을 Claude가 읽기 좋은 형태로 변환"""
    formatted = f"[토론 주제: {DEBATE_TOPIC}]\n\n"
    
    for i, msg in enumerate(messages, 1):
        formatted += f"발언 {i} [{msg['side']}] {msg['nickname']}:\n"
        formatted += f"{msg['content']}\n\n"
    
    return formatted


# ========================================
# 테스트 1: 5개 발언 후 중간 정리
# ========================================

async def test_interim_summary():
    """5개 발언 후 AI가 중간 정리를 하는 테스트"""
    
    print("=" * 60)
    print("🧪 테스트 1: 5개 발언 후 중간 정리")
    print("=" * 60)
    
    # 메시지 포맷팅
    debate_text = format_messages_for_ai(MESSAGES)
    
    # Claude API 호출
    prompt = f"""당신은 토론 사회자입니다.

{debate_text}

위 토론을 읽고 다음을 제공해주세요:
1. 지금까지의 핵심 쟁점 (2-3가지)
2. 찬성 측 주요 주장 요약 (1-2문장)
3. 반대 측 주요 주장 요약 (1-2문장)
4. 앞으로 논의가 필요한 부분 (1-2문장)

간결하고 명확하게 작성해주세요."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response = message.content[0].text
    
    print("\n📊 AI 중간 정리 결과:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()


# ========================================
# 테스트 2: 논점 이탈 감지
# ========================================

async def test_off_topic_detection():
    """논점 이탈 감지 테스트"""
    
    print("=" * 60)
    print("🧪 테스트 2: 논점 이탈 감지")
    print("=" * 60)
    
    # 정상 발언
    normal_message = {
        "side": "찬성",
        "nickname": "테스터",
        "content": "유기농 급식은 환경 보호에도 도움이 됩니다. 화학 비료를 사용하지 않아 토양 오염을 막을 수 있습니다."
    }
    
    # 이탈 발언
    off_topic_message = {
        "side": "반대",
        "nickname": "테스터2",
        "content": "그나저나 요즘 날씨가 너무 춥네요. 겨울방학은 언제 시작하나요?"
    }
    
    # 정상 발언 체크
    print("\n✅ 정상 발언 테스트:")
    print(f"발언: {normal_message['content']}")
    
    prompt1 = f"""토론 주제: "{DEBATE_TOPIC}"

새로운 발언: "{normal_message['content']}"

이 발언이 토론 주제와 관련이 있나요?
- "관련 있음" 또는 "관련 없음"으로만 답하고, 한 줄로 이유를 설명하세요."""

    message1 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt1}]
    )
    
    print(f"AI 판단: {message1.content[0].text}")
    
    # 이탈 발언 체크
    print("\n❌ 이탈 발언 테스트:")
    print(f"발언: {off_topic_message['content']}")
    
    prompt2 = f"""토론 주제: "{DEBATE_TOPIC}"

새로운 발언: "{off_topic_message['content']}"

이 발언이 토론 주제와 관련이 있나요?
- "관련 있음" 또는 "관련 없음"으로만 답하고, 한 줄로 이유를 설명하세요."""

    message2 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt2}]
    )
    
    print(f"AI 판단: {message2.content[0].text}")
    print()


# ========================================
# 테스트 3: 최종 요약 및 판정
# ========================================

async def test_final_judgment():
    """최종 요약 및 승패 판정 테스트"""
    
    print("=" * 60)
    print("🧪 테스트 3: 최종 요약 및 승패 판정")
    print("=" * 60)
    
    debate_text = format_messages_for_ai(MESSAGES)
    
    prompt = f"""당신은 공정한 토론 심판입니다.

{debate_text}

위 토론을 종합적으로 평가하여 다음을 제공해주세요:

1. 전체 토론 요약 (3-4문장)
2. 찬성 측 강점과 약점
3. 반대 측 강점과 약점
4. 승패 판정 (찬성 승/반대 승/무승부 중 선택)
5. 판정 이유 (2-3문장)

객관적이고 논리적으로 평가해주세요."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response = message.content[0].text
    
    print("\n🏆 AI 최종 판정 결과:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()


# ========================================
# 메인 실행
# ========================================

async def main():
    """모든 테스트 실행"""
    print("\n")
    print("🤖 Claude API 토론 응답 테스트 시작")
    print("=" * 60)
    print()
    
    # 테스트 1: 중간 정리
    await test_interim_summary()
    
    input("Enter를 눌러 다음 테스트로... ")
    
    # 테스트 2: 논점 이탈 감지
    await test_off_topic_detection()
    
    input("Enter를 눌러 다음 테스트로... ")
    
    # 테스트 3: 최종 판정
    await test_final_judgment()
    
    print()
    print("=" * 60)
    print("✅ 모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())