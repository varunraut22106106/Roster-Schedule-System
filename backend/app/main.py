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
from app.routes.org_route import router as organization_router
from app.routes.employee_route import router as employee_router
from app.routes.policy_route import router as policies_router
from app.routes.availability_route import router as availability_router



app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(employee_router)
app.include_router(policies_router)
app.include_router(availability_router)