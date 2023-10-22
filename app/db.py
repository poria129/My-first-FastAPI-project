from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["todo_app"]
todo_collection = db["todos"]
user_collection = db["users"]
