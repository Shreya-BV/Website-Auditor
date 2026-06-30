import httpx
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
import re

from app.scanners.logging_engine import setup_logger
from app.scanners.rendering import RenderingEngine
from app.scanners.detection import DetectionEngine
from app.scanners.scoring import ScoringEngine
from app.scanners.recommendations import RecommendationEngine

logger = setup_logger(__name__)

class HybridScanner:
    def __init__(self, url: str):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.url = url
        self.renderer = RenderingEngine(url)

    async def check_url_status(self, path: str) -> bool:
        target = f"{self.renderer.base_url.scheme}://{self.renderer.base_url.netloc}/{path.lstrip('/')}"
        client_options = {"timeout": 5.0, "follow_redirects": True, "verify": False, "headers": self.renderer.req_headers}
        try:
            async with httpx.AsyncClient(**client_options) as client:
                resp = await client.head(target)
                if resp.status_code in [200, 301, 302, 307, 308]:
                    return True
                resp = await client.get(target)
                return resp.status_code in [200, 301, 302, 307, 308]
        except Exception:
            return False

    async def run(self) -> Dict[str, Any]:
        await self.renderer.fetch()
        
        soup = BeautifulSoup(self.renderer.html, "html.parser")
        detector = DetectionEngine(self.renderer.html, soup, self.renderer.rendered_by_pw, self.renderer.pw_js_vars)
        
        # Async tasks for auxiliary files
        sitemap_task = self.check_url_status("sitemap.xml")
        robots_task = self.check_url_status("robots.txt")
        llms_task = self.check_url_status("llms.txt")
        sitemap_exists, robots_exists, llms_exists = await asyncio.gather(sitemap_task, robots_task, llms_task)

        # ---------------- MEASUREMENT ----------------
        meas_checks = {
            "google_analytics": detector.check_multiple("GA", ["google-analytics.com/analytics.js", "googletagmanager.com/gtag/js", "ga.js", "gtag("], [r"G-[A-Z0-9]+", r"UA-[0-9]+-[0-9]+"]),
            "gtm": detector.check_multiple("GTM", ["googletagmanager.com/gtm.js", "dataLayer.push"], [r"GTM-[A-Z0-9]+"]),
            "clarity": detector.check_multiple("Clarity", ["clarity.ms/tag/"]),
            "hotjar": detector.check_multiple("Hotjar", ["static.hotjar.com", "hjid"])
        }
        m_weights = {"google_analytics": 8, "gtm": 8, "clarity": 2, "hotjar": 2}
        _, m_score, m_exp = ScoringEngine.calculate_pillar("measurement", meas_checks, m_weights)

        # ---------------- RETARGETING ----------------
        retarg_checks = {
            "meta_pixel": detector.check_multiple("Meta", ["connect.facebook.net/en_us/fbevents.js", "fbq("]),
            "google_ads": detector.check_multiple("Google Ads", ["googleads", "aw-", "gtag('config', 'aw-"], [r"AW-[0-9]+"]),
            "linkedin_insight": detector.check_multiple("LinkedIn", ["snap.licdn.com/li.lms-analytics", "linkedin.com/profile.js"]),
            "tiktok_pixel": detector.check_multiple("TikTok", ["analytics.tiktok.com", "ttq.load("]),
            "pinterest_pixel": detector.check_multiple("Pinterest", ["ct.pinterest.com", "pintrk("])
        }
        r_weights = {"meta_pixel": 8, "google_ads": 6, "linkedin_insight": 3, "tiktok_pixel": 2, "pinterest_pixel": 1}
        _, r_score, r_exp = ScoringEngine.calculate_pillar("retargeting", retarg_checks, r_weights)

        # ---------------- CONVERSION ----------------
        c_form = bool(soup.find("form"))
        c_news = bool(soup.find("form", action=re.compile(r"(mailchimp|newsletter|subscribe|aweber)", re.I))) or detector.check_multiple("Newsletter", ["mc-embedded", "mailerlite"])["found"]
        c_wa = detector.check_multiple("WhatsApp", ["wa.me", "api.whatsapp.com", "whatsapp://"])["found"]
        
        if bool(soup.find("a", href=re.compile(r"^(tel|mailto):", re.I))):
            c_wa = True 
            
        conv_checks = {
            "contact_form": {"found": c_form, "confidence": 90 if c_form else 0, "method": "<form> tag", "evidence": "Form detected in HTML" if c_form else None},
            "newsletter_form": {"found": c_news, "confidence": 80 if c_news else 0, "method": "Newsletter form signature", "evidence": "Newsletter action or embedded form detected" if c_news else None},
            "whatsapp": {"found": c_wa, "confidence": 90 if c_wa else 0, "method": "WhatsApp/Phone/Email Link", "evidence": "Communication links detected" if c_wa else None},
            "messenger": detector.check_multiple("Messenger", ["connect.facebook.net/en_US/sdk/xfbml.customerchat.js", "fb-customerchat"]),
            "live_chat": detector.check_multiple("Live Chat", ["tawk.to", "intercom", "zendesk", "crisp", "drift"]),
            "calendly": detector.check_multiple("Calendly", ["calendly.com/assets", "calendly.com/widget"]),
            "crm": detector.check_multiple("CRM", ["hubspot", "zoho", "salesforce", "freshworks"])
        }
        c_weights = {"contact_form": 5, "whatsapp": 4, "newsletter_form": 3, "live_chat": 3, "messenger": 2, "crm": 2, "calendly": 1}
        _, c_score, c_exp = ScoringEngine.calculate_pillar("conversion", conv_checks, c_weights)

        # ---------------- TRUST ----------------
        nav_links = [a.get('href', '').lower() for a in soup.find_all('a') if a.get('href')]
        t_privacy = any("privacy" in link for link in nav_links)
        t_terms = any("terms" in link or "conditions" in link for link in nav_links)
        t_contact = any("contact" in link for link in nav_links)
        t_aria = bool(soup.find(attrs={"aria-label": True})) or bool(soup.find(attrs={"role": True}))

        s_sec = "strict-transport-security" in self.renderer.headers or "x-frame-options" in self.renderer.headers or "content-security-policy" in self.renderer.headers
        
        set_cookie_headers = [v for k, v in self.renderer.headers.items() if k.lower() == 'set-cookie']
        has_insecure_cookies = any("secure" not in h.lower() for h in set_cookie_headers) if set_cookie_headers else False
        has_secure_cookies = len(set_cookie_headers) == 0 or not has_insecure_cookies

        trust_checks = {
            "https": {"found": self.renderer.url.startswith("https://"), "confidence": 100, "method": "URL Scheme", "evidence": self.renderer.url},
            "ssl": {"found": self.renderer.ssl_valid, "confidence": 100, "method": "Certificate Validation", "evidence": "Valid SSL verified by httpx" if self.renderer.ssl_valid else None},
            "cookies": detector.check_multiple("Cookie Banner", ["cookie-consent", "cookiebot", "onetrust", "osano", "termly"]),
            "privacy_policy": {"found": t_privacy, "confidence": 90 if t_privacy else 0, "method": "Navigation Link", "evidence": "Found privacy policy link"},
            "terms": {"found": t_terms, "confidence": 90 if t_terms else 0, "method": "Navigation Link", "evidence": "Found terms link"},
            "contact_page": {"found": t_contact, "confidence": 90 if t_contact else 0, "method": "Navigation Link", "evidence": "Found contact link"},
            "accessibility": {"found": t_aria, "confidence": 80 if t_aria else 0, "method": "DOM ARIA Attributes", "evidence": "Found aria-label or role attributes"}
        }
        
        t_weights = {"https": 4, "ssl": 4, "privacy_policy": 3, "terms": 2, "contact_page": 2, "cookies": 3, "accessibility": 2}
        _, t_score, t_exp = ScoringEngine.calculate_pillar("trust", trust_checks, t_weights)
        
        if s_sec: t_exp += " | Security Headers: OK"
        if has_secure_cookies: t_exp += " | Secure Cookies: OK"

        # ---------------- SEO & AI ----------------
        s_title = soup.title is not None and len(soup.title.text.strip()) > 0
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        s_desc = desc_tag is not None and len(desc_tag.get("content", "").strip()) > 0
        s_canon = soup.find("link", rel="canonical") is not None
        s_schema = bool(soup.find("script", type="application/ld+json")) or detector.check_multiple("Schema", ["schema.org"])["found"]
        s_og = soup.find("meta", property=re.compile(r"^og:", re.I)) is not None
        s_tw = soup.find("meta", attrs={"name": re.compile(r"^twitter:", re.I)}) is not None
        
        seo_checks = {
            "canonical_url": {"found": s_canon, "confidence": 95 if s_canon else 0, "method": "Link canonical tag", "evidence": None},
            "meta_title": {"found": s_title, "confidence": 99 if s_title else 0, "method": "<title> tag", "evidence": None},
            "meta_description": {"found": s_desc, "confidence": 99 if s_desc else 0, "method": "<meta name='description'>", "evidence": None},
            "sitemap": {"found": sitemap_exists, "confidence": 100 if sitemap_exists else 0, "method": "HTTP GET", "evidence": "/sitemap.xml resolved" if sitemap_exists else None},
            "robots": {"found": robots_exists, "confidence": 100 if robots_exists else 0, "method": "HTTP GET", "evidence": "/robots.txt resolved" if robots_exists else None},
            "schema_markup": {"found": s_schema, "confidence": 90 if s_schema else 0, "method": "JSON-LD Script", "evidence": "application/ld+json found" if s_schema else None},
            "opengraph": {"found": s_og, "confidence": 99 if s_og else 0, "method": "og: meta tags", "evidence": "og: tags present"},
            "twitter_card": {"found": s_tw, "confidence": 99 if s_tw else 0, "method": "twitter: meta tags", "evidence": "twitter: tags present"},
            "llms_txt": {"found": llms_exists, "confidence": 100 if llms_exists else 0, "method": "HTTP GET", "evidence": "/llms.txt resolved" if llms_exists else None},
            "security_headers": {"found": s_sec, "confidence": 100 if s_sec else 0, "method": "HTTP Headers", "evidence": "Security headers present in HTTP response"}
        }
        s_weights = {"meta_title": 3, "meta_description": 3, "sitemap": 3, "robots": 2, "schema_markup": 3, "canonical_url": 2, "opengraph": 2, "twitter_card": 1, "llms_txt": 1, "security_headers": 0} 
        _, s_score, s_exp = ScoringEngine.calculate_pillar("seo_ai", seo_checks, s_weights)

        # ---------------- COMPILE ----------------
        overall_score = int(round(m_score + r_score + c_score + t_score + s_score))
        overall_score = min(100, max(0, overall_score))
        grade = ScoringEngine.get_grade(overall_score)
        
        all_checks = {
            "measurement": meas_checks,
            "retargeting": retarg_checks,
            "conversion": conv_checks,
            "trust": trust_checks,
            "seo_ai": seo_checks
        }
        
        recommendations = RecommendationEngine.generate(all_checks)

        return {
            "url": self.renderer.url,
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
            "checks": all_checks,
            "recommendations": recommendations,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "debug": {
                "rendering_mode": "Playwright" if self.renderer.rendered_by_pw else "HTTPX",
                "response_time": self.renderer.response_time
            }
        }

async def run_scan(url: str) -> Dict[str, Any]:
    scanner = HybridScanner(url)
    return await scanner.run()
