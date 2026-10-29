
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.coins import router as coins_router
from app.api.routes.scanner import router as scanner_router
from app.api.routes.portfolio import router as portfolio_router


app = FastAPI(
    title="Crypto Intelligence Platform",
    version="0.1.0",
)

# Angular-Frontend darf lokal auf die API zugreifen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(coins_router, prefix="/api/v1")
app.include_router(scanner_router, prefix="/api/v1")
app.include_router(portfolio_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
