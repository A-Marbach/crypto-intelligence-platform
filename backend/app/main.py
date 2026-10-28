from fastapi import FastAPI
from app.api.routes.coins import router as coins_router

app = FastAPI(
    title="Crypto Intelligence Platform",
    version="0.1.0",
)

app.include_router(coins_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}