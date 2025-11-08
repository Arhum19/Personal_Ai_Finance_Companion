from app import models
from app.database import engine, Base
from fastapi import FastAPI
from app.routes import auth
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"Message": "Welcome to the Finance Companion API"}

