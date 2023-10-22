from dataclasses import field
from enum import unique
from bson import ObjectId
from pydantic import BaseModel, EmailStr


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

    class config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


# class UserLogin(BaseModel):
#     username: str
#     password: str
