import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, escrows, disputes, token, stats

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tet API",
    description="Backend for the Tet decentralized escrow platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(escrows.router)
app.include_router(disputes.router)
app.include_router(token.router)
app.include_router(stats.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tet-api"}
