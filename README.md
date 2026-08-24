# Amazon ATMS Auto-Claim Bot

An automated, stealth-enabled web scraping and automation bot built with Python and Playwright. This bot monitors the Amazon ATMS (Amazon Translation Management System) portal 24/7, automatically detects newly released translation jobs, claims them instantly, and sends real-time notifications to Telegram.

## Key Features

- **Stealth Mode**: Custom JavaScript injection and browser fingerprint spoofing to bypass anti-bot detection systems (e.g., hiding `navigator.webdriver`, spoofing WebGL, and mimicking real user behavior).
- **Smart Authentication**: Dynamically detects and handles both full login forms and "Quick Sign-In" session persistence.
- **Real-Time Monitoring**: Continuously polls the target page at configurable intervals, with automatic hard-reloads to prevent stale DOM states.
- **Instant Claiming**: Extracts job metadata (Weighted Words, Price) *before* submission, clicks the claim button, and verifies success via DOM state changes.
- **Telegram Notifications**: Sends formatted, real-time alerts to a Telegram chat upon startup, successful claims, or critical errors.
- **Self-Healing Architecture**: Automatically recovers from network drops, session expirations, or browser crashes by restarting the loop gracefully.

## Tech Stack

- **Language**: Python 3.12
- **Automation**: Playwright (Async API)
- **Stealth**: Custom `add_init_script` injections + `playwright-stealth`
- **Configuration**: `python-dotenv` for secure credential management
- **Logging**: `loguru` for structured, readable console output
- **Notifications**: `httpx` for async Telegram Bot API requests

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/auto-claim-bot.git
   cd auto-claim-bot


2. Create and activate a virtual environment
    ```bash
    python -m ven ven
    souirce venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies
   ```bash
    pip install -r requirements.txt
    playwright install chromium

4.**Configure Environment Variables:**
Create a .env file in the root directory and add your credentials:

LOGIN_URL=your_login_url
BOT_USERNAME=your_amazon_username
BOT_PASSWORD=your_amazon_password
TARGET_URL=your_target_url
   
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
   
HEADLESS=false  # Set to 'true' when deploying to a cloud VPS

1. **Run the bot:**
   ```bash
    python -m bot.main


# Project Structure
auto-claim-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point and main event loop
│   ├── browser.py           # Stealth browser initialization and configuration
│   ├── claimer.py           # Core logic: login, job detection, and claiming
│   ├── config.py            # Environment variable loading and defaults
│   └── notifier.py          # Telegram API integration
├── data/                    # Persistent browser profile (gitignored)
├── logs/                    # Debug screenshots and error logs (gitignored)
├── .env                     # Local environment variables (gitignored)
├── .gitignore
└── README.md

# Deployment (24/7)
While this bot can run locally, it is designed for continuous deployment. To run it 24/7 without keeping your personal computer on:

1. Provision a cheap Linux VPS (e.g., Oracle Cloud Always Free tier, DigitalOcean, or RackNerd).
2. Install Python, Playwright dependencies, and pm2.
3. Upload the code, set HEADLESS=true in your .env, and run:
    ```bash
    pm2 start "python -m bot.main" --name auto-claim-bot
    pm2 save
    pm2 startup

# DISCLAIMER
This project is built for educational purposes and to demonstrate advanced web automation, anti-detection techniques, and asynchronous Python programming. Users are responsible for complying with the Terms of Service of any platform they interact with.