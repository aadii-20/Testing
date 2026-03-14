import os
import certifi
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

DB_NAME = "rbas_chatbot"

_client: MongoClient = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCAFile=certifi.where()
        )
    return _client


def get_db() -> Database:
    return get_client()[DB_NAME]


def init_db():
    try:
        db = get_db()

        # test connection
        get_client().admin.command("ping")

        # create unique index
        db["users"].create_index([("email", ASCENDING)], unique=True)

        print(f"[DB] ✅ Connected to MongoDB Atlas — database: '{DB_NAME}'")

    except Exception as e:
        print(f"[DB] ❌ WARNING: Could not connect to MongoDB Atlas: {e}")
        print("[DB] Check MONGODB_URI in backend/.env")