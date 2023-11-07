from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWSError, jwt
from starlette import status
from typing import Annotated

from app.db import MongoDBManager
from app.models import User
from app.utils import hash_password, verify_password


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


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        id: str = payload.get("id")
        if username is None or id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate"
            )
        return {"username": username, "id": id}
    except JWSError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate"
        )


def get_collection():
    with MongoDBManager() as db_manager:
        user_collection = db_manager.users
        return user_collection


# def get_collection(db_manager):
#     with db_manager:
#         user_collection = db_manager.users
#         return user_collection


# if __name__ == "__main__":
#     db_manager = MongoDBManager()
#     user_collection = get_collection(db_manager)


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
    existing_user_email = get_collection().find_one(
        {"email": create_user_request.email}
    )
    if existing_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_user_username = get_collection().find_one(
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

    get_collection().insert_one(dict(create_user_model))


@router.get("/")
def get_users():
    return list_serializer(get_collection().find())


@router.put("/{id}")
def update_user(id: str, user: User):
    get_collection().find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(user)})


@router.delete("/{id}")
def delete_user(id: str, token: str = Depends(oauth2_scheme)):
    get_collection().find_one_and_delete({"_id": ObjectId(id)})


@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_collection().find_one({"username": form_data.username})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "id": str(user["_id"])},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
