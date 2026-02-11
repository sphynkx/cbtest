import os
from dotenv import load_dotenv

load_dotenv()

CB_CONNSTR = os.getenv("CB_CONNSTR", "couchbase://127.0.0.1")
CB_USERNAME = os.getenv("CB_USERNAME", "admin")
CB_PASSWORD = os.getenv("CB_PASSWORD", "")

CB_BUCKET = os.getenv("CB_BUCKET", "comments")
CB_SCOPE = os.getenv("CB_SCOPE", "_default")
CB_COLLECTION = os.getenv("CB_COLLECTION", "_default")

DEFAULT_THREAD_ID = os.getenv("DEFAULT_THREAD_ID", "thread::demo")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))