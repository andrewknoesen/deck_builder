from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One shared, connection-pooled client for the whole process lifetime —
    # the previous per-request `async with httpx.AsyncClient(...)` in
    # get_scryfall_service() paid a fresh TCP+TLS handshake to Scryfall on
    # every single request, which was the main source of latency on
    # Scryfall-backed pages (e.g. the landing page's hero card).
    app.state.scryfall_client = httpx.AsyncClient(
        base_url=settings.SCRYFALL_BASE_URL, timeout=30.0
    )
    yield
    await app.state.scryfall_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to MTG Deck Builder API"}

@app.get("/docs", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
