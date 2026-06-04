"""
ShopeeFood AI API - Main Application Entry Point
Khởi tạo FastAPI server với đầy đủ middleware, routes, và static files.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Load biến môi trường từ .env (phải load TRƯỚC khi import services)
load_dotenv()

from routes.chat import router as chat_router
from routes.foods import router as foods_router
from routes.users import router as users_router

# ============================================================
# Logging configuration
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("shopeefood_ai")


# ============================================================
# Application Lifespan
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup và shutdown events"""
    # Startup
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        logger.info("🚀 ShopeeFood AI API khởi động với Gemini API")
    else:
        logger.warning("⚠️  ShopeeFood AI API khởi động ở chế độ FALLBACK (không có GEMINI_API_KEY)")
    logger.info("📍 Docs: http://localhost:8000/docs")
    logger.info("📍 Frontend: http://localhost:8000/")
    yield
    # Shutdown
    logger.info("👋 ShopeeFood AI API đã tắt")


# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title="ShopeeFood AI API",
    description=(
        "🍜 API Backend cho ShopeeFood AI Copilot - "
        "Trợ lý tìm món ăn thông minh sử dụng Google Gemini AI. "
        "Hỗ trợ gợi ý cá nhân hóa theo 3 nhóm: Học sinh, Sinh viên, Văn phòng."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================
# CORS Middleware - Cho phép frontend truy cập (dev mode)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev mode: cho phép tất cả origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Include Routers
# ============================================================
app.include_router(chat_router)
app.include_router(foods_router)
app.include_router(users_router)


# ============================================================
# Static Files - Serve frontend
# ============================================================
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )
    logger.info(f"📂 Static files mounted từ: {FRONTEND_DIR}")
else:
    logger.warning(f"⚠️  Thư mục frontend không tồn tại: {FRONTEND_DIR}")


# ============================================================
# Root & Health Check Endpoints
# ============================================================
@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve trang index.html cho frontend"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        content={
            "message": "ShopeeFood AI API đang chạy!",
            "docs": "/docs",
            "note": "Frontend chưa được tạo. Truy cập /docs để test API.",
        }
    )


@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Kiểm tra trạng thái hoạt động của API server.

    Trả về thông tin:
    - status: trạng thái server
    - gemini_api: có API key hay không
    - mode: chế độ hoạt động (live / fallback)
    """
    has_api_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "service": "ShopeeFood AI API",
        "version": "1.0.0",
        "gemini_api": "connected" if has_api_key else "not_configured",
        "mode": "live" if has_api_key else "fallback",
    }


# ============================================================
# Entry point - chạy trực tiếp bằng: python main.py
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
