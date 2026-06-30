from bs4 import BeautifulSoup
from typing import Tuple
import re

class DecisionEngine:
    @staticmethod
    def requires_playwright(html: str, soup: BeautifulSoup) -> Tuple[bool, str]:
        """
        Analyzes HTML quality to determine if it's a JS-rendered SPA.
        Returns (requires_pw, reason)
        """
        if not html or not soup:
            return True, "Empty HTML"
            
        body = soup.body
        if not body:
            return True, "Missing <body> tag"
            
        body_text = body.get_text(strip=True)
        html_size = len(html)
        
        # 1. Very small HTML size or empty text
        if html_size < 1000 and len(body_text) < 100:
            return True, "Very small HTML size with minimal text"
            
        # 2. Known SPA mount points
        spa_mounts = ["root", "app", "__next", "vue-app", "nuxt-app"]
        if soup.find(id=re.compile(f"^({'|'.join(spa_mounts)})$", re.I)):
            # Double check if there's actual content inside
            mount_node = soup.find(id=re.compile(f"^({'|'.join(spa_mounts)})$", re.I))
            if mount_node and len(mount_node.get_text(strip=True)) < 50:
                return True, f"Found empty SPA mount point: {mount_node.get('id')}"

        # 3. Missing structural elements often added by JS
        nav = soup.find(["nav", "header"])
        footer = soup.find("footer")
        if not nav and not footer and len(body_text) < 500:
            return True, "Missing structural elements (nav/footer) and low text content"

        # 4. Known framework runtime scripts
        scripts = [s.get('src', '') for s in soup.find_all('script') if s.get('src')]
        framework_patterns = [
            r"_next/static", r"nuxt", r"react(-dom)?\.production", r"vue\.runtime"
        ]
        for src in scripts:
            for pat in framework_patterns:
                if re.search(pat, src, re.I):
                    return True, f"Detected JS framework runtime: {src}"

        # 5. Cloudflare or DDoS protection pages
        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        if "attention required" in title or "cloudflare" in title or "just a moment" in title:
            return True, "Cloudflare/DDoS protection challenge detected"

        return False, "HTML appears sufficient"
