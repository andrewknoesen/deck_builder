from app.api.routes import auth, users, cards, decks, ai

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(decks.router, prefix="/decks", tags=["decks"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

