from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.business import router as business_router
from app.api.category import router as category_router
from app.api.mention import router as mention_router
from app.api.resolution import router as resolution_router
from app.api.document import router as document_router
from app.api.extraction import router as extraction_router
from app.api.qa import router as qa_router


app = FastAPI(
    title="Business Mention Resolution Platform",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(business_router)
app.include_router(category_router)
app.include_router(mention_router)
app.include_router(resolution_router)
app.include_router(document_router)
app.include_router(extraction_router)
app.include_router(qa_router)


@app.get("/")
def root():
    return {
        "message": "Business Mention Resolution Platform API",
        "status": "running",
    }