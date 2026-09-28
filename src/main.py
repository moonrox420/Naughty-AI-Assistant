from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.websocket import ws_router
from src.cards.presets import seed_builtin_characters
from src.config import settings
from src.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize persistent storage and seed default presets
    await init_db()
    await seed_builtin_characters()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(ws_router)

# Mount Static Files and Generated Images
settings.setup_directories()
app.mount("/static/images", StaticFiles(directory=str(settings.IMAGES_DIR)), name="static_images")

import sys

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    static_dir = Path(sys._MEIPASS) / "static"
else:
    static_dir = Path(__file__).parent.parent / "static"

static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def serve_index():
    index_file = static_dir / "index.html"
    if not index_file.exists():
        return {"message": f"{settings.APP_NAME} backend running. Frontend index.html not yet initialized."}
    return FileResponse(str(index_file))
