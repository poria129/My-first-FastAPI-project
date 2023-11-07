from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from app.db import MongoDBManager
from app.models import ToDoCreate, ToDo


router = APIRouter()

# with MongoDBManager() as db:
#     todo_collection = db.todos


def get_collection():
    with MongoDBManager() as db_manager:
        todo_collection = db_manager.todos
        return todo_collection


user_dependency = Annotated[dict, Depends(get_current_user)]


# The serializers
def single_serializer(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "name": todo["name"],
        "description": todo["description"],
        "complete": todo["complete"],
        "username": todo["username"],
    }


def list_serializer(todos) -> list:
    return [single_serializer(todo) for todo in todos]


@router.get("/")
def get_todos(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticaation Failed")
    return list_serializer(get_collection().find({"username": user.get("username")}))


@router.post("/")
def post_todos(todo: ToDoCreate, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticaation Failed")
    create_todo = ToDo(
        name=todo.name,
        description=todo.description,
        complete=todo.complete,
        username=user.get("username"),
    )
    get_collection().insert_one(dict(create_todo))


@router.put("/{id}")
def update_todos(id: str, todo: ToDo, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticaation Failed")
    get_collection().find_one_and_update(
        {"_id": ObjectId(id), "username": user.get("username")}, {"$set": dict(todo)}
    )


@router.delete("/{id}")
def delete_todos(id: str, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticaation Failed")
    get_collection().find_one_and_delete(
        {"_id": ObjectId(id), "username": user.get("username")}
    )
