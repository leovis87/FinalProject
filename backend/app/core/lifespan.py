from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import date

from .database import init_db, engine, AsyncSessionLocal
from models.enums import AuthProvider
from services.user import user_service

TEST_USERS = [
    {"id": "test_user_001", "name": "김민준", "nickname": "팩트폭격기", "email": "user1@test.com", "birth_date": date(2014, 5, 12), "gender": "M"}, # 초등학생
    {"id": "test_user_002", "name": "이서연", "nickname": "논리정연", "email": "user2@test.com", "birth_date": date(2015, 9, 3), "gender": "F"},    # 초등학생
    {"id": "test_user_003", "name": "박지훈", "nickname": "중립기어", "email": "user3@test.com", "birth_date": date(2011, 2, 18), "gender": "M"},   # 중학생
    {"id": "test_user_004", "name": "최수진", "nickname": "핵심관통", "email": "user4@test.com", "birth_date": date(2010, 11, 27), "gender": "F"},  # 중학생
    {"id": "test_user_005", "name": "정우성", "nickname": "열린귀", "email": "user5@test.com", "birth_date": date(2008, 7, 6), "gender": "M"},      # 고등학생
    {"id": "test_user_006", "name": "한예슬", "nickname": "반론마스터", "email": "user6@test.com", "birth_date": date(2007, 12, 1), "gender": "F"}, # 고등학생
]

async def init_test_users():
    async with AsyncSessionLocal() as db:
        for user_data in TEST_USERS:
            try:
                await user_service.get_or_create_social_user(
                    db,
                    provider=AuthProvider.TEST,
                    provider_user_id=user_data["id"],
                    name=user_data["name"],
                    nickname=user_data["nickname"],
                    email=user_data["email"],
                    phone_number="010-0000-0000",
                    birth_date=user_data["birth_date"],
                    gender=user_data["gender"]
                )
            except Exception as e:
                print(f"테스트 유저({user_data['name']}) 생성 실패: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 앱 시작 ---
    await init_db()
    await init_test_users()

    # --- 앱 종료 ---
    yield
    if engine:
        await engine.dispose()