from typing import Dict, List, Tuple, Optional, Union
import anthropic
import os
import logging
import torch

# ===== LLM model selector =====
Use_Claude = True

# ============================================================================
# Clude API_key 호출
# anthropic.Anthropic() => API 클라이언트 생성
# ============================================================================
client = anthropic.Anthropic(
    api_key = os.environ.get("ANTHROPIC_API_KEY")
)

# ============================================================================
# Claude models - claude API
# models["sonnet"] 으로 모델명 로드
# ============================================================================
models = {
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
    "opus": "claude-opus-4-20250514"
}

# 저렴이: models['haiku']
# 기본: models['sonnet']


# ============================================================================
# Claude models - claude API
# 사용 함수들
# ============================================================================
def set_prompt(role: str,
                content: str) -> Dict:
    """
    API에게 prompt를 주입하기 위한 메시지 구조 생성
        role: "user", "assistant", "system" 중 하나
        content: 메시지 텍스트
    """
    return {
        "role": role,
        "content": content
    }

conversation = []

def chat_haiku(query: str):
    # 1. 사용자 입력 추가

    conversation.append(set_prompt("user", query))

    # 2. 모델 호출

    response = client.messages.create(
        model = models['haiku'],        # 사용할 모델 (위에서 보고 선택)
        max_tokens = 1024,
        messages = conversation         # 지금까지의 대화 히스토리 전달
    )

    # 3. 모델 응답 추출
    answer = response.content[0].text

    # 4. conversation에 기록
    conversation.append(set_prompt("assistant", answer))

    return answer

def chat_sonnet(query: str):
    # 1. 사용자 입력 추가

    conversation.append(set_prompt("user", query))

    # 2. 모델 호출

    response = client.messages.create(
        model = models['sonnet'],        # 사용할 모델 (위에서 보고 선택)
        max_tokens = 1024,
        messages = conversation         # 지금까지의 대화 히스토리 전달
    )

    # 3. 모델 응답 추출
    answer = response.content[0].text

    # 4. conversation에 기록
    conversation.append(set_prompt("assistant", answer))

    return answer