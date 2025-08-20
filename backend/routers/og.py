from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..services.og_scraper import fetch_og_metadata


router = APIRouter(prefix="/api", tags=["og"])


@router.get("/og-scrape")
async def og_scrape(url: str = Query(..., description="URL to scrape")) -> dict:
    try:
        data = await fetch_og_metadata(url)
        return {"title": data.title, "description": data.description}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to scrape OG metadata: {exc}")


