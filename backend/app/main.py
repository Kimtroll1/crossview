from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.analyze import router as analyze_router

load_dotenv()

app = FastAPI(title="CrossView API", version="0.3.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.youtube.com",
        "https://youtube.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "CrossView API", "version": "0.3.5"}

@app.get("/")
async def root():
    return {"ok": True, "service": "CrossView API", "message": "Use /api/health or /api/analyze"}
