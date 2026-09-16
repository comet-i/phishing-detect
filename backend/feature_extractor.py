# backend/feature_extractor.py
import re
import math
from urllib.parse import urlparse
import tldextract

class FeatureExtractor:
    """Layer 2: Converts raw URLs into numeric feature vectors."""
    
    def __init__(self):
        self.extractor = tldextract.TLDExtract()

    def _calculate_entropy(self, string: str) -> float:
        """Calculates Shannon entropy of a string."""
        if not string: return 0.0
        prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
        return -sum([p * math.log(p) / math.log(2.0) for p in prob])

    def extract_features(self, url: str) -> dict:
        """Extracts numeric features from a URL string."""
        if not url or not isinstance(url, str):
            return self._get_empty_features()

        parsed = urlparse(url if '://' in url else f'http://{url}')
        domain_info = self.extractor(url)
        
        # 1. Length Features
        url_length = len(url)
        domain_length = len(domain_info.domain)
        
        # 2. Character & Symbol Features
        num_dots = url.count('.')
        num_hyphens = url.count('-')
        has_at_symbol = 1 if '@' in url else 0
        
        # 3. IP Address Presence
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        has_ip = 1 if ip_pattern.match(domain_info.domain) else 0
        
        # 4. Entropy (High entropy in domain often indicates DGA/malicious)
        domain_entropy = self._calculate_entropy(domain_info.domain)

        return {
            'url_length': url_length,
            'domain_length': domain_length,
            'num_dots': num_dots,
            'num_hyphens': num_hyphens,
            'has_at_symbol': has_at_symbol,
            'has_ip': has_ip,
            'domain_entropy': domain_entropy
        }

    def _get_empty_features(self) -> dict:
        return {k: 0 for k in ['url_length', 'domain_length', 'num_dots', 
                               'num_hyphens', 'has_at_symbol', 'has_ip', 'domain_entropy']}
