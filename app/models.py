from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool
    role: str


class ToDo(BaseModel):
    name: str
    description: str
    complete: bool
    username: str

    class config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class ToDoCreate(ToDo):
    username: str = Field(..., read_only=True)
