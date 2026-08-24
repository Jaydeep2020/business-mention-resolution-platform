from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.business import router as business_router


app = FastAPI(
    title="Business Mention Resolution Platform",
    version="1.0.0",
)


app.include_router(
    auth_router
)

app.include_router(
    business_router
)


@app.get("/")
def root():

    return {
        "message": "Business Mention Resolution Platform API",
        "status": "running",
    }