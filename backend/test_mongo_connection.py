from dotenv import load_dotenv
import os

load_dotenv()

from pymongo import MongoClient

uri = os.getenv("MONGODB_URI", "")

if not uri or "<username>" in uri or "xxxxx" in uri:
    print("ERROR: MONGODB_URI is still the placeholder.")
    print("Please update backend/.env with your real Atlas connection string.")
else:
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        info = client.server_info()
        print(f"SUCCESS: Connected to MongoDB Atlas!")
        print(f"Server version : {info['version']}")
        db = client["rbas_chatbot"]
        print(f"Database       : rbas_chatbot")
        print(f"Collections    : {db.list_collection_names()}")
        client.close()
    except Exception as e:
        print(f"FAILED: Could not connect to MongoDB Atlas.")
        print(f"Error: {e}")
