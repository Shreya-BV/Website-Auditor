import httpx
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List
import asyncio

# Define Recommendation generator based on failed checks
RECOMMENDATION_TEMPLATES = {
    "measurement": {
        "google_analytics": "Google Analytics is missing. Install Google Analytics to track visitor behavior and understand traffic sources.",
        "gtm": "Google Tag Manager (GTM) is missing. Use GTM to manage and deploy marketing tags without modifying code.",
        "clarity": "Microsoft Clarity is missing. Install Microsoft Clarity to see visitor session recordings and heatmaps.",
        "hotjar": "Hotjar is missing. Consider adding Hotjar to collect feedback and run user surveys on your website."
    },
    "retargeting": {
        "meta_pixel": "Meta Pixel is missing. Install Meta Pixel to retarget website visitors through Facebook and Instagram advertising campaigns.",
        "google_ads": "Google Ads Retargeting is missing. Set up Google Ads tags to reach previous visitors when they search on Google or browse other sites.",
        "linkedin_insight": "LinkedIn Insight Tag is missing. Add the Insight Tag to measure conversions and retarget B2B audiences on LinkedIn."
    },
    "conversion": {
        "contact_form": "No contact form detected. Add a clear contact form to capture visitor inquiries directly.",
        "whatsapp": "WhatsApp integration is missing. Enable WhatsApp chat to let visitors connect with you instantly.",
        "live_chat": "Live chat widget is missing. Install a chat tool (like Intercom, Drift, or Tawk.to) to engage visitors in real-time.",
        "crm": "CRM integration is missing. Connect your site to a CRM (HubSpot, Salesforce, Zoho) to automate lead tracking.",
        "lead_popup": "No popup lead form detected. Use exit-intent or timed popups to capture emails before visitors leave."
    },
    "trust": {
        "https": "Website does not force HTTPS. Upgrade to secure HTTPS to protect user data and improve search rankings.",
        "ssl": "SSL Certificate is invalid or self-signed. Ensure you have a valid, trusted SSL certificate to prevent browser warning screens.",
        "privacy_policy": "Privacy Policy is missing. Create a Privacy Policy page to satisfy legal requirements (GDPR/CCPA) and build trust.",
        "terms": "Terms & Conditions page is missing. Publish Terms & Conditions to protect your business liability.",
        "contact_page": "Contact page is missing. Create a dedicated contact page with clear business details."
    },
    "seo_ai": {
        "meta_title": "Meta Title is missing or empty. Write a unique, keyword-rich title tag to rank higher in search engines.",
        "meta_description": "Meta Description is missing. Write a compelling meta description to improve click-through rates from search results.",
        "sitemap": "Sitemap.xml not found. Create a sitemap to help search engines find and index all your website pages.",
        "robots": "Robots.txt not found. Add a robots.txt file to instruct search crawlers which pages they should or should not index.",
        "schema_markup": "Schema Markup is missing. Add structured data schema to help Google and AI assistants understand your business content.",
        "opengraph": "OpenGraph tags are missing. Add OpenGraph metadata to control how your pages look when shared on Facebook and LinkedIn.",
        "twitter_card": "Twitter Card metadata is missing. Set up Twitter Card tags to ensure rich previews on X (formerly Twitter).",
        "llms_txt": "llms.txt file is missing. Add an llms.txt file at the root of your domain to guide AI crawlers and LLM search agents indexing your business offerings."
    }
}

async def check_url_status(client: httpx.AsyncClient, base_url: str, path: str) -> bool:
    """Checks if a specific path (e.g. sitemap.xml) returns a successful response code."""
    parsed = urllib.parse.urlparse(base_url)
    target = f"{parsed.scheme}://{parsed.netloc}/{path.lstrip('/')}"
    try:
        # Perform a quick GET request with a 2.0s timeout
        response = await client.get(target, timeout=2.0, follow_redirects=True)
        return response.status_code in [200, 301, 302]
    except Exception:
        return False

async def run_scan(url: str) -> Dict[str, Any]:
    # Normalize URL
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
    
    # Try fetching with SSL verification first
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url)
            html_content = response.text
            ssl_valid = https_detected
        except httpx.ConnectTimeout:
            raise Exception("Website connection timed out. Please check if the site is online.")
        except httpx.ConnectError:
            raise Exception("Failed to connect to the website. The URL might be invalid or the site is down.")
        except httpx.TransportError as e:
            # Check for SSL validation error
            if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                # Retry with SSL verification disabled
                try:
                    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers, verify=False) as client_unverified:
                        response = await client_unverified.get(url)
                        html_content = response.text
                        ssl_valid = False  # HTTPS works but SSL certificate is invalid
                except Exception as inner_e:
                    raise Exception(f"SSL handshake failed and unverified fallback failed: {str(inner_e)}")
            else:
                raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to scan website: {str(e)}")

    soup = BeautifulSoup(html_content, "html.parser")
    text_content = html_content.lower()

    # We also check for auxiliary files asynchronously in parallel
    async with httpx.AsyncClient(headers=headers, verify=False) as client:
        sitemap_task = check_url_status(client, url, "sitemap.xml")
        robots_task = check_url_status(client, url, "robots.txt")
        llms_task = check_url_status(client, url, "llms.txt")
        sitemap_exists, robots_exists, llms_exists = await asyncio.gather(
            sitemap_task, robots_task, llms_task
        )

    # 1. MEASUREMENT PILLAR (Max 20 points, 5 checks, 4 pts each)
    measurement_checks = {
        "google_analytics": ("google-analytics.com" in text_content or "ga.js" in text_content),
        "gtm": ("googletagmanager.com" in text_content or "gtm-" in text_content),
        "clarity": ("clarity.ms" in text_content),
        "hotjar": ("hotjar" in text_content)
    }
    # GA4 check is whether gtag( is found, but also count it as true if we have googleanalytics or gtm
    measurement_checks["google_analytics"] = measurement_checks["google_analytics"] or "gtag(" in text_content
    # Let's add clarity / hotjar checks
    # Calculate score
    measurement_true_count = sum(1 for v in measurement_checks.values() if v)
    # Since hotjar and clarity are less common but good, we distribute score:
    # 5 checks total = GA, GTM, GA4, Clarity, Hotjar
    # Let's formalize checks exactly as required:
    # Google Analytics, Google Tag Manager, GA4 Tracking, Hotjar, Microsoft Clarity.
    m_ga = "google-analytics.com" in text_content or "ga.js" in text_content
    m_gtm = "googletagmanager.com" in text_content or "gtm-" in text_content
    m_ga4 = "gtag(" in text_content
    m_clarity = "clarity.ms" in text_content
    m_hotjar = "hotjar" in text_content

    measurement_checks = {
        "google_analytics": m_ga or m_ga4,
        "gtm": m_gtm,
        "clarity": m_clarity,
        "hotjar": m_hotjar
    }
    # Scoring: 4 checks here, let's distribute: GA/GA4, GTM, Clarity, Hotjar. If we have 4 items:
    # Let's count GA, GTM, Clarity, Hotjar. Let's make it 5 checks by splitting:
    # google_analytics (GA or GA4), gtm, clarity, hotjar.
    # To return exactly what's requested:
    # "google_analytics": true, "gtm": true, "clarity": false, "hotjar": false, "score": 50
    # Let's use these 4 keys exactly.
    # If 4 checks, each worth 5 points.
    measurement_score = sum(5 for v in measurement_checks.values() if v)

    # 2. RETARGETING PILLAR (Max 20 points, 3 checks)
    r_meta = "fbq(" in text_content or "connect.facebook.net" in text_content
    r_gads = "gtag('config'" in text_content or "googleads" in text_content
    r_li = "linkedin" in text_content or "linkedin.com/profile.js" in text_content

    retargeting_checks = {
        "meta_pixel": r_meta,
        "google_ads": r_gads,
        "linkedin_insight": r_li
    }
    retargeting_score = sum((20.0 / 3.0) for v in retargeting_checks.values() if v)
    retargeting_score = round(retargeting_score, 1)

    # 3. CONVERSION / CRM PILLAR (Max 20 points, 5 checks, 4 pts each)
    c_form = "<form" in text_content
    c_wa = "wa.me" in text_content or "api.whatsapp.com" in text_content
    c_chat = "tawk.to" in text_content or "intercom" in text_content or "drift" in text_content
    c_crm = "hubspot" in text_content or "salesforce" in text_content or "zoho" in text_content
    
    # Popup detection: check script classes or popular widgets
    c_popup = "popup" in text_content or "modal" in text_content or "lightbox" in text_content

    conversion_checks = {
        "contact_form": c_form,
        "whatsapp": c_wa,
        "live_chat": c_chat,
        "crm": c_crm,
        "lead_popup": c_popup
    }
    conversion_score = sum(4 for v in conversion_checks.values() if v)

    # 4. TRUST & SECURITY PILLAR (Max 20 points, 5 checks, 4 pts each)
    t_https = https_detected
    t_ssl = ssl_valid
    
    # Privacy Policy Page
    t_privacy = any(kw in text_content for kw in ["privacy-policy", "privacy policy", "privacy.html"])
    # Terms
    t_terms = any(kw in text_content for kw in ["terms-of-service", "terms and conditions", "terms.html", "terms-and-conditions", "terms/"])
    # Contact
    t_contact = any(kw in text_content for kw in ["contact-us", "contact us", "contact.html", "contact/"])

    trust_checks = {
        "https": t_https,
        "ssl": t_ssl,
        "privacy_policy": t_privacy,
        "terms": t_terms,
        "contact_page": t_contact
    }
    trust_score = sum(4 for v in trust_checks.values() if v)

    # 5. DISCOVERY / SEO / AI SEARCH PILLAR (Max 20 points, 8 checks, 2.5 pts each)
    s_title = soup.title is not None and len(soup.title.text.strip()) > 0
    
    # Meta Description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if not desc_tag:
         desc_tag = soup.find("meta", attrs={"name": "Description"})
    s_desc = desc_tag is not None and len(desc_tag.get("content", "").strip()) > 0

    s_sitemap = sitemap_exists or "sitemap.xml" in text_content
    s_robots = robots_exists or "robots.txt" in text_content
    s_schema = "application/ld+json" in text_content
    s_og = 'property="og:' in text_content or 'property=\'og:' in text_content
    s_tw = 'name="twitter:' in text_content or 'name=\'twitter:' in text_content
    s_llms = llms_exists or "llms.txt" in text_content

    seo_checks = {
        "meta_title": s_title,
        "meta_description": s_desc,
        "sitemap": s_sitemap,
        "robots": s_robots,
        "schema_markup": s_schema,
        "opengraph": s_og,
        "twitter_card": s_tw,
        "llms_txt": s_llms
    }
    seo_score = sum(2.5 for v in seo_checks.values() if v)

    # Compile scores & overall metrics
    overall_score = int(round(measurement_score + retargeting_score + conversion_score + trust_score + seo_score))
    
    # Cap at 100 just in case
    overall_score = min(100, max(0, overall_score))

    if overall_score >= 90:
        grade = "Excellent"
    elif overall_score >= 70:
        grade = "Good"
    elif overall_score >= 50:
        grade = "Average"
    else:
        grade = "Needs Improvement"

    # Generate recommendations
    recommendations = []
    # Loop over all checks and append message if False
    for pillar, checks in [
        ("measurement", measurement_checks),
        ("retargeting", retargeting_checks),
        ("conversion", conversion_checks),
        ("trust", trust_checks),
        ("seo_ai", seo_checks)
    ]:
        for key, val in checks.items():
            if not val and key in RECOMMENDATION_TEMPLATES[pillar]:
                recommendations.append({
                    "pillar": pillar,
                    "item": key,
                    "recommendation": RECOMMENDATION_TEMPLATES[pillar][key]
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
