import asyncio
import re
from datetime import datetime
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from . import config
import json
from pathlib import Path

CLAIMED_JOBS_FILE = Path(config.LOG_DIR) / "claimed_jobs.json"

try:
    from .notifier import notify_job_seen, notify_job_claimed as _notify_job_claimed, send_telegram_message
    async def notify_job_claimed(description: str) -> None:
        await _notify_job_claimed(description)
except ImportError:
    async def notify_job_seen() -> None: pass
    async def notify_job_claimed(description: str) -> None: pass
    async def send_telegram_message(message: str, use_html: bool = False) -> None: pass

async def notify_error(message: str) -> None:
    logger.warning(f"Notifier error: {message}")
    try:
        from . import notifier
        parent_notify_error = getattr(notifier, "notify_error", None)
        if parent_notify_error is not None:
            await parent_notify_error(message)
    except ImportError:
        pass


async def login(page: Page) -> bool:
    logger.info(f" Navigating to login page: {config.LOGIN_URL}")

    await page.goto(
        config.LOGIN_URL,
        timeout=config.PAGE_LOAD_TIMEOUT,
        wait_until="domcontentloaded",
    )
    await page.wait_for_timeout(3000)

    if "login" not in page.url.lower() and "signin" not in page.url.lower():
        logger.info(" Already logged in (session persisted)")
        return True

    logger.info(" Filling login form...")
    await page.screenshot(path=f"{config.LOG_DIR}/debug_before_login.png")

    try:
        quick_signin_el = None
        
        try:
            quick_signin_el = page.get_by_role("button", name=re.compile(r"sign in as", re.IGNORECASE)).first
            await quick_signin_el.wait_for(state="visible", timeout=3000)
            logger.info("🔍 Found quick sign-in button (role-based)! Clicking...")
        except:
            quick_signin_el = None

        if not quick_signin_el:
            try:
                quick_signin_el = page.locator(f"button:has-text('{config.BOT_USERNAME}')").first
                await quick_signin_el.wait_for(state="visible", timeout=3000)
                logger.info(" Found quick sign-in button (username-based)! Clicking...")
            except:
                quick_signin_el = None
 
        if not quick_signin_el:
            try:
                quick_signin_el = page.locator("button.btn-primary, button[type='submit']").first
                button_text = await quick_signin_el.text_content()
                if button_text and ("sign in" in button_text.lower() or config.BOT_USERNAME.lower() in button_text.lower()):
                    await quick_signin_el.wait_for(state="visible", timeout=3000)
                    logger.info("🔍 Found quick sign-in button (primary button)! Clicking...")
                else:
                    quick_signin_el = None
            except:
                quick_signin_el = None

        if quick_signin_el:
            await quick_signin_el.click(force=True)
            await page.wait_for_timeout(2000)

            try:
                await page.wait_for_url(
                    lambda url: "login" not in url.lower() and "signin" not in url.lower(),
                    timeout=config.PAGE_LOAD_TIMEOUT,
                )
            except PlaywrightTimeout:
                pass
            
            logger.success(" Quick sign-in successful!")
            return True
        
        logger.info(" Using full login form...")
        elements = page.locator("input, button, [role='button']")
        username_el = None
        password_el = None
        submit_el = None
        count = await elements.count()

        for i in range(count):
            el = elements.nth(i)
            if not await el.is_visible():
                continue

            element_id = (await el.get_attribute("id") or "").lower()
            element_name = (await el.get_attribute("name") or "").lower()
            element_type = (await el.get_attribute("type") or "").lower()
            placeholder = (await el.get_attribute("placeholder") or "").lower()
            aria_label = (await el.get_attribute("aria-label") or "").lower()

            text = " ".join([element_id, element_name, element_type, placeholder, aria_label])

            if username_el is None and ("email" in text or "user" in text or "username" in text or "login" in text) and element_type in {"", "text", "email"}:
                username_el = el
                continue
                
            if password_el is None and ("pass" in text or "password" in text or "pwd" in text) and element_type == "password":
                password_el = el
                continue

            if submit_el is None and ("submit" in text or "sign in" in text or "login" in text or "continue" in text or "next" in text):
                submit_el = el

        if not username_el or not password_el or not submit_el:
            missing = []
            if not username_el: missing.append("username")
            if not password_el: missing.append("password")
            if not submit_el: missing.append("submit")
            raise RuntimeError(f"Could not find login fields: {', '.join(missing)}")

        logger.debug(f" Typing username: {config.BOT_USERNAME}")
        await username_el.fill(config.BOT_USERNAME, force=True)
        
        logger.debug(" Typing password")
        await password_el.fill(config.BOT_PASSWORD, force=True)

        entered_pwd = await password_el.input_value()
        if entered_pwd != config.BOT_PASSWORD:
            raise RuntimeError("Password was not entered correctly")

        logger.debug("️ Clicking submit button")
        await submit_el.click(force=True)

        try:
            await page.wait_for_url(
                lambda url: "login" not in url.lower() and "signin" not in url.lower(),
                timeout=config.PAGE_LOAD_TIMEOUT,
            )
        except PlaywrightTimeout:
            logger.warning(f" Login redirect timeout, but continuing. Current URL: {page.url}")

        logger.success(" Login successful!")
        return True

    except Exception as e:
        logger.error(f" Login error: {e}")
        await page.screenshot(path=f"{config.LOG_DIR}/login_error.png")
        return False


async def extract_job_details_before_claim(page: Page) -> dict:
    try:
        weighted_words = "N/A"
        price = "N/A"
        claimed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        all_texts = await page.locator("*").all_text_contents()
        
        page_content = await page.content()
        
        try:
            offer_section = page.locator(".job-offer, .offer-card, [class*='offer'], [class*='job']").first
            
            try:
                weighted_elem = offer_section.locator("text=/Weighted Words/i, text=/weighted/i").first
                if await weighted_elem.is_visible():
                    weighted_text = await weighted_elem.text_content()
                    if weighted_text:
                        import re
                        numbers = re.findall(r'[\d,]+\.?\d*', weighted_text)
                        if numbers:
                            weighted_words = numbers[0].replace(',', '')
            except Exception:
                pass
            
            try:
                price_elem = offer_section.locator("text=/Price|Earn|Payment|\\$/i").first
                if await price_elem.is_visible():
                    price_text = await price_elem.text_content()
                    import re
                    if price_text:
                        prices = re.findall(r'\$?[\d,]+\.?\d*', price_text)
                        if prices:
                            price = prices[0].replace('$', '').replace(',', '')
            except Exception:
                pass
                
        except Exception:
            pass
        
        if weighted_words == "N/A" or price == "N/A":
            try:
                weighted_locator = page.locator("text=/\\d+\\.?\\d*\\s*weighted/i, text=/weighted\\s*words:\\s*([\\d,]+)/i").first
                if await weighted_locator.is_visible():
                    text = await weighted_locator.text_content()
                    import re
                    if text:
                        numbers = re.findall(r'[\d,]+\.?\d*', text)
                        if numbers:
                            weighted_words = numbers[0].replace(',', '')
            except Exception:
                pass
            
            try:
                price_locator = page.locator("text=/\\$\\s*([\\d,]+\\.?\\d*)/i").first
                if await price_locator.is_visible():
                    text = await price_locator.text_content()
                    import re
                    if text:
                        prices = re.findall(r'\$?[\d,]+\.?\d*', text)
                        if prices:
                            price = prices[0].replace('$', '').replace(',', '')
            except Exception:
                pass
        
        return {
            "weighted_words": weighted_words,
            "price_usd": price,
            "claimed_at": claimed_at
        }
        
    except Exception as e:
        logger.warning(f" Error extracting job details: {e}")
        return {
            "weighted_words": "N/A",
            "price_usd": "N/A",
            "claimed_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }


async def check_and_claim(page: Page) -> bool:
    try:
        claim_button = page.locator(config.CLAIM_BUTTON_SELECTOR).first
        await claim_button.wait_for(state="visible", timeout=2000)

        if not await claim_button.is_enabled():
            logger.debug(" Claim button visible but disabled")
            return False

        logger.info(" Claim button detected!")
        
        logger.info(" Extracting job details before claiming...")
        job_details = await extract_job_details_before_claim(page)
        
        await notify_job_seen()
        await claim_button.click()
        logger.info(" Claim button clicked. Verifying success...")

        try:
            await claim_button.wait_for(state="hidden", timeout=config.WAIT_AFTER_CLAIM * 1000)
            logger.info(" Claim button disappeared, success confirmed!")
        except PlaywrightTimeout:
            if not await claim_button.is_enabled():
                logger.info(" Claim button disabled, success confirmed!")
            else:
                logger.error(" Claim click occurred, but button is still enabled. Success not confirmed.")
                await page.screenshot(path=f"{config.LOG_DIR}/claim_not_confirmed.png")
                return False

        await notify_job_claimed_with_details(job_details)
        return True

    except PlaywrightTimeout:
        logger.debug(f"No claim button found using selector: {config.CLAIM_BUTTON_SELECTOR}")
        return False

    except Exception as e:
        logger.exception(f" Claim attempt failed: {e}")
        await notify_error(f"Claim attempt failed: {e}")
        return False


async def notify_job_claimed_with_details(job_details: dict) -> None:
    try:
        price= job_details.get("price_usd", "0")
        weighted_words = job_details.get("weighted_words", "0")
        claimed_at = job_details.get("claimed_at", "Unknown")
        
        try:
            price_float = float(price.replace(',', ''))
            price_str = f"€{price_float:.2f}"
        except:
            price_str = f"€{price}" 
        
        message = (
            " <b>Job Claimed Successfully!</b>\n\n"
            f" <b>Date:</b> {claimed_at}\n"
            f" <b>Weighted Words:</b> {weighted_words}\n"
            f" <b>Price:</b> {price_str}\n"
        )
        
        await send_telegram_message(message, use_html=True)
        
    except Exception as e:
        logger.error(f" Error sending job claimed notification: {e}")
        await send_telegram_message(" Job claimed!", use_html=True)


async def claim_loop(page: Page):
    logger.info(" Starting claim loop...")

    try:
        await page.goto(
            config.TARGET_URL,
            timeout=60000,
            wait_until="domcontentloaded",
        )
    except Exception as e:
        logger.error(f" Failed to navigate to target page: {e}")
        await page.screenshot(path=f"{config.LOG_DIR}/target_nav_failed.png")
        return False

    if "login" in page.url.lower() or "signin" in page.url.lower():
        logger.error(f" Target page redirected to login: {page.url}")
        await page.screenshot(path=f"{config.LOG_DIR}/target_redirected_to_login.png")
        return False

    await page.wait_for_timeout(5000)
    
    page_content = await page.content()
    
    if len(page_content) < 3000 or ("Job offers" not in page_content and "no job offers" not in page_content.lower()):
        logger.warning(" Page content not fully loaded (blank or incomplete). Performing hard reload...")
        await page.screenshot(path=f"{config.LOG_DIR}/blank_page_before_reload.png")
        
        try:
            await page.reload(wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            logger.info(" Hard reload complete. Checking content again...")
        except Exception as e:
            logger.error(f" Hard reload failed: {e}")
            return False
    
    logger.info(f" Current URL: {page.url}")
    logger.info(f" Page title: {await page.title()}")

    check_count = 0

    while True:
        try:
            if not page or page.is_closed():
                logger.warning(" Page is closed! Re-initializing browser...")
                return False

            try:
                current_url = page.url
                if "login" in current_url.lower() or "signin" in current_url.lower():
                    logger.error(" Got redirected to login page! Session expired.")
                    return False
            except Exception:
                logger.warning(" Could not check page URL")
                return False

            check_count += 1
            
            if check_count % 60 == 0:
                logger.info(" Periodic hard reload to refresh data...")
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    logger.warning(f" Periodic reload failed: {e}")

            claimed = await check_and_claim(page)

            if claimed:
                logger.info(f" Waiting {config.CHECK_INTERVAL}s before next check...")
                await asyncio.sleep(config.CHECK_INTERVAL)
                check_count = 0
            else:
                await asyncio.sleep(config.CHECK_INTERVAL)

        except Exception as e:
            if "closed" in str(e).lower():
                logger.warning(" Browser closed unexpectedly. Restarting...")
                return False

            if "Timeout" not in str(e):
                logger.error(f" Loop error: {e}")
                await notify_error(str(e))
            
            await asyncio.sleep(10)