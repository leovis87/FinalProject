import httpx
import uuid
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import AuthProvider
from services.user import user_service
from services.user_token import user_token_service
from core.config import settings
from core.database import get_db

router = APIRouter(prefix='/api/users', tags=['사용자'])

@router.get("/login/{provider}")
async def social_login(provider: AuthProvider):
    """로그인"""
    if provider == AuthProvider.KAKAO: # 카카오
        params = {
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
        }
        url = f"{settings.KAKAO_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    elif provider == AuthProvider.NAVER: # 네이버
        state = str(uuid.uuid4())
        params = {
            "client_id": settings.NAVER_CLIENT_ID,
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "response_type": "code",
            "state": state
        }
        url = f"{settings.NAVER_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    else:
        raise HTTPException(status_code=404, detail="지원하지 않는 소셜 플랫폼입니다.")
    
    return RedirectResponse(url)

@router.get("/callback/{provider}")
async def social_callback(
    provider: AuthProvider, code: str,
    response: Response, state: str = None, db:AsyncSession = Depends(get_db)
):
    """콜백"""
    social_id = None
    email = None
    name = None
    phone_number = None
    birth_date_obj = None

    async with httpx.AsyncClient() as client:
        # Access Token 발급 요청
        if provider == AuthProvider.KAKAO:
            token_res = await client.post(settings.KAKAO_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})

        elif provider == AuthProvider.NAVER:
            token_res = await client.get(settings.NAVER_TOKEN_URL, params={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "code": code,
                "state": state
            })

        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"{provider.value} 소셜 토큰 발급 실패: {token_res.text}")
        
        token_json = token_res.json()
        social_access_token = token_json.get("access_token")

        # 사용자 정보 조회
        if provider == AuthProvider.KAKAO:
            user_info_res = await client.get(settings.KAKAO_USER_INFO_URL, headers={
                "Authorization": f"Bearer {social_access_token}"
            })
            if user_info_res.status_code != 200:
                raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")
            
            user_info = user_info_res.json()
            social_id = str(user_info.get("id"))
            kakao_account = user_info.get("kakao_account", {})

            email = kakao_account.get("email")
            name = kakao_account.get("name", f"KakaoUser_{social_id[:4]}")
            phone_number = kakao_account.get("phone_number")

            birthyear = kakao_account.get("birthyear")
            birthday = kakao_account.get("birthday")

            _gender_raw = kakao_account.get("gender")
            if _gender_raw == "male":
                gender = "M"
            elif _gender_raw == "female":
                gender = "F"

            if birthyear and birthday:
                date_string = f"{birthyear}-{birthday[:2]}-{birthday[2:]}"
                try:
                    birth_date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()
                except ValueError:
                    print(f"날짜 변환 실패: {date_string}")
                    birth_date_obj = None

        elif provider == AuthProvider.NAVER:
            user_info_res = await client.get(settings.NAVER_USER_INFO_URL, headers={
                "Authorization": f"Bearer {social_access_token}"
            })
            if user_info_res.status_code != 200:
                raise HTTPException(status_code=404, detail="네이버 사용자 정보 조회 실패")
            
            user_info_json = user_info_res.json()
            response_obj = user_info_json.get("response", {})

            social_id = response_obj.get("id")
            email = response_obj.get("email")
            name = response_obj.get("name")
            phone_number = response_obj.get("mobile")

            birthyear = response_obj.get("birthyear")
            birthday = response_obj.get("birthday")

            gender = response_obj.get("gender")

            if birthyear and birthday:
                date_string = f"{birthyear}-{birthday}"
                try:
                    birth_date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()
                except ValueError:
                    print(f"날짜 변환 실패: {date_string}")
                    birth_date_obj = None

    if not social_id:
         raise HTTPException(status_code=400, detail="소셜 로그인 사용자 정보를 가져오지 못했습니다.")
    
    user = await user_service.get_or_create_social_user(
        db,
        provider=provider,
        provider_user_id=social_id,
        name=name,
        email=email,
        phone_number=phone_number,
        birth_date=birth_date_obj,
        gender=gender
    )

    access_token = user_token_service.create_access_token(user.user_id)
    refresh_token = user_token_service.create_refresh_token(user.user_id)
    await user_token_service.update_refresh_token(db, user.user_id, refresh_token)

    redirect_url = f"{settings.FRONTEND_URL}/social/callback?access_token={access_token}"
    response = RedirectResponse(url=redirect_url)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )

    return response