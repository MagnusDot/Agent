import asyncio
import sys

import uvicorn
from core import settings
from dotenv import load_dotenv

load_dotenv(override=settings.is_dev())

if __name__ == "__main__":
    # https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-operations
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=settings.is_dev())
