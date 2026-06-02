import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
