import os

from dotenv import load_dotenv

load_dotenv()

ADMINS_ID = os.getenv("ADMINS_ID", "[]")
ADMIN_ID = 8622766758

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
api_key = os.getenv("API_KEY")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "YOUR_BOT_USERNAME"
)
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")

URL_ADMIN_PANEL = os.getenv("URL_ADMIN_PANEL")