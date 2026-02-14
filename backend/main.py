from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from config import settings
from database.postgres import create_tables
# from consumers.incident_consumer import IncidentConsumer
# from consumers.live_consumer import LiveConsumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    # Startup: initialize DB tables
    print("🚀 Starting ThreatLens AI...")
    await create_tables()
    print("✅ Database tables created")
    
    # Start Kafka consumers as background tasks
    # Uncomment when Kafka is running
    # from consumers.incident_consumer import IncidentConsumer
    # from consumers.live_consumer import LiveConsumer
    # asyncio.create_task(IncidentConsumer().run())
    # asyncio.create_task(LiveConsumer().run())
    # print("✅ Kafka consumers started")
    
    yield
    
    # Shutdown cleanup
    print("🛑 Shutting down ThreatLens AI...")


app = FastAPI(
    title=settings.APP_NAME,
    description="XAI-Enabled Cyber Defense Monitor",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "checking...",
            "kafka": "checking...",
            "redis": "checking..."
        }
    }


# REST routes
from api.routes import incidents, copilot, live
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["copilot"])
app.include_router(live.router, prefix="/api/live", tags=["live"])
# app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
# app.include_router(sandbox.router, prefix="/api/sandbox", tags=["sandbox"])
# app.include_router(blockchain.router, prefix="/api/blockchain", tags=["blockchain"])
# app.include_router(iocs.router, prefix="/api/iocs", tags=["iocs"])

# WebSocket routes
from api.websockets import alerts, live as live_ws
app.include_router(alerts.router, prefix="/ws")
app.include_router(live_ws.router, prefix="/ws")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
