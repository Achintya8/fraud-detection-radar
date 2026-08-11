from contextlib import asynccontextmanager
from fastapi import FastAPI
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
