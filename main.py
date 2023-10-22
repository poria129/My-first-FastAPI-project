from fastapi import FastAPI
from app import auth, todo


app = FastAPI()


app.include_router(auth.router)
app.include_router(todo.router)
