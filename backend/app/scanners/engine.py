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
            "expected_score_increase": 4,
            "recommendation": "Install Google Analytics to track visitor behavior and understand traffic sources."
        },
        "gtm": {
            "issue": "Google Tag Manager is missing",
            "reason": "Marketing tags are likely hardcoded or missing, making it difficult to deploy tracking pixels.",
            "business_impact": "Slower marketing execution and reliance on developers for simple tracking changes.",
            "how_to_fix": "Create a GTM container and add the GTM scripts immediately after the <head> and <body> tags.",
            "estimated_time": "15 minutes",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Use GTM to manage and deploy marketing tags without modifying code."
        },
        "clarity": {
            "issue": "Microsoft Clarity is missing",
            "reason": "No behavioral analytics or session recording tool detected.",
            "business_impact": "Inability to see exactly how users interact with the site, causing missed UX improvements.",
            "how_to_fix": "Sign up for Microsoft Clarity and install the tracking snippet.",
            "estimated_time": "10 minutes",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Install Microsoft Clarity to see visitor session recordings and heatmaps."
        },
        "hotjar": {
            "issue": "Hotjar is missing",
            "reason": "Missing user feedback and heatmap tracking.",
            "business_impact": "Blind spots in understanding why users might be abandoning the site.",
            "how_to_fix": "Install Hotjar via GTM or directly in the website code.",
            "estimated_time": "10 minutes",
            "priority": "Low",
            "expected_score_increase": 4,
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
            "expected_score_increase": 6,
            "recommendation": "Install Meta Pixel to retarget website visitors through Facebook and Instagram advertising campaigns."
        },
        "google_ads": {
            "issue": "Google Ads Retargeting is missing",
            "reason": "Google Ads conversion and remarketing tags are absent.",
            "business_impact": "Inability to run effective Google Display or Search remarketing campaigns.",
            "how_to_fix": "Install the Google Ads tag via GTM.",
            "estimated_time": "15 minutes",
            "priority": "High",
            "expected_score_increase": 7,
            "recommendation": "Set up Google Ads tags to reach previous visitors when they search on Google or browse other sites."
        },
        "linkedin_insight": {
            "issue": "LinkedIn Insight Tag is missing",
            "reason": "Cannot track B2B professional demographics or conversions from LinkedIn ads.",
            "business_impact": "Missed opportunity for high-value B2B lead generation and retargeting.",
            "how_to_fix": "Add the LinkedIn Insight Tag to your website footer or via GTM.",
            "estimated_time": "10 minutes",
            "priority": "Medium",
            "expected_score_increase": 7,
            "recommendation": "Add the Insight Tag to measure conversions and retarget B2B audiences on LinkedIn."
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
            "expected_score_increase": 4,
            "recommendation": "Add a clear contact form to capture visitor inquiries directly."
        },
        "whatsapp": {
            "issue": "WhatsApp integration missing",
            "reason": "No wa.me or WhatsApp API links found.",
            "business_impact": "Losing mobile users who prefer instant messaging over emails.",
            "how_to_fix": "Add a WhatsApp floating button linking to your business number.",
            "estimated_time": "15 minutes",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Enable WhatsApp chat to let visitors connect with you instantly."
        },
        "live_chat": {
            "issue": "Live Chat Widget missing",
            "reason": "No customer support chat scripts detected.",
            "business_impact": "Delayed response to customer objections, leading to lost sales.",
            "how_to_fix": "Integrate tools like Tawk.to, Intercom, or Zendesk.",
            "estimated_time": "30 minutes",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Install a chat tool to engage visitors in real-time."
        },
        "crm": {
            "issue": "CRM integration missing",
            "reason": "No HubSpot, Salesforce, or Zoho tracking scripts found.",
            "business_impact": "Manual lead entry, causing delays and potential loss of valuable prospects.",
            "how_to_fix": "Install your CRM's tracking pixel on the website.",
            "estimated_time": "20 minutes",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Connect your site to a CRM to automate lead tracking."
        },
        "lead_popup": {
            "issue": "Lead Popup missing",
            "reason": "No exit-intent or newsletter popup detected.",
            "business_impact": "Failing to capture the 90% of visitors who leave without buying.",
            "how_to_fix": "Use a tool like OptinMonster or Mailchimp to create a lead magnet popup.",
            "estimated_time": "1 hour",
            "priority": "Low",
            "expected_score_increase": 4,
            "recommendation": "Use exit-intent or timed popups to capture emails before visitors leave."
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
            "expected_score_increase": 4,
            "recommendation": "Upgrade to secure HTTPS to protect user data and improve search rankings."
        },
        "ssl": {
            "issue": "SSL Certificate is invalid or missing",
            "reason": "The site does not have a valid, trusted SSL certificate.",
            "business_impact": "Users will see a 'Your connection is not private' error, destroying trust.",
            "how_to_fix": "Obtain a free certificate from Let's Encrypt or your hosting provider.",
            "estimated_time": "1 hour",
            "priority": "High",
            "expected_score_increase": 4,
            "recommendation": "Ensure you have a valid, trusted SSL certificate to prevent browser warning screens."
        },
        "privacy_policy": {
            "issue": "Privacy Policy missing",
            "reason": "No link to a privacy policy found in the page.",
            "business_impact": "Non-compliance with GDPR/CCPA, risk of fines, and advertising accounts getting banned.",
            "how_to_fix": "Generate a Privacy Policy and link it in the footer.",
            "estimated_time": "1 hour",
            "priority": "High",
            "expected_score_increase": 4,
            "recommendation": "Create a Privacy Policy page to satisfy legal requirements and build trust."
        },
        "terms": {
            "issue": "Terms & Conditions missing",
            "reason": "No link to Terms & Conditions found.",
            "business_impact": "Legal vulnerability regarding user disputes and liability.",
            "how_to_fix": "Generate a Terms & Conditions page and link it in the footer.",
            "estimated_time": "1 hour",
            "priority": "Medium",
            "expected_score_increase": 4,
            "recommendation": "Publish Terms & Conditions to protect your business liability."
        },
        "contact_page": {
            "issue": "Contact page link missing",
            "reason": "Could not find a dedicated link to a contact page.",
            "business_impact": "Reduces brand legitimacy and frustrates users trying to reach you.",
            "how_to_fix": "Create a Contact Us page and add it to the main navigation or footer.",
            "estimated_time": "30 minutes",
            "priority": "High",
            "expected_score_increase": 4,
            "recommendation": "Create a dedicated contact page with clear business details."
        }
    },
    "seo_ai": {
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
            "expected_score_increase": 3,
            "recommendation": "Write a compelling meta description to improve click-through rates from search results."
        },
        "sitemap": {
            "issue": "Sitemap.xml not found",
            "reason": "No sitemap detected at the standard /sitemap.xml path.",
            "business_impact": "Search engines may take longer to index new pages.",
            "how_to_fix": "Generate an XML sitemap and submit it to Google Search Console.",
            "estimated_time": "30 minutes",
            "priority": "Medium",
            "expected_score_increase": 3,
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
            "expected_score_increase": 3,
            "recommendation": "Add an llms.txt file at the root of your domain to guide AI crawlers and LLM search agents indexing your business offerings."
        }
    }
}

def detect_multiple(patterns: List[str], text: str) -> Tuple[bool, int, str]:
    """Helper to detect any of the patterns. Returns (found, confidence, matched_pattern)."""
    text_lower = text.lower()
    for p in patterns:
        if p.lower() in text_lower:
            # 90-99% confidence based on typical match
            return True, 95, p
    return False, 0, "None"

async def check_url_status(client: httpx.AsyncClient, base_url: str, path: str) -> bool:
    parsed = urllib.parse.urlparse(base_url)
    target = f"{parsed.scheme}://{parsed.netloc}/{path.lstrip('/')}"
    try:
        response = await client.get(target, timeout=15.0, follow_redirects=True)
        return response.status_code in [200, 301, 302]
    except Exception:
        return False

async def fetch_html_playwright(url: str) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=20000)
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"Playwright error: {e}")
        return ""

async def run_scan(url: str) -> Dict[str, Any]:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    html_content = ""
    https_detected = url.startswith("https://")
    ssl_valid = False
    
    # 1. Standard HTTPX Fetch
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url)
            html_content = response.text
            ssl_valid = https_detected
        except httpx.ConnectTimeout:
            raise Exception("Website connection timed out.")
        except httpx.ConnectError:
            raise Exception("Failed to connect to the website.")
        except httpx.TransportError as e:
            if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                try:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers, verify=False) as client_unverified:
                        response = await client_unverified.get(url)
                        html_content = response.text
                        ssl_valid = False 
                except Exception as inner_e:
                    raise Exception(f"SSL handshake failed: {str(inner_e)}")
            else:
                raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to scan website: {str(e)}")

    # 2. Check if Javascript Rendered SPA (e.g. React, Angular, Vue)
    # If body has very little content, or typical root div
    soup = BeautifulSoup(html_content, "html.parser")
    body_text = soup.body.get_text(strip=True) if soup.body else ""
    is_spa = len(body_text) < 500 or soup.find(id=re.compile("^(root|app|__next)$", re.I))
    
    if is_spa:
        print("Detected SPA, rendering with Playwright...")
        pw_html = await fetch_html_playwright(url)
        if pw_html:
            html_content = pw_html
            soup = BeautifulSoup(html_content, "html.parser")

    text_content = html_content.lower()

    # 3. Check for aux files
    async with httpx.AsyncClient(headers=headers, verify=False) as client:
        sitemap_task = check_url_status(client, url, "sitemap.xml")
        robots_task = check_url_status(client, url, "robots.txt")
        llms_task = check_url_status(client, url, "llms.txt")
        sitemap_exists, robots_exists, llms_exists = await asyncio.gather(
            sitemap_task, robots_task, llms_task
        )

    # Helper function to format check result
    def _cr(found: bool, conf: int, method: str) -> dict:
        return {"found": found, "confidence": conf, "method": method}

    # =========================================================================
    # MEASUREMENT PILLAR (Max 20 points, 4 checks = 5 points each)
    # =========================================================================
    m_ga_found, m_ga_conf, m_ga_meth = detect_multiple(
        ["gtag(", "googletagmanager.com/gtag", "G-", "UA-", "google-analytics.com", "ga.js"], text_content)
    
    m_gtm_found, m_gtm_conf, m_gtm_meth = detect_multiple(
        ["GTM-", "googletagmanager.com", "dataLayer"], text_content)
        
    m_clar_found, m_clar_conf, m_clar_meth = detect_multiple(
        ["clarity.ms"], text_content)
        
    m_hot_found, m_hot_conf, m_hot_meth = detect_multiple(
        ["static.hotjar.com", "hotjar"], text_content)

    measurement_checks = {
        "google_analytics": _cr(m_ga_found, m_ga_conf, m_ga_meth),
        "gtm": _cr(m_gtm_found, m_gtm_conf, m_gtm_meth),
        "clarity": _cr(m_clar_found, m_clar_conf, m_clar_meth),
        "hotjar": _cr(m_hot_found, m_hot_conf, m_hot_meth)
    }
    measurement_score = sum(5 for v in measurement_checks.values() if v["found"])

    # =========================================================================
    # RETARGETING PILLAR (Max 20 points, 3 checks = 6.66 points each)
    # =========================================================================
    r_meta_found, r_meta_conf, r_meta_meth = detect_multiple(
        ["fbq(", "connect.facebook.net", "Meta Pixel"], text_content)
        
    r_gads_found, r_gads_conf, r_gads_meth = detect_multiple(
        ["gtag('config'", "googleads", "aw-"], text_content)
        
    r_li_found, r_li_conf, r_li_meth = detect_multiple(
        ["snap.licdn.com", "linkedin.com/profile.js"], text_content)

    retargeting_checks = {
        "meta_pixel": _cr(r_meta_found, r_meta_conf, r_meta_meth),
        "google_ads": _cr(r_gads_found, r_gads_conf, r_gads_meth),
        "linkedin_insight": _cr(r_li_found, r_li_conf, r_li_meth)
    }
    retargeting_score = sum((20.0 / 3.0) for v in retargeting_checks.values() if v["found"])

    # =========================================================================
    # CONVERSION PILLAR (Max 20 points, 5 checks = 4 points each)
    # =========================================================================
    c_form_found = bool(soup.find("form") or soup.find("input", type="email"))
    c_form_meth = "<form> tag" if c_form_found else "None"
    
    c_wa_found, c_wa_conf, c_wa_meth = detect_multiple(
        ["wa.me", "api.whatsapp.com", "whatsapp://"], text_content)
        
    c_chat_found, c_chat_conf, c_chat_meth = detect_multiple(
        ["tawk.to", "intercom", "zendesk", "crisp", "drift", "livechat"], text_content)
        
    c_crm_found, c_crm_conf, c_crm_meth = detect_multiple(
        ["hubspot", "zoho", "salesforce", "freshworks"], text_content)
        
    c_popup_found, c_popup_conf, c_popup_meth = detect_multiple(
        ["popup", "modal", "lightbox", "optinmonster", "newsletter"], text_content)

    conversion_checks = {
        "contact_form": _cr(c_form_found, 90 if c_form_found else 0, c_form_meth),
        "whatsapp": _cr(c_wa_found, c_wa_conf, c_wa_meth),
        "live_chat": _cr(c_chat_found, c_chat_conf, c_chat_meth),
        "crm": _cr(c_crm_found, c_crm_conf, c_crm_meth),
        "lead_popup": _cr(c_popup_found, 80 if c_popup_found else 0, c_popup_meth)
    }
    conversion_score = sum(4 for v in conversion_checks.values() if v["found"])

    # =========================================================================
    # TRUST PILLAR (Max 20 points, 5 checks = 4 points each)
    # =========================================================================
    nav_links = [a.get('href', '').lower() for a in soup.find_all('a')]
    
    t_privacy = any("privacy" in link for link in nav_links)
    t_terms = any("terms" in link or "conditions" in link for link in nav_links)
    t_contact = any("contact" in link for link in nav_links)

    trust_checks = {
        "https": _cr(https_detected, 100, "URL Scheme"),
        "ssl": _cr(ssl_valid, 100, "Certificate Validation"),
        "privacy_policy": _cr(t_privacy, 95 if t_privacy else 0, "Navigation Link Scan"),
        "terms": _cr(t_terms, 95 if t_terms else 0, "Navigation Link Scan"),
        "contact_page": _cr(t_contact, 95 if t_contact else 0, "Navigation Link Scan")
    }
    trust_score = sum(4 for v in trust_checks.values() if v["found"])

    # =========================================================================
    # SEO / AI PILLAR (Max 20 points, 8 checks = 2.5 points each)
    # =========================================================================
    s_title = soup.title is not None and len(soup.title.text.strip()) > 0
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    s_desc = desc_tag is not None and len(desc_tag.get("content", "").strip()) > 0
    s_schema = "application/ld+json" in text_content or "schema.org" in text_content
    s_og = soup.find("meta", property=re.compile(r"og:", re.I)) is not None
    s_tw = soup.find("meta", attrs={"name": re.compile(r"twitter:", re.I)}) is not None

    seo_checks = {
        "meta_title": _cr(s_title, 99 if s_title else 0, "<title> tag"),
        "meta_description": _cr(s_desc, 99 if s_desc else 0, "<meta name='description'>"),
        "sitemap": _cr(sitemap_exists, 100 if sitemap_exists else 0, "/sitemap.xml HTTP Check"),
        "robots": _cr(robots_exists, 100 if robots_exists else 0, "/robots.txt HTTP Check"),
        "schema_markup": _cr(s_schema, 95 if s_schema else 0, "JSON-LD Script or schema.org"),
        "opengraph": _cr(s_og, 99 if s_og else 0, "og: meta tags"),
        "twitter_card": _cr(s_tw, 99 if s_tw else 0, "twitter: meta tags"),
        "llms_txt": _cr(llms_exists, 100 if llms_exists else 0, "/llms.txt HTTP Check")
    }
    seo_score = sum(2.5 for v in seo_checks.values() if v["found"])

    # Compile scores
    overall_score = int(round(measurement_score + retargeting_score + conversion_score + trust_score + seo_score))
    overall_score = min(100, max(0, overall_score))

    if overall_score >= 90:
        grade = "Excellent"
    elif overall_score >= 70:
        grade = "Good"
    elif overall_score >= 50:
        grade = "Average"
    else:
        grade = "Needs Improvement"

    # Generate detailed recommendations
    recommendations = []
    for pillar, checks in [
        ("measurement", measurement_checks),
        ("retargeting", retargeting_checks),
        ("conversion", conversion_checks),
        ("trust", trust_checks),
        ("seo_ai", seo_checks)
    ]:
        for key, result in checks.items():
            if not result["found"] and key in RECOMMENDATION_TEMPLATES[pillar]:
                tmpl = RECOMMENDATION_TEMPLATES[pillar][key]
                recommendations.append({
                    "pillar": pillar,
                    "item": key,
                    "issue": tmpl["issue"],
                    "reason": tmpl["reason"],
                    "business_impact": tmpl["business_impact"],
                    "how_to_fix": tmpl["how_to_fix"],
                    "estimated_time": tmpl["estimated_time"],
                    "priority": tmpl["priority"],
                    "expected_score_increase": tmpl["expected_score_increase"],
                    "recommendation": tmpl["recommendation"]
                })

    return {
        "url": url,
        "overall_score": overall_score,
        "grade": grade,
        "pillar_scores": {
            "measurement": measurement_score,
            "retargeting": retargeting_score,
            "conversion": conversion_score,
            "trust": trust_score,
            "seo_ai": seo_score
        },
        "checks": {
            "measurement": measurement_checks,
            "retargeting": retargeting_checks,
            "conversion": conversion_checks,
            "trust": trust_checks,
            "seo_ai": seo_checks
        },
        "recommendations": recommendations,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
