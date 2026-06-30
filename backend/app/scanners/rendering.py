import httpx
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import asyncio
import logging
from playwright.async_api import async_playwright, Error as PlaywrightError

from app.scanners.logging_engine import setup_logger
from app.scanners.decision import DecisionEngine

logger = setup_logger(__name__)

class RenderingEngine:
    def __init__(self, url: str):
        self.original_url = url
        self.url = url
        self.base_url = urllib.parse.urlparse(url)
        self.html = ""
        self.headers = {}
        self.cookies = {}
        self.ssl_valid = url.startswith("https://")
        self.rendered_by_pw = False
        self.pw_js_vars = {}
        self.response_time = 0.0
        self.error = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.req_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def fetch_httpx(self):
        client_options = {
            "timeout": 20.0,
            "follow_redirects": True,
            "headers": self.req_headers
        }
        
        async with httpx.AsyncClient(**client_options) as client:
            try:
                response = await client.get(self.url)
                self._process_httpx_response(response)
            except httpx.TransportError as e:
                if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                    try:
                        client_options["verify"] = False
                        async with httpx.AsyncClient(**client_options) as client_unverified:
                            response = await client_unverified.get(self.url)
                            self._process_httpx_response(response, ssl_valid=False)
                    except Exception as inner_e:
                        raise Exception(f"SSL handshake failed: {str(inner_e)}")
                else:
                    raise Exception(f"Network error: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to scan website: {str(e)}")

    def _process_httpx_response(self, response: httpx.Response, ssl_valid: bool = True):
        self.html = response.text
        self.headers = {k.lower(): v for k, v in response.headers.items()}
        self.cookies = response.cookies
        self.url = str(response.url)
        self.base_url = urllib.parse.urlparse(self.url)
        self.ssl_valid = ssl_valid if self.url.startswith("https://") else False

    async def fetch_playwright(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
                context = await browser.new_context(user_agent=self.user_agent)
                # Block media/images to speed up rendering
                await context.route("**/*", lambda route: route.continue_() if route.request.resource_type not in ["image", "media", "font"] else route.abort())
                page = await context.new_page()
                
                try:
                    await page.goto(self.url, wait_until="domcontentloaded", timeout=25000)
                    
                    # Scroll to trigger lazy-loaded elements
                    await page.evaluate("""
                        window.scrollTo(0, document.body.scrollHeight / 2);
                        setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 500);
                    """)
                    
                    # Wait for network idle or timeout
                    try:
                        await page.wait_for_load_state("networkidle", timeout=5000)
                    except PlaywrightError:
                        pass # Ignore networkidle timeout, we still have DOM
                    
                    self.html = await page.content()
                    
                    # Check JS variables for tracking and analytics
                    js_vars = await page.evaluate("""() => {
                        return {
                            'ga': typeof window.ga !== 'undefined' || typeof window.gtag !== 'undefined',
                            'dataLayer': typeof window.dataLayer !== 'undefined' && window.dataLayer.length > 0,
                            'fbq': typeof window.fbq !== 'undefined' || typeof window._fbq !== 'undefined',
                            'ttq': typeof window.ttq !== 'undefined',
                            'pintrk': typeof window.pintrk !== 'undefined',
                            'hubspot': typeof window.HubSpotConversations !== 'undefined' || typeof window._hsq !== 'undefined',
                            'clarity': typeof window.clarity !== 'undefined',
                            'hj': typeof window.hj !== 'undefined',
                            'intercom': typeof window.Intercom !== 'undefined',
                            'zendesk': typeof window.zE !== 'undefined',
                            'tawk': typeof window.Tawk_API !== 'undefined'
                        };
                    }""")
                    self.pw_js_vars = js_vars
                    self.rendered_by_pw = True
                except Exception as e:
                    logger.warning(f"Playwright navigation/execution error: {str(e)}")
                    # Fallback to HTTPX html if PW totally failed and we had nothing
                    if not self.html:
                        raise e
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"Playwright critical error: {str(e)}")
            self.error = str(e)

    async def fetch(self):
        start_time = datetime.now()
        # 1. Always do fast HTTPX first
        await self.fetch_httpx()
        
        soup = BeautifulSoup(self.html, "html.parser")
        
        # 2. Decide if Playwright is needed
        requires_pw, reason = DecisionEngine.requires_playwright(self.html, soup)
        logger.info(f"Rendering Decision for {self.url}: Playwright Required={requires_pw}, Reason={reason}")
        
        # 3. Run Playwright if needed
        if requires_pw:
            pw_start = datetime.now()
            await self.fetch_playwright()
            pw_dur = (datetime.now() - pw_start).total_seconds()
            logger.info(f"Playwright rendering finished in {pw_dur:.2f}s")
            
        self.response_time = (datetime.now() - start_time).total_seconds()
