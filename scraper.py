import asyncio
from playwright.async_api import async_playwright
from playwright_stealth.stealth import stealth_async
import random

# Stealth-enabled function to scrape multiple URLs concurrently
async def scrape(urls):
    """Scrape multiple URLs concurrently while bypassing Cloudflare."""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            # executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            headless=True  # Set to True for full stealth mode
        )
        
        async def fetch_url(url):
            """Fetch a single URL and return extracted data."""
            page = await browser.new_page()

            # Apply stealth mode - using the correct function
            await stealth_async(page)

            # Randomized user agent & headers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            ]
            await page.set_extra_http_headers({
                "User-Agent": random.choice(user_agents),
                "Accept-Language": "en-US,en;q=0.9",
            })

            try:
                await page.goto(url, wait_until="domcontentloaded")  # Changed from networkidle
                await asyncio.sleep(random.uniform(2, 4))  # Random delay to avoid detection

                # Extract details
                title = await page.title()
                description = await page.evaluate('''() => {
                    let meta = document.querySelector("meta[name='description']");
                    return meta ? meta.content : "No description available";
                }''')
                text = await page.evaluate("document.body.innerText")

                results.append({
                    "url": url,
                    "title": title,
                    "description": description,
                    "text": text
                })
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            finally:
                await page.close()

        # Run all URL fetches concurrently
        await asyncio.gather(*(fetch_url(url) for url in urls))

        await browser.close()

    return results
