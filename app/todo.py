from bson import ObjectId
from fastapi import APIRouter

from .models import ToDo
from .db import todo_collection


router = APIRouter()


# The serializers
def single_serializer(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "name": todo["name"],
        "description": todo["description"],
        "complete": todo["complete"],
    }


def list_serializer(todos) -> list:
    return [single_serializer(todo) for todo in todos]


# Routes
router = APIRouter()


@router.get("/")
async def get_todos():
    return list_serializer(todo_collection.find())


@router.post("/")
async def post_todos(todo: ToDo):
    todo_collection.insert_one(dict(todo))


@router.put("/{id}")
async def update_todos(id: str, todo: ToDo):
    todo_collection.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(todo)})


@router.delete("/{id}")
async def delete_todos(id: str):
    todo_collection.find_one_and_delete({"_id": ObjectId(id)})
