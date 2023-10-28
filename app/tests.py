from pymongo import MongoClient


class MongoDBConnection:
    def __init__(self, host, port, database_name):
        self.host = host
        self.port = port
        self.database_name = database_name
        self.client = None

    def __enter__(self):
        self.client = MongoClient(self.host, self.port)
        self.db = self.client[self.database_name]
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        if self.client:
            self.client.close()


def get_todo_collection():
    with MongoDBConnection("localhost", 27017, "todo_app") as db:
        return db["todos"]


def get_user_collection():
    with MongoDBConnection("localhost", 27017, "todo_app") as db:
        return db["users"]


todo_collection = get_todo_collection()
user_collection = get_user_collection()
