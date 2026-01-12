"""가드 동작을 확인하기 위한 간단한 실행 스크립트."""
from rag.guard import guard_user_query


def run_demo() -> None:
    cases = [
        {
            "name": "REJECT",
            "user_query": "",
            "level": "중학교",
            "subject": "사회",
            "allow_sensitive": False,
        },
        {
            "name": "REFINE",
            "user_query": "가" * 320,
            "level": "고등학교",
            "subject": "국어",
            "allow_sensitive": False,
        },
        {
            "name": "OK",
            "user_query": "중학생을 위한 인공지능 활용 찬반 토론 주제를 추천해줘.",
            "level": "중학교",
            "subject": "기술",
            "allow_sensitive": False,
        },
        {
            "name": "FALLBACK",
            "user_query": "고등학생 경제 토론 주제를 알려줘.",
            "level": "고등학교",
            "subject": "경제",
            "allow_sensitive": False,
            "model_name": "__invalid_model__",
        },
    ]

    for case in cases:
        result = guard_user_query(
            user_query=case["user_query"],
            level=case["level"],
            subject=case["subject"],
            allow_sensitive=case["allow_sensitive"],
            model_name=case.get("model_name", "llama-3.1-8b-instant"),
        )
        print(f"[{case['name']}] {result.to_dict()}")


if __name__ == "__main__":
    run_demo()
