"""Routers package for API endpoints."""

from app.routers.deals import router as deals_router
from app.routers.comps import router as comps_router
from app.routers.dcf import router as dcf_router
from app.routers.pitchbook import router as pitchbook_router
from app.routers.news import router as news_router
from app.routers.documents import router as documents_router
from app.routers.ws import router as ws_router

__all__ = [
    "deals_router",
    "comps_router",
    "dcf_router",
    "pitchbook_router",
    "news_router",
    "documents_router",
    "ws_router"
]
