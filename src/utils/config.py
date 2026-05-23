import os
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not found. Check that your .env file exist and contain the key.")
    raise ValueError("GROQ_API_KEY is missing from environment variables.")

logger.info("GROQ_API_KEY is loaded successfully.")
