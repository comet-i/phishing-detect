import math
import re
from urllib.parse import urlparse

import tldextract


class FeatureExtractor:
    """Extract URL features while distinguishing host threats from valid URL syntax."""

    FEATURE_NAMES = [
        "url_length", "domain_length", "num_dots", "num_hyphens",
        "has_at_symbol", "has_ip", "domain_entropy",
    ]

    def __init__(self):
        self.extractor = tldextract.TLDExtract()

    def _calculate_entropy(self, value: str) -> float:
        if not value:
            return 0.0
        probabilities = [value.count(char) / len(value) for char in set(value)]
        return -sum(probability * math.log(probability, 2) for probability in probabilities)

    def extract_features(self, url: str) -> dict:
        if not url or not isinstance(url, str):
            return self._get_empty_features()

        candidate = url.strip()
        parsed = urlparse(candidate if "://" in candidate else f"http://{candidate}")
        hostname = (parsed.hostname or "").lower().rstrip(".")
        username = parsed.username or ""
        password = parsed.password or ""
        domain_info = self.extractor(hostname)

        has_credentials = 1 if username or password else 0
        has_at_symbol = 1 if has_credentials else 0
        invalid_hostname_chars = len(re.findall(r"[^a-z0-9.-]", hostname))
        has_ip = 1 if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", hostname) else 0
        scheme = parsed.scheme.lower()
        has_http = 1 if scheme == "http" else 0
        has_https = 1 if scheme == "https" else 0
        has_onion = 1 if hostname.endswith(".onion") or hostname == "onion" else 0
        # Explicit policy signal: these characters anywhere in the submitted
        # URL receive score 4, while HTTP and .onion receive score 5.
        has_dangerous_symbols = 1 if re.search(r"[@#$]", candidate) else 0

        return {
            "url_length": len(candidate),
            "domain_length": len(hostname),
            "num_dots": hostname.count("."),
            "num_hyphens": hostname.count("-"),
            "has_at_symbol": has_at_symbol,
            "has_credentials": has_credentials,
            "has_ip": has_ip,
            "domain_entropy": self._calculate_entropy(domain_info.domain),
            "invalid_hostname_chars": invalid_hostname_chars,
            "has_http": has_http,
            "has_https": has_https,
            "has_onion": has_onion,
            "has_dangerous_symbols": has_dangerous_symbols,
            "hostname": hostname,
        }

    def _get_empty_features(self) -> dict:
        return {
            "url_length": 0,
            "domain_length": 0,
            "num_dots": 0,
            "num_hyphens": 0,
            "has_at_symbol": 0,
            "has_credentials": 0,
            "has_ip": 0,
            "domain_entropy": 0.0,
            "invalid_hostname_chars": 0,
            "has_http": 0,
            "has_https": 0,
            "has_onion": 0,
            "has_dangerous_symbols": 0,
            "hostname": "",
        }
