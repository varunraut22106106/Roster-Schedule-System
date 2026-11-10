from fastapi import FastAPI

app = FastAPI(
    title="Roster Scheduling System",
    description="Intelligent Employee Roster Management",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Roster Scheduling System API is running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
    
from app.routes.auth import router as auth_router

app.include_router(auth_router)