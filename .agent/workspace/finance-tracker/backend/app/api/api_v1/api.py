"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, transactions, categories, websocket

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])