from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DATABASE = "todo_app"

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]


def get_db():
    try:
        yield db
    finally:
        client.close()
