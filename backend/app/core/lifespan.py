from fastapi import FastAPI
from contextlib import asynccontextmanager

from .database import init_db, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 앱 시작 ---
    await init_db()

    # --- 앱 종료 ---
    yield
    if engine:
        await engine.dispose()