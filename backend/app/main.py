import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limit import limiter
from app.routes import (
    auth_routes,
    billing_routes,
    lead_routes,
    tenant_routes,
    websocket_routes,
)
from app.ws.manager import manager

app = FastAPI(title="Lead Tracker API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],  # locked to the actual frontend, never "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(tenant_routes.router)
app.include_router(lead_routes.router)
app.include_router(websocket_routes.router)
app.include_router(billing_routes.router)


@app.on_event("startup")
async def bind_websocket_loop():
    # Lets sync route handlers (running in FastAPI's thread pool) safely
    # schedule an async broadcast via run_coroutine_threadsafe.
    manager.bind_loop(asyncio.get_running_loop())


@app.get("/health")
def health_check():
    return {"status": "ok"}
