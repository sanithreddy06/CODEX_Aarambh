from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sample_project.backend.config import config
from sample_project.backend.controllers.auth_controller import router as auth_router
from sample_project.backend.controllers.product_controller import router as product_router
from sample_project.backend.controllers.order_controller import router as order_router

app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")

@app.get("/api/v1/health")
def api_health():
    return {"status": "ok", "service": config.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
