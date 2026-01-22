import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.lifespan import lifespan
from routers import user, debate, rag
from core.socket_io import sio_app

app = FastAPI(lifespan=lifespan)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://61.40.108.149:5173"  # 외부 IP 프론트엔드 허용 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(debate.router)
app.include_router(rag.router)

@app.get("/")
def read_root():
    return {"message": "Debate High API"}

if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",  # localhost에서 0.0.0.0으로 변경 (외부 접속 허용의 핵심)
                port=8000,
                reload=True)

app.mount("/socket.io", sio_app)