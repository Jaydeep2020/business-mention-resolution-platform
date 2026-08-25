from fastapi import FastAPI

from document_service.api.document import (
    router as document_router,
)

from document_service.api.internal import (
    router as internal_router,
)


app = FastAPI(
    title="Document Service",
    version="1.0.0",
)


app.include_router(
    document_router
)

app.include_router(
    internal_router
)


@app.get("/")
def root():

    return {
        "service": (
            "document-service"
        ),
        "status": "running",
    }