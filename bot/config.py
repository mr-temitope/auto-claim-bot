import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).parent.parent.resolve()

LOGIN_URL = os.getenv("LOGIN_URL", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "")
TARGET_URL = os.getenv("TARGET_URL", "")

CLAIM_BUTTON_SELECTOR = os.getenv(
    "CLAIM_BUTTON_SELECTOR",
    "button:has-text('Claim'), button:has-text('claim'), button:has-text('CLAIM'), [role='button']:has-text('Claim'), a:has-text('Claim')"
)

CLAIM_SUCCESS_SELECTOR = os.getenv(
    "CLAIM_SUCCESS_SELECTOR",
    "[role='alert'], .toast, .notification, .success, text=Claimed"
)

JOB_DESCRIPTION_SELECTOR = os.getenv(
    "JOB_DESCRIPTION_SELECTOR",
    ".job-description, .description, [data-job-description], .offer-details"
)

WAIT_AFTER_CLAIM = int(os.getenv("WAIT_AFTER_CLAIM", "5"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "2"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

USER_DATA_DIR = os.getenv("USER_DATA_DIR", str(BASE_DIR / "data" / "browser"))
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))

Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)