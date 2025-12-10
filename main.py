from fastapi import FastAPI
from config import settings
from routes import rooms, guests, reservations
from fastapi.openapi.utils import get_openapi
from logger import logger

app = FastAPI(
    title=settings.app_name,
    description="A comprehensive hotel management system API",
    version="1.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    # Generate original schema
    openapi_schema = get_openapi(
        title=settings.app_name,
        version="1.0.0",
        description="Hotel Management API",
        routes=app.routes
    )

    # Add BearerAuth scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Attach BearerAuth to all endpoints
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi



app.include_router(rooms.router)
app.include_router(guests.router)
app.include_router(reservations.router)



@app.get("/")
def read_root():
    return {
        "message": "Welcome to Hotel Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    logger.info("Health Check endpoint called")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
