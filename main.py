from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="UDO API",
    description="Unternehmensdaten API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to UDO API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "udo-api"
    }


@app.get("/api/dummy")
async def dummy_endpoint():
    return {
        "data": "This is a dummy endpoint",
        "example": {
            "id": 1,
            "name": "Sample Company",
            "status": "active"
        }
    }
