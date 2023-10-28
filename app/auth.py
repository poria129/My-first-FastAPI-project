from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWSError, jwt
from pydantic import EmailStr
from starlette import status
from typing import Annotated

from .db import MongoDBManager
from .models import User
from .utils import hash_password, verify_password, pwd_context


router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "my-32-character-ultra-secret-123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        email: EmailStr = payload.get("email")
        if username is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate"
            )
        return {"username": username, "email": email}
    except JWSError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate"
        )


with MongoDBManager() as db:
    user_collection = db.users


def single_serializer(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "hashed_password": user["hashed_password"],
        "is_active": user["is_active"],
        "role": user["role"],
    }


def list_serializer(users) -> list:
    return [single_serializer(user) for user in users]


@router.post("/")
async def create_user(create_user_request: User):
    existing_user_email = user_collection.find_one({"email": create_user_request.email})
    if existing_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_user_username = user_collection.find_one(
        {"username": create_user_request.username}
    )
    if existing_user_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    create_user_model = User(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=hash_password(create_user_request.hashed_password),
        is_active=create_user_request.is_active,
        role=create_user_request.role,
    )

    user_collection.insert_one(dict(create_user_model))


@router.get("/")
def get_users():
    return list_serializer(user_collection.find())


@router.put("/{id}")
def update_user(id: str, user: User):
    user_collection.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(user)})


@router.delete("/{id}")
def delete_user(id: str, token: str = Depends(oauth2_scheme)):
    user_collection.find_one_and_delete({"_id": ObjectId(id)})


@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_collection.find_one({"username": form_data.username})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "email": user["email"]},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
