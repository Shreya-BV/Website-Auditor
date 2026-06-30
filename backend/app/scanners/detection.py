from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
import re

class DetectionEngine:
    def __init__(self, html: str, soup: BeautifulSoup, rendered_by_pw: bool, pw_js_vars: dict):
        self.html = html
        self.html_lower = html.lower()
        self.soup = soup
        self.rendered_by_pw = rendered_by_pw
        self.pw_js_vars = pw_js_vars
        self.scripts = soup.find_all("script")
        self.links = soup.find_all("link")
        self.meta = soup.find_all("meta")

    def _check_signatures(self, signatures: List[str], regex_patterns: List[str] = None) -> Tuple[bool, int, str, Optional[str]]:
        """Returns (found, confidence, method, evidence)"""
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
            if sig.lower() in self.html_lower:
                return True, 70, "Raw HTML Match", f"Found keyword '{sig}' in DOM"
        if regex_patterns:
            for pat in regex_patterns:
                if re.search(pat, self.html, re.IGNORECASE):
                    return True, 70, "Raw HTML Regex", "Pattern matched in raw HTML"

        return False, 0, "None", None

    def check_multiple(self, tool_name: str, signatures: List[str], regex_patterns: List[str] = None) -> dict:
        found, conf, method, evidence = self._check_signatures(signatures, regex_patterns)
        return {"found": found, "confidence": conf, "method": method, "evidence": evidence}
