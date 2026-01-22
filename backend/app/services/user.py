from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.user import User
from models.enums import AuthProvider, BadgeType, UserTier

class UserService:
    async def get_or_create_social_user(
        self, db: AsyncSession,
        provider: AuthProvider, provider_user_id: str,
        name: str, email: str = None, phone_number: str = None, birth_date: str = None,
        gender: str = None,
        nickname: str = None,
    ) -> User:
        """소셜 로그인 유저 조회 또는 생성"""
        # 기존 유저 조회
        query = select(User).where(
            User.provider == provider,
            User.provider_user_id == provider_user_id
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return user
        
        # 신규 유저 생성 (초기 티어: 옹알이)
        new_user = User(
            provider=provider,
            provider_user_id=provider_user_id,
            name=name,
            nickname=nickname,
            email=email,
            phone_number=phone_number,
            birth_date=birth_date,
            tier=UserTier.ONG_AL_YI,  # 기본 티어 설정
            points=0,
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
    
    async def add_points(self, db: AsyncSession, user_id: int, amount: int) -> User | None:
        """포인트 추가 및 티어 자동 업데이트 로직"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        # 포인트 적립
        user.points += amount
        
        # 새로운 점수에 맞춰 티어 재계산 및 적용
        new_tier = self._calculate_tier(user.points)
        user.tier = new_tier
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
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
        
        # 좋아요 30개 이상 시 '인기 토론가' 뱃지 부여
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

    def _calculate_tier(self, points: int) -> UserTier:
        """포인트 구간별 티어 계산 로직"""
        if points < 100:
            return UserTier.ONG_AL_YI   # 100점 미만: 옹알이
        elif points < 300:
            return UserTier.BEGINNER    # 100점 이상: 입문자
        elif points < 600:
            return UserTier.AMATEUR     # 300점 이상: 아마추어
        elif points < 1000:
            return UserTier.PRO         # 600점 이상: 프로
        elif 2000 <= points: 
            return UserTier.MASTER      # 2000점 이상: 마스터
    
user_service = UserService()