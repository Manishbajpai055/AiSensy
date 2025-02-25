import asyncio
from playwright.async_api import async_playwright

async def scrape(urls):
    """Scrape multiple URLs and return structured data (title, description, text)."""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",headless=True)
        
        page = await browser.new_page()

        for url in urls:
            await page.goto(url, wait_until="networkidle") # Ensure all network request are complete
            await asyncio.sleep(2)  # Ensure all dynamic content is rendered (for React, Angular, etc.)

            try:
                # Wait for body to ensure full page load
                await page.wait_for_selector("body", timeout=1000)

                # Extract page details
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
                results.append({
                    "url": url,
                    "title": None,
                    "description": None,
                    "text": None
                })

        await browser.close()
    
    return results