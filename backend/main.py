import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import audit, reports, watchlist

app = FastAPI(
    title="TokenScope API",
    description="Solana Token Due Diligence & Risk Intelligence Platform",
    version="1.0.0"
)

# CORS setup - supports localhost on any port and regex for local networks
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(watchlist.router)

@app.get("/health")
async def health_root():
    return {"status": "healthy", "service": "TokenScope API"}

@app.get("/")
async def root():
    return {
        "service": "TokenScope API",
        "description": "Solana Token Due Diligence Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
