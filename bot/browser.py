import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from loguru import logger
from . import config

async def create_browser():
    logger.info(" Launching browser...")
    playwright = await async_playwright().start()

    headless = os.getenv("HEADLESS", "false").lower() == "true"

    launch_options = {
        "headless": False,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
            "--disable-web-security",
            "--allow-running-insecure-content",
        ]
    }

    browser = await playwright.chromium.launch(**launch_options)

    context = await browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-US",
        timezone_id="America/New_York"
    )

    stealth_js = """
        () => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'EN'] });
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGl Engine';
                return getParameter.apply(this, arguments);
            };
        }
    """
    
    await context.add_init_script(stealth_js)
    page = await context.new_page()
    
    logger.info(" Stealth Browser Ready!")
    
    return playwright, browser, context, page

async def get_page(context):
    pass