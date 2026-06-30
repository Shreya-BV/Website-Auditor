from typing import List

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

class RecommendationEngine:
    @staticmethod
    def generate(pillar_checks: dict) -> List[dict]:
        recommendations = []
        for pillar, checks in pillar_checks.items():
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
        return recommendations
