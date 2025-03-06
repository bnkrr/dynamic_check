import re
from typing import Dict, Any, List, Iterable
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page
import json
import yaml

class FingerprintDetectionError(Exception):
    """Base exception for fingerprint detection errors"""

class FingerprintDetector:
    def __init__(self, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context(ignore_https_errors=True)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def check_target(self, url: str, checks: List[Dict], timeout: int = 30) -> Dict:
        page = self.context.new_page()
        result = {
            "url": url,
            "success": False,
            "checks": [],
            "error": None
        }

        try:
            page.set_default_timeout(timeout * 1000)
            response = page.goto(url)
            page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            
            if not response.ok:
                raise FingerprintDetectionError(f"HTTP {response.status}")

            # Collect base page information
            page_info = {
                "title": page.title(),
                "content": page.content(),
                "headers": response.headers,
                "cookies": self.context.cookies(),
                "url": page.url,
            }

            # Execute all checks
            for check in checks:
                check_result = self._execute_check(check, page, page_info)
                result["checks"].append(check_result)

            result["success"] = all(c["success"] for c in result["checks"])

        except Exception as e:
            result["error"] = str(e)
        finally:
            page.close()

        return result

    def _execute_check(self, check: Dict, page, page_info: Dict) -> Dict:
        check_type = check["type"]
        handler = {
            "header": self._check_header,
            "cookie": self._check_cookie,
            "element": self._check_element,
            "url": self._check_url,
            "js_variable": self._check_js_variable,
            "title": self._check_title,
            "content": self._check_content
        }.get(check_type)

        if not handler:
            return {
                "type": check_type,
                "success": False,
                "expected": check.get("value"),
                "found": None,
                "error": f"Unknown check type: {check_type}"
            }

        try:
            return handler(check, page_info, page)
        except Exception as e:
            return {
                "type": check_type,
                "success": False,
                "expected": check.get("value"),
                "found": None,
                "error": str(e)
            }

    def _check_header(self, check: Dict, page_info: Dict, _) -> Dict:
        headers = {k.lower(): v for k, v in page_info["headers"].items()}
        header_name = check["name"].lower()
        expected = check.get("value")
        
        found = headers.get(header_name)
        success = (found == expected) if expected else (found is not None)
        
        return {
            "type": "header",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_url(self, check: Dict, page_info: Dict, _) -> Dict:
        expected = check["value"]
        found = page_info["url"]
        success = (found == expected)
        
        return {
            "type": "url",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_cookie(self, check: Dict, page_info: Dict, _) -> Dict:
        cookie_name = check["name"]
        expected = check.get("value")
        cookies = {c["name"]: c["value"] for c in page_info["cookies"]}
        
        found = cookies.get(cookie_name)
        success = (found == expected) if expected else (found is not None)
        
        return {
            "type": "cookie",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_element(self, check: Dict, page_info: Dict, _) -> Dict:
        soup = BeautifulSoup(page_info["content"], "html.parser")
        element = soup.select_one(check["selector"])
        
        if not element:
            return {
                "type": "element",
                "success": False,
                "expected": check.get("value"),
                "found": None,
                "error": "Element not found"
            }

        attribute = check.get("attribute")
        expected = check.get("value")
        
        if attribute:
            found = element.get(attribute)
        else:
            found = element.text.strip()

        success = (found == expected) if expected else (found is not None)
        
        return {
            "type": "element",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_js_variable(self, check: Dict, _, page: Page) -> Dict:
        result = page.evaluate(f"JSON.stringify({check['name']})")
        
        try:
            found = json.loads(result) if result != "undefined" else None
        except json.JSONDecodeError:
            found = result

        expected = check.get("value")
        success = (found == expected) if expected else (found is not None)
        
        return {
            "type": "js_variable",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_title(self, check: Dict, page_info: Dict, _) -> Dict:
        expected = check["value"]
        found = page_info["title"]
        success = (found == expected)
        
        return {
            "type": "title",
            "success": success,
            "expected": expected,
            "found": found,
            "error": None
        }

    def _check_content(self, check: Dict, page_info: Dict, _) -> Dict:
        pattern = re.compile(check["pattern"])
        found = bool(pattern.search(page_info["content"]))
        
        return {
            "type": "content",
            "success": found,
            "expected": check["pattern"],
            "found": found,
            "error": None
        }
        
class FingerprintDetectorWithTemplate(FingerprintDetector):
    def __init__(self, template: Dict|str, headless: bool = True, timeout=None):
        super().__init__(headless)
        
        if isinstance(template, str):
            self.template = self.load_template(template)
        else:
            self.template = template

        # P0: direct setting of timeout each check
        # P1: direct setting of timeout
        # P2: template setting of timeout
        # P3: default timeout (30)
        if timeout is not None:
            self.timeout = timeout
        else:
            self.timeout = self.template.get("timeout", 30)

    @staticmethod
    def load_template(template_path: str) -> dict:
        try:
            with open(template_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise FingerprintDetectionError(f"Config error: {str(e)}")

    @staticmethod
    def url_append_path(url, path):
        if url.endswith("/") and path.startswith("/"):
            return url + path[1:]
        elif not url.endswith("/") and not path.startswith("/"):
            return url + "/" + path
        else:
            return url + path

    def check_target_with_template(self, base_url: str, timeout: int = None) -> Dict:
        if timeout is None:
            timeout = self.timeout
        url = self.url_append_path(base_url, self.template.get("path", "/"))
        return super().check_target(url, self.template["checks"], timeout)
    
    def iter_check_targets(self, base_urls: Iterable[str], timeout: int = None):
        for base_url in base_urls:
            yield self.check_target_with_template(base_url, timeout)

