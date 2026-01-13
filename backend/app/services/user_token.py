import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from core.config import settings
from models.user import User

class UserTokenService:
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def _encode_token(self, user_id: int, expires_delta: timedelta, token_type: str) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": str(user_id), "type": token_type, "exp": expire}
        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
    
    def create_access_token(self, user_id: int) -> str:
        """Access Token 생성"""
        return self._encode_token(user_id, timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    
    def create_refresh_token(self, user_id: int) -> str:
        """Refresh Token 생성"""
        return self._encode_token(user_id, timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    
    def get_token_hash(self, token: str) -> str:
        """토큰 해싱 (SHA256) - DB 저장용"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def update_refresh_token(self, db: AsyncSession, user_id: int, refresh_token: str):
        """Refresh Token을 해싱하여 DB에 저장하고 만료 시간을 업데이트"""
        token_hash = self.get_token_hash(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                refresh_token_hash=token_hash,
                refresh_token_expires_at=expires_at,
                refresh_token_revoked=False
            )
        )
        await db.execute(stmt)
        await db.commit()

    def verify_token_payload(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                return None
            return user_id
        except JWTError:
            return None

user_token_service = UserTokenService()