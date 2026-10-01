import os 
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = 5890656811

api_key = os.getenv("API_KEY")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "YOUR_BOT_USERNAME"
)
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")