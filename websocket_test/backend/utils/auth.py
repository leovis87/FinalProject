"""
JWT 토큰 생성 및 검증
비밀번호 암호화 및 검증
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from src.models import User
import os

# ========================================
# 설정
# ========================================

# ⚠️ 실제 프로덕션에서는 환경변수로 관리!
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

# 비밀번호 암호화 컨텍스트
pwd_context = CryptContext(schemes = ["argon2"],
                           deprecated = "auto")

# OAuth2 스키마 (토큰 추출용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/auth/login")


# ========================================
# 비밀번호 관련 함수
# ========================================

def verify_password(plain_password: str,
                    hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시된 비밀번호 비교
    
    비유: 입력한 비밀번호를 암호화해서 저장된 것과 비교
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호를 암호화 (해싱)
    
    비유: "1234" → "$2b$12$abcd..." 같은 암호로 변환
    """
    return pwd_context.hash(password)


# ========================================
# JWT 토큰 관련 함수
# ========================================

def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None):
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 넣을 데이터 (예: {"sub": "user123"})
        expires_delta: 만료 시간 (기본: 7일)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


# ========================================
# 사용자 인증 함수
# ========================================

def authenticate_user(db: Session,
                      user_id: str,
                      password: str):
    """
    사용자 인증 (로그인 검증)
    
    Args:
        db: DB 세션
        user_id: 로그인 ID
        password: 비밀번호 (평문)
    
    Returns:
        User 객체 (성공) 또는 False (실패)
    """
    # 1. DB에서 사용자 찾기
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        return False
    
    # 2. 비밀번호 확인
    if not verify_password(password, user.hashed_password):
        return False
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 정보 가져오기
    
    비유: 토큰을 보여주면 "당신은 user123이군요!" 하고 확인
    
    Args:
        token: JWT 토큰 (자동으로 헤더에서 추출)
        db: DB 세션
    
    Returns:
        User 객체
    
    Raises:
        HTTPException: 토큰이 유효하지 않으면
    """
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "인증 정보를 확인할 수 없습니다",
        headers = {"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # 2. DB에서 사용자 찾기
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    활성화된 사용자만 허용
    
    비유: 계정이 정지되지 않은 사람만 통과
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다")
    
    return current_user