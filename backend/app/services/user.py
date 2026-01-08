from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.enums import AuthProvider

class UserService:
    async def get_or_create_social_user(
        self, db: AsyncSession,
        provider: AuthProvider, provider_user_id: str,
        name: str, email: str = None, phone_number: str = None, birth_date: str = None,
        gender: str = None
    ) -> User:
        # 조회
        query = select(User).where(
            User.provider == provider,
            User.provider_user_id == provider_user_id
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return user
        
        # 신규 생성
        new_user = User(
            provider=provider,
            provider_user_id=provider_user_id,
            name=name,
            email=email,
            phone_number=phone_number,
            birth_date=birth_date,
            gender=gender
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
    
user_service = UserService()