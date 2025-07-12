from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import your authentication routes
from app.routes.auth import router as auth_router
from app.routes.portfolio import router as portfolio_router
from app.routes.social import router as social_router
from app.routes.portfolio_snapshot import router as portfolio_snapshot_router


# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Portfolio Platform API",
    description="Social portfolio tracking platform with posts, comments, and following",
    version="2.0.0"
)

# Configure CORS (allows frontend to talk to backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll make this more secure later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)
app.include_router(portfolio_router)
app.include_router(social_router)
app.include_router(portfolio_snapshot_router)


@app.get("/")
async def root():
    return {"message": "Portfolio Platform API v2.0 with Social Features!", "status": "success"}


@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy", 
        "environment": os.getenv("ENVIRONMENT", "development"),
        "message": "All systems operational",
        "features": ["authentication", "portfolios", "holdings", "social", "feed", "database"],
        "database": "unknown"
    }
    # Test database connection
    try:
        from app.database.connection import engine
        from sqlalchemy import text
        
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    return health_status

# Test endpoint - we'll replace this later with real portfolios
@app.get("/api/portfolios")
async def get_portfolios():
    return {
        "portfolios": [
            {
                "id": 1,
                "name": "Tech Growth Portfolio",
                "total_value": 125000,
                "daily_return": 2.5,
                "total_return": 15.8
            },
            {
                "id": 2,
                "name": "Value Dividend Portfolio", 
                "total_value": 85000,
                "daily_return": -0.3,
                "total_return": 8.2
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
