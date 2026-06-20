from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.database import engine, Base
from app.models import user, job
from app.routers import auth, jobs, applications, ai

app = FastAPI(
    title="Job Tracker API",
    description="AI-powered job application tracker",
    version="1.0.0"
)

# CORS must be added BEFORE anything else
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(ai.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Job Tracker API is running"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Job Tracker API",
        version="1.0.0",
        description="AI-powered job application tracker",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Create tables after app and middleware are set up
Base.metadata.create_all(bind=engine)