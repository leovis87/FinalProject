import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.lifespan import lifespan
from routers import user, debate, rag, websocket

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(debate.router)
app.include_router(rag.router)
app.include_router(websocket.router) 

@app.get("/")
def read_root():
    return {"message": "Debate High API"}

if __name__ == "__main__":
    uvicorn.run("main:app",
                host="localhost",
                port=8000,
                reload=True)