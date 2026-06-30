import httpx
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import asyncio
import re
from playwright.async_api import async_playwright

RECOMMENDATION_TEMPLATES = {
    "measurement": {
        "google_analytics": {
            "issue": "Google Analytics is missing",
            "reason": "Unable to track visitor behavior, traffic sources, and website engagement.",
            "business_impact": "Loss of critical data needed for marketing optimization and ROI tracking.",
            "how_to_fix": "Create a GA4 property and install the tracking script in the <head> of your website.",
            "estimated_time": "15 minutes",
            "priority": "High",
            "expected_score_increase": 5,
            "recommendation": "Install Google Analytics to track visitor behavior and understand traffic sources."
        },
        "gtm": {
            "issue": "Google Tag Manager is missing",
            "reason": "Marketing tags are likely hardcoded or missing, making it difficult to deploy tracking pixels.",
            "business_impact": "Slower marketing execution and reliance on developers for simple tracking changes.",
            "how_to_fix": "Create a GTM container and add the GTM scripts immediately after the <head> and <body> tags.",
            "estimated_time": "15 minutes",
            "priority": "Medium",
            "expected_score_increase": 5,
            "recommendation": "Use GTM to manage and deploy marketing tags without modifying code."
        },
        "clarity": {
            "issue": "Microsoft Clarity is missing",
            "reason": "No behavioral analytics or session recording tool detected.",
            "business_impact": "Inability to see exactly how users interact with the site, causing missed UX improvements.",
            "how_to_fix": "Sign up for Microsoft Clarity and install the tracking snippet.",
            "estimated_time": "10 minutes",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Install Microsoft Clarity to see visitor session recordings and heatmaps."
        },
        "hotjar": {
            "issue": "Hotjar is missing",
            "reason": "Missing user feedback and heatmap tracking.",
            "business_impact": "Blind spots in understanding why users might be abandoning the site.",
            "how_to_fix": "Install Hotjar via GTM or directly in the website code.",
            "estimated_time": "10 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Consider adding Hotjar to collect feedback and run user surveys on your website."
        }
    },
    "retargeting": {
        "meta_pixel": {
            "issue": "Meta Pixel is missing",
            "reason": "Unable to track Facebook/Instagram ad conversions or build retargeting audiences.",
            "business_impact": "Wasted ad spend and inability to reach people who previously visited your site.",
            "how_to_fix": "Generate a Meta Pixel in Facebook Events Manager and install it.",
            "estimated_time": "20 minutes",
            "priority": "High",
            "expected_score_increase": 4,
            "recommendation": "Install Meta Pixel to retarget website visitors through Facebook and Instagram advertising campaigns."
        },
        "google_ads": {
            "issue": "Google Ads Retargeting is missing",
            "reason": "Google Ads conversion and remarketing tags are absent.",
            "business_impact": "Inability to run effective Google Display or Search remarketing campaigns.",
            "how_to_fix": "Install the Google Ads tag via GTM.",
            "estimated_time": "15 minutes",
            "priority": "High",
            "expected_score_increase": 4,
            "recommendation": "Set up Google Ads tags to reach previous visitors when they search on Google or browse other sites."
        },
        "linkedin_insight": {
            "issue": "LinkedIn Insight Tag is missing",
            "reason": "Cannot track B2B professional demographics or conversions from LinkedIn ads.",
            "business_impact": "Missed opportunity for high-value B2B lead generation and retargeting.",
            "how_to_fix": "Add the LinkedIn Insight Tag to your website footer or via GTM.",
            "estimated_time": "10 minutes",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Add the Insight Tag to measure B2B conversions and retarget audiences."
        },
        "tiktok_pixel": {
            "issue": "TikTok Pixel is missing",
            "reason": "Cannot track TikTok ad conversions.",
            "business_impact": "Missed opportunity for Gen Z/Millennial retargeting.",
            "how_to_fix": "Add TikTok pixel via GTM.",
            "estimated_time": "10 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Add TikTok pixel to measure conversions from TikTok."
        },
        "pinterest_pixel": {
            "issue": "Pinterest Pixel is missing",
            "reason": "Cannot track Pinterest ad conversions.",
            "business_impact": "Missed visual commerce retargeting.",
            "how_to_fix": "Add Pinterest pixel via GTM.",
            "estimated_time": "10 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Add Pinterest pixel for retargeting."
        }
    },
    "conversion": {
        "contact_form": {
            "issue": "Contact Form not found",
            "reason": "No standard <form> elements detected for user inquiries.",
            "business_impact": "Lower conversion rates as users have no easy way to contact the business.",
            "how_to_fix": "Add a functional contact form on a dedicated contact page.",
            "estimated_time": "1-2 hours",
            "priority": "High",
            "expected_score_increase": 5,
            "recommendation": "Add a clear contact form to capture visitor inquiries directly."
        },
        "newsletter_form": {
            "issue": "Newsletter form missing",
            "reason": "No newsletter subscription elements found.",
            "business_impact": "Failing to build an email list.",
            "how_to_fix": "Add an email capture form.",
            "estimated_time": "30 mins",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Add a newsletter form."
        },
        "whatsapp": {
            "issue": "WhatsApp integration missing",
            "reason": "No wa.me or WhatsApp API links found.",
            "business_impact": "Losing mobile users who prefer instant messaging over emails.",
            "how_to_fix": "Add a WhatsApp floating button linking to your business number.",
            "estimated_time": "15 minutes",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Enable WhatsApp chat to let visitors connect with you instantly."
        },
        "messenger": {
            "issue": "Facebook Messenger missing",
            "reason": "No FB Messenger plugin found.",
            "business_impact": "Missing conversational conversions via social.",
            "how_to_fix": "Add Messenger chat plugin.",
            "estimated_time": "15 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Enable Facebook Messenger chat on your site."
        },
        "live_chat": {
            "issue": "Live Chat Widget missing",
            "reason": "No customer support chat scripts detected.",
            "business_impact": "Delayed response to customer objections, leading to lost sales.",
            "how_to_fix": "Integrate tools like Tawk.to, Intercom, or Zendesk.",
            "estimated_time": "30 minutes",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Install a chat tool to engage visitors in real-time."
        },
        "calendly": {
            "issue": "Calendly integration missing",
            "reason": "No scheduling tool detected.",
            "business_impact": "Friction in booking sales calls.",
            "how_to_fix": "Embed a Calendly widget.",
            "estimated_time": "15 mins",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Integrate Calendly for easy booking."
        },
        "crm": {
            "issue": "CRM integration missing",
            "reason": "No HubSpot, Salesforce, or Zoho tracking scripts found.",
            "business_impact": "Manual lead entry, causing delays and potential loss of valuable prospects.",
            "how_to_fix": "Install your CRM's tracking pixel on the website.",
            "estimated_time": "20 minutes",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Connect your site to a CRM to automate lead tracking."
        }
    },
    "trust": {
        "https": {
            "issue": "Website is not enforcing HTTPS",
            "reason": "The connection is not secure, exposing user data.",
            "business_impact": "Browser warnings will scare away users, and Google will penalize SEO.",
            "how_to_fix": "Configure your server to redirect all HTTP traffic to HTTPS.",
            "estimated_time": "30 minutes",
            "priority": "High",
            "expected_score_increase": 5,
            "recommendation": "Upgrade to secure HTTPS to protect user data and improve search rankings."
        },
        "ssl": {
            "issue": "SSL Certificate is invalid or missing",
            "reason": "The site does not have a valid, trusted SSL certificate.",
            "business_impact": "Users will see a 'Your connection is not private' error, destroying trust.",
            "how_to_fix": "Obtain a free certificate from Let's Encrypt or your hosting provider.",
            "estimated_time": "1 hour",
            "priority": "High",
            "expected_score_increase": 3,
            "recommendation": "Ensure you have a valid, trusted SSL certificate to prevent browser warning screens."
        },
        "cookies": {
            "issue": "Cookie Consent missing",
            "reason": "No cookie banner detected.",
            "business_impact": "Risk of GDPR/CCPA fines.",
            "how_to_fix": "Implement a cookie banner like OneTrust.",
            "estimated_time": "30 mins",
            "priority": "High",
            "expected_score_increase": 3,
            "recommendation": "Add a cookie consent banner for legal compliance."
        },
        "privacy_policy": {
            "issue": "Privacy Policy missing",
            "reason": "No link to a privacy policy found in the page.",
            "business_impact": "Non-compliance with GDPR/CCPA, risk of fines, and advertising accounts getting banned.",
            "how_to_fix": "Generate a Privacy Policy and link it in the footer.",
            "estimated_time": "1 hour",
            "priority": "High",
            "expected_score_increase": 3,
            "recommendation": "Create a Privacy Policy page to satisfy legal requirements and build trust."
        },
        "terms": {
            "issue": "Terms & Conditions missing",
            "reason": "No link to Terms & Conditions found.",
            "business_impact": "Legal vulnerability regarding user disputes and liability.",
            "how_to_fix": "Generate a Terms & Conditions page and link it in the footer.",
            "estimated_time": "1 hour",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Publish Terms & Conditions to protect your business liability."
        },
        "contact_page": {
            "issue": "Contact page link missing",
            "reason": "Could not find a dedicated link to a contact page.",
            "business_impact": "Reduces brand legitimacy and frustrates users trying to reach you.",
            "how_to_fix": "Create a Contact Us page and add it to the main navigation or footer.",
            "estimated_time": "30 minutes",
            "priority": "High",
            "expected_score_increase": 3,
            "recommendation": "Create a dedicated contact page with clear business details."
        },
        "accessibility": {
            "issue": "Basic Accessibility missing",
            "reason": "No ARIA attributes or basic accessibility tags found.",
            "business_impact": "Potential ADA lawsuits and poor experience for disabled users.",
            "how_to_fix": "Add ARIA roles to interactive elements.",
            "estimated_time": "2 hours",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Improve basic web accessibility."
        }
    },
    "seo_ai": {
        "canonical_url": {
            "issue": "Canonical URL missing",
            "reason": "No <link rel='canonical'> found.",
            "business_impact": "Duplicate content penalties.",
            "how_to_fix": "Add canonical link tags.",
            "estimated_time": "15 mins",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Define a canonical URL to avoid duplicate content SEO issues."
        },
        "meta_title": {
            "issue": "Meta Title missing or empty",
            "reason": "The <title> tag is not properly defined.",
            "business_impact": "Poor visibility in search engine results and unappealing browser tabs.",
            "how_to_fix": "Add a descriptive, keyword-optimized <title> tag to the <head>.",
            "estimated_time": "15 minutes",
            "priority": "High",
            "expected_score_increase": 2,
            "recommendation": "Write a unique, keyword-rich title tag to rank higher in search engines."
        },
        "meta_description": {
            "issue": "Meta Description missing",
            "reason": "The <meta name='description'> tag is absent.",
            "business_impact": "Lower click-through rates from Google search results.",
            "how_to_fix": "Add a compelling meta description tag.",
            "estimated_time": "15 minutes",
            "priority": "High",
            "expected_score_increase": 2,
            "recommendation": "Write a compelling meta description to improve click-through rates from search results."
        },
        "sitemap": {
            "issue": "Sitemap.xml not found",
            "reason": "No sitemap detected at the standard /sitemap.xml path.",
            "business_impact": "Search engines may take longer to index new pages.",
            "how_to_fix": "Generate an XML sitemap and submit it to Google Search Console.",
            "estimated_time": "30 minutes",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Create a sitemap to help search engines find and index all your website pages."
        },
        "robots": {
            "issue": "Robots.txt not found",
            "reason": "Missing robots.txt file at the root directory.",
            "business_impact": "Inability to control how search engines crawl the site.",
            "how_to_fix": "Create a robots.txt file allowing required crawlers.",
            "estimated_time": "15 minutes",
            "priority": "Medium",
            "expected_score_increase": 2,
            "recommendation": "Add a robots.txt file to instruct search crawlers which pages they should or should not index."
        },
        "schema_markup": {
            "issue": "Schema Markup missing",
            "reason": "No JSON-LD structured data found on the page.",
            "business_impact": "Missing out on Google Rich Snippets (stars, FAQs, organization info).",
            "how_to_fix": "Implement Organization or LocalBusiness schema via JSON-LD.",
            "estimated_time": "1 hour",
            "priority": "Medium",
            "expected_score_increase": 3,
            "recommendation": "Add structured data schema to help Google and AI assistants understand your business content."
        },
        "opengraph": {
            "issue": "OpenGraph tags missing",
            "reason": "No og:title or og:image tags detected.",
            "business_impact": "Links shared on social media will look unappealing without preview images.",
            "how_to_fix": "Add OpenGraph meta tags to the <head>.",
            "estimated_time": "20 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Add OpenGraph metadata to control how your pages look when shared on Facebook and LinkedIn."
        },
        "twitter_card": {
            "issue": "Twitter Card missing",
            "reason": "No twitter:card tags detected.",
            "business_impact": "Poor link previews when shared on X/Twitter.",
            "how_to_fix": "Add Twitter Card meta tags to the <head>.",
            "estimated_time": "10 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Set up Twitter Card tags to ensure rich previews on X (formerly Twitter)."
        },
        "llms_txt": {
            "issue": "llms.txt missing",
            "reason": "No llms.txt found to guide AI assistants.",
            "business_impact": "AI tools like ChatGPT may hallucinate or fail to understand the business offerings properly.",
            "how_to_fix": "Create an llms.txt at the root of the site with essential business facts.",
            "estimated_time": "15 minutes",
            "priority": "Low",
            "expected_score_increase": 2,
            "recommendation": "Add an llms.txt file at the root of your domain to guide AI crawlers."
        },
        "security_headers": {
            "issue": "Security headers missing",
            "reason": "Missing HSTS, X-Frame-Options, or CSP headers.",
            "business_impact": "Vulnerable to basic web exploits.",
            "how_to_fix": "Add security headers to your server configuration.",
            "estimated_time": "1 hour",
            "priority": "High",
            "expected_score_increase": 3,
            "recommendation": "Implement modern security headers."
        }
    }
}

class AdvancedScanner:
    def __init__(self, url: str):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.url = url
        self.base_url = urllib.parse.urlparse(url)
        self.html = ""
        self.soup = None
        self.headers = {}
        self.cookies = {}
        self.scripts = []
        self.links = []
        self.meta = []
        self.rendered_by_pw = False
        self.pw_js_vars = {}
        self.response_time = 0.0
        
        self.ssl_valid = url.startswith("https://")
        
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.req_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            # We omit Accept-Encoding to let httpx handle gzip, deflate, br automatically
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def check_url_status(self, client: httpx.AsyncClient, path: str) -> bool:
        target = f"{self.base_url.scheme}://{self.base_url.netloc}/{path.lstrip('/')}"
        try:
            resp = await client.head(target, timeout=5.0, follow_redirects=True)
            if resp.status_code in [200, 301, 302, 307, 308]:
                return True
            resp = await client.get(target, timeout=5.0, follow_redirects=True)
            return resp.status_code in [200, 301, 302, 307, 308]
        except Exception:
            return False

    async def fetch_html_playwright(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self.user_agent)
                page = await context.new_page()
                
                # Navigate and wait for networkidle
                await page.goto(self.url, wait_until="networkidle", timeout=25000)
                
                # Scroll to trigger lazy-loaded elements
                await page.evaluate("""
                    window.scrollTo(0, document.body.scrollHeight / 2);
                    setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 500);
                """)
                await page.wait_for_timeout(1000)
                
                self.html = await page.content()
                
                # Check for JS variables typical of tracking tools
                js_vars = await page.evaluate("""() => {
                    return {
                        'ga': typeof window.ga !== 'undefined' || typeof window.gtag !== 'undefined',
                        'dataLayer': typeof window.dataLayer !== 'undefined' && window.dataLayer.length > 0,
                        'fbq': typeof window.fbq !== 'undefined' || typeof window._fbq !== 'undefined',
                        'ttq': typeof window.ttq !== 'undefined',
                        'pintrk': typeof window.pintrk !== 'undefined',
                        'hubspot': typeof window.HubSpotConversations !== 'undefined' || typeof window._hsq !== 'undefined',
                        'clarity': typeof window.clarity !== 'undefined',
                        'hj': typeof window.hj !== 'undefined'
                    };
                }""")
                self.pw_js_vars = js_vars
                await browser.close()
                self.rendered_by_pw = True
        except Exception as e:
            print(f"Playwright error: {e}")

    async def fetch_website(self):
        start_time = datetime.now()
        client_options = {
            "timeout": 20.0,
            "follow_redirects": True,
            "headers": self.req_headers
        }
        
        async with httpx.AsyncClient(**client_options) as client:
            try:
                response = await client.get(self.url)
                self.html = response.text
                self.headers = {k.lower(): v for k, v in response.headers.items()}
                self.cookies = response.cookies
                self.url = str(response.url)  # update to final redirect URL
                self.ssl_valid = self.url.startswith("https://")
            except httpx.TransportError as e:
                if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                    try:
                        client_options["verify"] = False
                        async with httpx.AsyncClient(**client_options) as client_unverified:
                            response = await client_unverified.get(self.url)
                            self.html = response.text
                            self.headers = {k.lower(): v for k, v in response.headers.items()}
                            self.cookies = response.cookies
                            self.url = str(response.url)
                            self.ssl_valid = False
                    except Exception as inner_e:
                        raise Exception(f"SSL handshake failed: {str(inner_e)}")
                else:
                    raise Exception(f"Network error: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to scan website: {str(e)}")

        self.response_time = (datetime.now() - start_time).total_seconds()
        self.soup = BeautifulSoup(self.html, "html.parser")
        
        # Check if SPA (Client-Side Rendered)
        body_text = self.soup.body.get_text(strip=True) if self.soup.body else ""
        is_spa = len(body_text) < 1000 or self.soup.find(id=re.compile("^(root|app|__next|vue-app)$", re.I))
        
        if is_spa:
            await self.fetch_html_playwright()
            self.soup = BeautifulSoup(self.html, "html.parser")

        # Parse essential elements for fast scanning
        self.scripts = self.soup.find_all("script")
        self.links = self.soup.find_all("link")
        self.meta = self.soup.find_all("meta")

    def _check_signatures(self, signatures: List[str], regex_patterns: List[str] = None) -> Tuple[bool, int, str, str]:
        """Returns (found, confidence, method, evidence)"""
        html_lower = self.html.lower()
        
        # 1. Check JS Variables (Highest Confidence)
        if self.rendered_by_pw:
            for sig in signatures:
                if self.pw_js_vars.get(sig.lower()):
                    return True, 100, "JS Variable Execution", f"window.{sig} is active"
        
        # 2. Check Script SRC (High Confidence)
        for script in self.scripts:
            src = script.get("src", "")
            if src:
                src_lower = src.lower()
                for sig in signatures:
                    if sig.lower() in src_lower:
                        return True, 95, "External Script", src
                if regex_patterns:
                    for pat in regex_patterns:
                        if re.search(pat, src, re.IGNORECASE):
                            return True, 95, "External Script Regex", src

        # 3. Check Inline Scripts (Medium-High Confidence)
        for script in self.scripts:
            content = script.string
            if content:
                content_lower = content.lower()
                for sig in signatures:
                    if sig.lower() in content_lower:
                        idx = content_lower.find(sig.lower())
                        start = max(0, idx - 20)
                        end = min(len(content_lower), idx + 40)
                        snippet = content[start:end].replace("\n", " ").strip()
                        return True, 90, "Inline Script", f"...{snippet}..."
                if regex_patterns:
                    for pat in regex_patterns:
                        match = re.search(pat, content, re.IGNORECASE)
                        if match:
                            snippet = match.group(0)[:40].replace("\n", " ")
                            return True, 90, "Inline Script Regex", f"Matched: {snippet}"

        # 4. Check DOM/Network links
        for link in self.links:
            href = link.get("href", "")
            if href:
                href_lower = href.lower()
                for sig in signatures:
                    if sig.lower() in href_lower:
                        return True, 85, "Link/Resource tag", href
                if regex_patterns:
                    for pat in regex_patterns:
                        if re.search(pat, href, re.IGNORECASE):
                            return True, 85, "Link Regex", href

        # 5. Last resort: raw HTML check
        for sig in signatures:
            if sig.lower() in html_lower:
                return True, 70, "Raw HTML Match", f"Found keyword '{sig}' in DOM"
        if regex_patterns:
            for pat in regex_patterns:
                if re.search(pat, self.html, re.IGNORECASE):
                    return True, 70, "Raw HTML Regex", "Pattern matched in raw HTML"

        return False, 0, "None", None

    def check_multiple(self, tool_name: str, signatures: List[str], regex_patterns: List[str] = None) -> dict:
        found, conf, method, evidence = self._check_signatures(signatures, regex_patterns)
        return {"found": found, "confidence": conf, "method": method, "evidence": evidence}

    def calculate_pillar(self, pillar_name: str, checks: dict, weights: dict) -> Tuple[float, float, str]:
        total_possible = sum(weights.values())
        achieved = 0.0
        explanations = []
        
        for key, w in weights.items():
            if checks.get(key, {}).get("found"):
                achieved += w
                explanations.append(f"{key.replace('_', ' ').title()}: +{w}")
            else:
                explanations.append(f"{key.replace('_', ' ').title()}: 0/{w}")
                
        # Scale to exactly 20 max
        if total_possible > 0:
            weighted = (achieved / total_possible) * 20.0
        else:
            weighted = 0.0
            
        weighted = min(20.0, max(0.0, weighted))
        explanation_str = " | ".join(explanations)
        return achieved, weighted, explanation_str

    async def run(self) -> Dict[str, Any]:
        await self.fetch_website()
        
        # Aux Files concurrently
        async with httpx.AsyncClient(headers=self.req_headers, verify=False) as client:
            sitemap_task = self.check_url_status(client, "sitemap.xml")
            robots_task = self.check_url_status(client, "robots.txt")
            llms_task = self.check_url_status(client, "llms.txt")
            sitemap_exists, robots_exists, llms_exists = await asyncio.gather(sitemap_task, robots_task, llms_task)

        # =====================================================================
        # PILLAR 1: MEASUREMENT
        # =====================================================================
        meas_checks = {
            "google_analytics": self.check_multiple("GA", ["google-analytics.com/analytics.js", "googletagmanager.com/gtag/js", "ga.js", "gtag("], [r"G-[A-Z0-9]+", r"UA-[0-9]+-[0-9]+"]),
            "gtm": self.check_multiple("GTM", ["googletagmanager.com/gtm.js", "dataLayer.push"], [r"GTM-[A-Z0-9]+"]),
            "clarity": self.check_multiple("Clarity", ["clarity.ms/tag/"]),
            "hotjar": self.check_multiple("Hotjar", ["static.hotjar.com", "hjid"])
        }
        m_weights = {"google_analytics": 8, "gtm": 8, "clarity": 2, "hotjar": 2}
        m_raw, m_score, m_exp = self.calculate_pillar("measurement", meas_checks, m_weights)

        # =====================================================================
        # PILLAR 2: RETARGETING
        # =====================================================================
        retarg_checks = {
            "meta_pixel": self.check_multiple("Meta", ["connect.facebook.net/en_us/fbevents.js", "fbq("]),
            "google_ads": self.check_multiple("Google Ads", ["googleads", "aw-", "gtag('config', 'aw-"], [r"AW-[0-9]+"]),
            "linkedin_insight": self.check_multiple("LinkedIn", ["snap.licdn.com/li.lms-analytics", "linkedin.com/profile.js"]),
            "tiktok_pixel": self.check_multiple("TikTok", ["analytics.tiktok.com", "ttq.load("]),
            "pinterest_pixel": self.check_multiple("Pinterest", ["ct.pinterest.com", "pintrk("])
        }
        r_weights = {"meta_pixel": 8, "google_ads": 6, "linkedin_insight": 3, "tiktok_pixel": 2, "pinterest_pixel": 1}
        r_raw, r_score, r_exp = self.calculate_pillar("retargeting", retarg_checks, r_weights)

        # =====================================================================
        # PILLAR 3: CONVERSION
        # =====================================================================
        c_form = bool(self.soup.find("form"))
        c_news = bool(self.soup.find("form", action=re.compile(r"(mailchimp|newsletter|subscribe|aweber)", re.I))) or self.check_multiple("Newsletter", ["mc-embedded", "mailerlite"])["found"]
        c_wa = self.check_multiple("WhatsApp", ["wa.me", "api.whatsapp.com", "whatsapp://"])["found"]
        
        # Phone and Email links
        has_tel = bool(self.soup.find("a", href=re.compile(r"^tel:", re.I)))
        has_mailto = bool(self.soup.find("a", href=re.compile(r"^mailto:", re.I)))
        if has_tel or has_mailto:
            c_wa = True  # We merge this into whatsapp/phone/email
            
        conv_checks = {
            "contact_form": {"found": c_form, "confidence": 90 if c_form else 0, "method": "<form> tag", "evidence": "Form detected in HTML" if c_form else None},
            "newsletter_form": {"found": c_news, "confidence": 80 if c_news else 0, "method": "Newsletter form signature", "evidence": "Newsletter action or embedded form detected" if c_news else None},
            "whatsapp": {"found": c_wa, "confidence": 90 if c_wa else 0, "method": "WhatsApp/Phone/Email Link", "evidence": "Communication links detected" if c_wa else None},
            "messenger": self.check_multiple("Messenger", ["connect.facebook.net/en_US/sdk/xfbml.customerchat.js", "fb-customerchat"]),
            "live_chat": self.check_multiple("Live Chat", ["tawk.to", "intercom", "zendesk", "crisp", "drift"]),
            "calendly": self.check_multiple("Calendly", ["calendly.com/assets", "calendly.com/widget"]),
            "crm": self.check_multiple("CRM", ["hubspot", "zoho", "salesforce", "freshworks"])
        }
        c_weights = {"contact_form": 5, "whatsapp": 4, "newsletter_form": 3, "live_chat": 3, "messenger": 2, "crm": 2, "calendly": 1}
        c_raw, c_score, c_exp = self.calculate_pillar("conversion", conv_checks, c_weights)

        # =====================================================================
        # PILLAR 4: TRUST
        # =====================================================================
        nav_links = [a.get('href', '').lower() for a in self.soup.find_all('a') if a.get('href')]
        t_privacy = any("privacy" in link for link in nav_links)
        t_terms = any("terms" in link or "conditions" in link for link in nav_links)
        t_contact = any("contact" in link for link in nav_links)
        t_aria = bool(self.soup.find(attrs={"aria-label": True})) or bool(self.soup.find(attrs={"role": True}))

        # Headers check
        s_sec = "strict-transport-security" in self.headers or "x-frame-options" in self.headers or "content-security-policy" in self.headers
        
        # Cookies check (are any cookies secure?)
        has_insecure_cookies = any(not c.secure for c in self.cookies.values())
        has_secure_cookies = len(self.cookies) == 0 or not has_insecure_cookies

        trust_checks = {
            "https": {"found": self.url.startswith("https://"), "confidence": 100, "method": "URL Scheme", "evidence": self.url},
            "ssl": {"found": self.ssl_valid, "confidence": 100, "method": "Certificate Validation", "evidence": "Valid SSL verified by httpx" if self.ssl_valid else None},
            "cookies": self.check_multiple("Cookie Banner", ["cookie-consent", "cookiebot", "onetrust", "osano", "termly"]),
            "privacy_policy": {"found": t_privacy, "confidence": 90 if t_privacy else 0, "method": "Navigation Link", "evidence": "Found privacy policy link"},
            "terms": {"found": t_terms, "confidence": 90 if t_terms else 0, "method": "Navigation Link", "evidence": "Found terms link"},
            "contact_page": {"found": t_contact, "confidence": 90 if t_contact else 0, "method": "Navigation Link", "evidence": "Found contact link"},
            "accessibility": {"found": t_aria, "confidence": 80 if t_aria else 0, "method": "DOM ARIA Attributes", "evidence": "Found aria-label or role attributes"}
        }
        
        # We implicitly reward for secure cookies and headers in overall score
        t_weights = {"https": 4, "ssl": 4, "privacy_policy": 3, "terms": 2, "contact_page": 2, "cookies": 3, "accessibility": 2}
        t_raw, t_score, t_exp = self.calculate_pillar("trust", trust_checks, t_weights)
        
        if s_sec: t_exp += " | Security Headers: OK"
        if has_secure_cookies: t_exp += " | Secure Cookies: OK"

        # =====================================================================
        # PILLAR 5: SEO / AI
        # =====================================================================
        s_title = self.soup.title is not None and len(self.soup.title.text.strip()) > 0
        title_text = self.soup.title.text.strip() if s_title else None
        
        desc_tag = self.soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        s_desc = desc_tag is not None and len(desc_tag.get("content", "").strip()) > 0
        desc_text = desc_tag.get("content") if s_desc else None

        canon_tag = self.soup.find("link", rel="canonical")
        s_canon = canon_tag is not None

        s_schema = bool(self.soup.find("script", type="application/ld+json")) or self.check_multiple("Schema", ["schema.org"])["found"]
        s_og = self.soup.find("meta", property=re.compile(r"^og:", re.I)) is not None
        s_tw = self.soup.find("meta", attrs={"name": re.compile(r"^twitter:", re.I)}) is not None
        
        seo_checks = {
            "canonical_url": {"found": s_canon, "confidence": 95 if s_canon else 0, "method": "Link canonical tag", "evidence": canon_tag.get("href") if s_canon else None},
            "meta_title": {"found": s_title, "confidence": 99 if s_title else 0, "method": "<title> tag", "evidence": title_text},
            "meta_description": {"found": s_desc, "confidence": 99 if s_desc else 0, "method": "<meta name='description'>", "evidence": desc_text},
            "sitemap": {"found": sitemap_exists, "confidence": 100 if sitemap_exists else 0, "method": "HTTP GET", "evidence": "/sitemap.xml resolved" if sitemap_exists else None},
            "robots": {"found": robots_exists, "confidence": 100 if robots_exists else 0, "method": "HTTP GET", "evidence": "/robots.txt resolved" if robots_exists else None},
            "schema_markup": {"found": s_schema, "confidence": 90 if s_schema else 0, "method": "JSON-LD Script", "evidence": "application/ld+json found" if s_schema else None},
            "opengraph": {"found": s_og, "confidence": 99 if s_og else 0, "method": "og: meta tags", "evidence": "og: tags present"},
            "twitter_card": {"found": s_tw, "confidence": 99 if s_tw else 0, "method": "twitter: meta tags", "evidence": "twitter: tags present"},
            "llms_txt": {"found": llms_exists, "confidence": 100 if llms_exists else 0, "method": "HTTP GET", "evidence": "/llms.txt resolved" if llms_exists else None},
            "security_headers": {"found": s_sec, "confidence": 100 if s_sec else 0, "method": "HTTP Headers", "evidence": "Security headers present in HTTP response"}
        }
        s_weights = {"meta_title": 3, "meta_description": 3, "sitemap": 3, "robots": 2, "schema_markup": 3, "canonical_url": 2, "opengraph": 2, "twitter_card": 1, "llms_txt": 1, "security_headers": 0} # using sec_headers mostly for trust actually, keeping weight 0 here to total 20.
        s_raw, s_score, s_exp = self.calculate_pillar("seo_ai", seo_checks, s_weights)

        # =====================================================================
        # COMPILE RESULTS
        # =====================================================================
        overall_score = int(round(m_score + r_score + c_score + t_score + s_score))
        overall_score = min(100, max(0, overall_score))

        if overall_score >= 90:
            grade = "Excellent"
        elif overall_score >= 70:
            grade = "Good"
        elif overall_score >= 50:
            grade = "Average"
        else:
            grade = "Needs Improvement"

        recommendations = []
        for pillar, checks in [
            ("measurement", meas_checks),
            ("retargeting", retarg_checks),
            ("conversion", conv_checks),
            ("trust", trust_checks),
            ("seo_ai", seo_checks)
        ]:
            for key, result in checks.items():
                if not result.get("found") and key in RECOMMENDATION_TEMPLATES.get(pillar, {}):
                    tmpl = RECOMMENDATION_TEMPLATES[pillar][key]
                    recommendations.append({
                        "pillar": pillar,
                        "item": key,
                        "issue": tmpl["issue"],
                        "reason": tmpl.get("technical_explanation", tmpl.get("reason", "No reason provided.")),
                        "business_impact": tmpl["business_impact"],
                        "how_to_fix": tmpl["how_to_fix"],
                        "estimated_time": tmpl["estimated_time"],
                        "priority": tmpl["priority"],
                        "expected_score_increase": tmpl["expected_score_increase"],
                        "recommendation": tmpl["recommendation"]
                    })

        return {
            "url": self.url,
            "overall_score": overall_score,
            "grade": grade,
            "pillar_scores": {
                "measurement": m_score,
                "retargeting": r_score,
                "conversion": c_score,
                "trust": t_score,
                "seo_ai": s_score
            },
            "explanations": {
                "measurement": m_exp,
                "retargeting": r_exp,
                "conversion": c_exp,
                "trust": t_exp,
                "seo_ai": s_exp
            },
            "checks": {
                "measurement": meas_checks,
                "retargeting": retarg_checks,
                "conversion": conv_checks,
                "trust": trust_checks,
                "seo_ai": seo_checks
            },
            "recommendations": recommendations,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

async def run_scan(url: str) -> Dict[str, Any]:
    scanner = AdvancedScanner(url)
    return await scanner.run()
