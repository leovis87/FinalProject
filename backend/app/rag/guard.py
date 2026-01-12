"""입력 질의를 검증/정제하는 가드 모듈.

이 모듈은 사용자 요청이 학습 맥락에 맞는지 판단하고,
필요 시 한국어 1문장으로 정제된 질의를 제공합니다.
검색 단계로 넘어가기 전에 불필요한 비용을 줄이기 위한 게이트입니다.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import List, Literal, Optional

from groq import Groq

Decision = Literal["OK", "REFINE", "REJECT", "FALLBACK"]


@dataclass
class GuardResult:
    """가드 결과를 표준화된 형태로 반환합니다."""

    decision: Decision
    reason_ko: str
    refined_query_ko: Optional[str]
    risk_tags: List[str]
    recommended_examples_ko: Optional[List[str]]

    def to_dict(self) -> dict:
        """라우터/서비스에서 바로 사용할 수 있도록 dict로 변환합니다."""
        return {
            "decision": self.decision,
            "reason_ko": self.reason_ko,
            "refined_query_ko": self.refined_query_ko,
            "risk_tags": self.risk_tags,
            "recommended_examples_ko": self.recommended_examples_ko,
        }


_URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
_REPEAT_RE = re.compile(r"(.)\1{6,}")


def _reject(reason_ko: str, tags: List[str]) -> GuardResult:
    return GuardResult(
        decision="REJECT",
        reason_ko=reason_ko,
        refined_query_ko=None,
        risk_tags=tags,
        recommended_examples_ko=[
            "중학생 수준의 인공지능 활용 토론 주제를 알려줘.",
            "고등학교 경제 과목에서 다룰 만한 토론 주제를 추천해줘.",
            "초등 고학년 환경 보호 관련 찬반 토론 주제를 알려줘.",
        ],
    )


def _fallback(reason_ko: str, tags: Optional[List[str]] = None) -> GuardResult:
    return GuardResult(
        decision="FALLBACK",
        reason_ko=reason_ko,
        refined_query_ko=None,
        risk_tags=tags or [],
        recommended_examples_ko=None,
    )


def _rule_check(user_query: str) -> Optional[str]:
    """빠른 규칙 기반 필터로 명백한 문제를 차단합니다."""
    q = user_query.strip()
    if not q:
        return "EMPTY"
    if len(q) < 4:
        return "TOO_SHORT"
    if _URL_RE.search(q):
        return "HAS_URL"
    if _REPEAT_RE.search(q):
        return "REPEAT"
    if len(q) > 300:
        return "TOO_LONG"
    return None


def guard_user_query(
    user_query: str,
    level: str,
    subject: str,
    allow_sensitive: bool,
    model_name: str = "llama-3.1-8b-instant",
    temperature: float = 0.0,
    max_tokens: int = 400,
) -> GuardResult:
    """질의를 OK/REFINE/REJECT/FALLBACK로 분류하고 필요 시 정제합니다."""
    rule_flag = _rule_check(user_query)
    if rule_flag == "EMPTY":
        return _reject("요청 문장이 비어 있습니다.", ["empty"])
    if rule_flag == "TOO_SHORT":
        return _reject("요청 문장이 너무 짧습니다.", ["too_short"])
    if rule_flag == "HAS_URL":
        return _reject("요청에 주소가 포함되어 있습니다.", ["has_url"])
    if rule_flag == "REPEAT":
        return _reject("반복 문자로 보이는 입력입니다.", ["repeat"])

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return _fallback("모델 키가 없어 분류를 수행할 수 없습니다.", ["no_api_key"])

    system = (
        "You are an input validator for student debate topics. "
        "You must output JSON only. "
        "decision must be one of OK|REFINE|REJECT|FALLBACK. "
        "reason_ko must be a short reason in Korean. "
        "If decision is REFINE, provide one Korean sentence in refined_query_ko. "
        "If decision is REJECT, provide 3 Korean examples in recommended_examples_ko."
    )

    prompt = f"""
[Input]
user_query: {user_query}
level: {level}
subject: {subject}
allow_sensitive: {allow_sensitive}
rule_flag: {rule_flag}

[Decision Rules]
- If allow_sensitive is false, student-inappropriate sensitive topics must be REJECT or FALLBACK.
- If rule_flag is TOO_LONG, decision must be REFINE and output a single Korean sentence.
- Output JSON only, no extra text.

[Output Format]
{{
  "decision": "OK|REFINE|REJECT|FALLBACK",
  "reason_ko": "...",
  "refined_query_ko": "One Korean sentence only when REFINE, otherwise null",
  "risk_tags": ["..."],
  "recommended_examples_ko": ["...", "...", "..."] or null
}}
"""

    client = Groq(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    except Exception:
        return _fallback("모델 호출에 실패했습니다.", ["model_error"])

    try:
        data = json.loads(resp.choices[0].message.content)
    except Exception:
        return _fallback("모델 응답을 해석하지 못했습니다.", ["parse_error"])

    decision = data.get("decision")
    if decision not in {"OK", "REFINE", "REJECT", "FALLBACK"}:
        return _fallback("모델 판단이 유효하지 않습니다.", ["invalid_decision"])

    if rule_flag == "TOO_LONG" and decision != "REFINE":
        decision = "REFINE"

    reason_ko = data.get("reason_ko") or "판단 사유가 제공되지 않았습니다."
    risk_tags = data.get("risk_tags") or []
    refined_query_ko = data.get("refined_query_ko")
    recommended_examples_ko = data.get("recommended_examples_ko")

    if decision == "REFINE":
        if not refined_query_ko or not isinstance(refined_query_ko, str):
            return _fallback("정제 문장이 제공되지 않았습니다.", ["missing_refine"])
    else:
        refined_query_ko = None

    if decision == "REJECT":
        if not isinstance(recommended_examples_ko, list) or len(recommended_examples_ko) < 3:
            recommended_examples_ko = [
                "중학생 수준의 인공지능 활용 토론 주제를 알려줘.",
                "고등학교 경제 과목에서 다룰 만한 토론 주제를 추천해줘.",
                "초등 고학년 환경 보호 관련 찬반 토론 주제를 알려줘.",
            ]
    else:
        recommended_examples_ko = None

    return GuardResult(
        decision=decision,
        reason_ko=reason_ko,
        refined_query_ko=refined_query_ko,
        risk_tags=risk_tags,
        recommended_examples_ko=recommended_examples_ko,
    )
