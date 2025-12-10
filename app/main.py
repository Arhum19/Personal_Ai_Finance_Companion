from app import models
from app.database import engine, Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, expense, category, income, summary

app = FastAPI(
    title="Finance Companion API",
    description="Personal finance management API",
    version="1.0.0"
)

# Create all tables
models.Base.metadata.create_all(bind=engine)

# CORS middleware (for future frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain when frontend is ready
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(income.router)
app.include_router(expense.router)
app.include_router(summary.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Finance Companion API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}