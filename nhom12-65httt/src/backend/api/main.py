from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routers import admin_bi, auth, chatbot, interactions, listings, reports, stubs
from src.backend.config.settings import settings

app = FastAPI(
    title="Smart Rental Housing API",
    description="Backend API cho Hệ thống tìm kiếm nhà thuê thông minh (Hà Nội) - Nhóm 12 (65HTTT)",
    version="1.1.0",
)

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(interactions.router)
app.include_router(reports.router)
app.include_router(admin_bi.router)
app.include_router(chatbot.router)
app.include_router(auth.router)
app.include_router(stubs.router)


@app.get("/")
def read_root():
    return {
        "project": "Hệ Thống Tìm Kiếm Nhà Thuê Thông Minh",
        "group": "Nhóm 12 - 65HTTT",
        "status": "online",
        "version": "1.1.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
