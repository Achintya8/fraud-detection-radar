import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import HealthResponse
from app.services.anomaly_detector import anomaly_detector
from app.services.velocity_checker import velocity_checker
from app.routers import score


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"Starting {settings.APP_NAME}...")
    anomaly_detector.load_artifacts()
    try:
        r = await velocity_checker.get_client()
        await r.ping()
        print("[Lifespan] Redis connection established successfully.")
    except Exception as e:
        print(f"[Lifespan] Warning: Redis ping failed at startup: {e}")
    yield
    # Shutdown logic
    print("[Lifespan] Shutting down application services...")
    await velocity_checker.close()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>Fraud Detection Radar API is running. Frontend missing.</h2>")


app.include_router(score.router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    redis_ok = False
    try:
        r = await velocity_checker.get_client()
        redis_ok = await r.ping()
    except Exception:
        redis_ok = False

    model_ok = anomaly_detector.is_loaded

    overall_status = "ok" if (redis_ok and model_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        redis_connected=redis_ok,
        model_loaded=model_ok
    )

