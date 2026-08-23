import asyncio
from loguru import logger
from .browser import create_browser
from .claimer import login, claim_loop
from .notifier import notify_startup, notify_error
from . import config

async def main():
    logger.info(" Starting Auto-Claim Bot...")
    await notify_startup()

    while True:
        playwright = None
        browser = None
        context = None
        page = None
        try:
            logger.info(" Initializing stealth browser and logging in...")
            playwright, browser, context, page = await create_browser()

            login_success = await login(page)

            if not login_success:
                logger.error(" Login failed - bot cannot continue")
                await notify_error("Login failed - retrying soon")
                await context.close()
                await browser.close()
                await playwright.stop()
                await asyncio.sleep(30)
                continue

            restart_needed = await claim_loop(page)

            if restart_needed is False:
                logger.warning(" Claim loop ended. Restarting bot...")

        except KeyboardInterrupt:
            logger.info(" Bot stopped by user (CTRL+C)")
            break
        except Exception as e:
            logger.error(f" Fatal error: {e}")
            await notify_error(f"Fatal error: {e}")

        finally:
            try:
                if context is not None:
                    await context.close()
                if browser is not None:
                    await browser.close()
                if playwright is not None:
                    await playwright.stop()
            except Exception:
                pass

            logger.info(" Waiting 10 seconds before restarting...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())