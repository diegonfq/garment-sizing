from fastapi import FastAPI
from src.api.v1.routers import garments

app = FastAPI(title="Garment Sizing API")
app.include_router(garments.router, prefix="/api/v1", tags=["Garments"])
