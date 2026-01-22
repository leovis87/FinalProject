from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.user import User
from models.enums import AuthProvider, BadgeType

class UserService:
    async def get_or_create_social_user(
        self, db: AsyncSession,
        provider: AuthProvider, provider_user_id: str,
        name: str, email: str = None, phone_number: str = None, birth_date: str = None,
        gender: str = None,
        nickname: str = None,
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
            nickname=nickname,
            email=email,
            phone_number=phone_number,
            birth_date=birth_date,
            gender=gender,
            badges=[{
                "name": BadgeType.SEED.value,
                "acquired_at": datetime.now().isoformat() 
            }]
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """ID로 사용자 조회"""
        query = select(User).where(User.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_nickname(self, db: AsyncSession, user_id: int, nickname: str) -> User | None:
        """닉네임 업데이트"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.nickname = nickname
            await db.commit()
            await db.refresh(user)
        return user
    
    async def like_user(self, db: AsyncSession, target_user_id: int) -> User | None:
            """좋아요 증가 및 인기 토론가 뱃지 체크 로직"""
            user = await self.get_by_id(db, target_user_id)
            if not user:
                return None
                
            user.likes_received += 1
            
            # 인기 토론가 (좋아요 30개 이상) 체크
            if user.likes_received >= 30:
                self._add_badge_local(user, BadgeType.POPULAR)
                
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

    def _add_badge_local(self, user: User, badge_type: BadgeType):
            """내부 헬퍼: 뱃지 중복 확인 후 추가"""
            badge_name = badge_type.value
            current_badges = list(user.badges) if user.badges else []
            
            if any(b.get('name') == badge_name for b in current_badges):
                return

            new_badge = {
                "name": badge_name,
                "acquired_at": datetime.now().isoformat()
            }
            current_badges.append(new_badge)
            user.badges = current_badges
    
user_service = UserService()