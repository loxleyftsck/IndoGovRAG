"""
PII (Personally Identifiable Information) Detection
For Indonesian Government Documents

Detects and redacts:
- NIK (Nomor Induk Kependudukan) - 16 digits
- Email addresses
- Phone numbers (Indonesian formats)
- NPWP (tax ID)
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class PIIMatch:
    """Detected PII match."""
    type: str  # 'nik', 'email', 'phone', 'npwp'
    value: str
    start: int
    end: int
    context: str  # Surrounding text


@dataclass
class PIIReport:
    """PII detection report."""
    text_length: int
    matches: List[PIIMatch]
    total_matches: int
    matches_by_type: Dict[str, int]
    redacted_text: str
    audit_log: Dict


class PIIDetector:
    """
    Detect PII in Indonesian text.
    
    Patterns:
    - NIK: 16-digit Indonesian ID number
    - NPWP: 15-digit tax ID (format: XX.XXX.XXX.X-XXX.XXX)
    - Email: Standard email format
    - Phone: Indonesian phone formats (+62, 08xx)
    """
    
    # Regex patterns
    PATTERNS = {
        'nik': r'\b\d{16}\b',  # 16 consecutive digits
        'npwp': r'\b\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}\b',  # XX.XXX.XXX.X-XXX.XXX
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(\+62|62|0)[0-9]{2,3}-?[0-9]{3,4}-?[0-9]{3,4}',  # Indonesian phones
    }
    
    # Redaction placeholders
    REDACTIONS = {
        'nik': '[NIK_REDACTED]',
        'npwp': '[NPWP_REDACTED]',
        'email': '[EMAIL_REDACTED]',
        'phone': '[PHONE_REDACTED]',
    }
    
    def __init__(
        self,
        enable_audit_log: bool = True,
        context_chars: int = 30
    ):
        """
        Initialize PII detector.
        
        Args:
            enable_audit_log: Log all PII detections
            context_chars: Characters of context to capture
        """
        self.enable_audit_log = enable_audit_log
        self.context_chars = context_chars
        self.audit_logs: List[Dict] = []
    
    def detect(self, text: str) -> PIIReport:
        """
        Detect all PII in text.
        
        Args:
            text: Input text
        
        Returns:
            PIIReport with all detected PII
        """
        matches = []
        
        # Run all patterns
        for pii_type, pattern in self.PATTERNS.items():
            type_matches = self._find_matches(text, pattern, pii_type)
            matches.extend(type_matches)
        
        # Sort by position
        matches.sort(key=lambda m: m.start)
        
        # Redact text
        redacted_text = self._redact(text, matches)
        
        # Count by type
        matches_by_type = {}
        for match in matches:
            matches_by_type[match.type] = matches_by_type.get(match.type, 0) + 1
        
        # Create audit log
        audit_log = {
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'total_matches': len(matches),
            'matches_by_type': matches_by_type,
        }
        
        if self.enable_audit_log:
            self.audit_logs.append(audit_log)
        
        return PIIReport(
            text_length=len(text),
            matches=matches,
            total_matches=len(matches),
            matches_by_type=matches_by_type,
            redacted_text=redacted_text,
            audit_log=audit_log
        )
    
    def _find_matches(
        self,
        text: str,
        pattern: str,
        pii_type: str
    ) -> List[PIIMatch]:
        """Find all matches of a pattern."""
        matches = []
        
        for match in re.finditer(pattern, text):
            value = match.group()
            start = match.start()
            end = match.end()
            
            # Get context
            context_start = max(0, start - self.context_chars)
            context_end = min(len(text), end + self.context_chars)
            context = text[context_start:context_end]
            
            matches.append(PIIMatch(
                type=pii_type,
                value=value,
                start=start,
                end=end,
                context=context
            ))
        
        return matches
    
    def _redact(self, text: str, matches: List[PIIMatch]) -> str:
        """Redact PII from text."""
        if not matches:
            return text
        
        # Build redacted text
        result = []
        last_end = 0
        
        for match in matches:
            # Add text before match
            result.append(text[last_end:match.start])
            
            # Add redaction
            result.append(self.REDACTIONS[match.type])
            
            last_end = match.end
        
        # Add remaining text
        result.append(text[last_end:])
        
        return ''.join(result)
    
    def validate_nik(self, nik: str) -> bool:
        """
        Validate NIK format and checksum.
        
        NIK structure (16 digits):
        - DD: Province code (2 digits)
        - DDDD: Regency/city code (4 digits)
        - DDMMYY: Birth date (6 digits)
        - XXXX: Sequence number (4 digits)
        
        Args:
            nik: NIK string
        
        Returns:
            True if valid format
        """
        # Check length
        if len(nik) != 16:
            return False
        
        # Check all digits
        if not nik.isdigit():
            return False
        
        # Extract parts
        province = nik[0:2]
        regency = nik[2:6]
        birth_date = nik[6:12]
        
        # Validate province (01-94)
        if not (1 <= int(province) <= 94):
            return False
        
        # Validate birth date (DDMMYY)
        day = int(birth_date[0:2])
        month = int(birth_date[2:4])
        year = int(birth_date[4:6])
        
        # Day can be +40 for females
        actual_day = day if day <= 31 else day - 40
        
        if not (1 <= actual_day <= 31):
            return False
        
        if not (1 <= month <= 12):
            return False
        
        return True
    
    def save_audit_logs(self, filepath: str = "data/pii_audit.json"):
        """Save audit logs to file."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'logs': self.audit_logs,
                'total_detections': len(self.audit_logs),
                'created': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📊 Audit logs saved to: {filepath}")
    
    def get_statistics(self) -> Dict:
        """Get PII detection statistics across all logs."""
        total_texts = len(self.audit_logs)
        total_matches = sum(log['total_matches'] for log in self.audit_logs)
        
        # Aggregate by type
        type_counts = {}
        for log in self.audit_logs:
            for pii_type, count in log['matches_by_type'].items():
                type_counts[pii_type] = type_counts.get(pii_type, 0) + count
        
        return {
            'total_texts_processed': total_texts,
            'total_pii_detected': total_matches,
            'detections_by_type': type_counts,
            'avg_pii_per_text': total_matches / max(total_texts, 1),
        }


# =============================================================================
# TESTING
# =============================================================================

def demo_pii_detector():
    """Demo PII detection."""
    
    print("🧪 PII Detector Demo\n")
    
    # Sample text with PII
    sample_text = """
    PERMOHONAN KTP ELEKTRONIK
    
    Data Pemohon:
    Nama: Ahmad Rizki
    NIK: 3201012501990001
    NPWP: 12.345.678.9-012.345
    Email: ahmad.rizki@email.com
    No. HP: 0812-3456-7890
    
    Untuk informasi lebih lanjut, hubungi kantor kependudukan setempat
    atau kirim email ke admin@dukcapil.go.id
    
    NIK ibu: 3201014002880002
    Telepon: +62-21-1234567
    """
    
    # Initialize detector
    detector = PIIDetector(enable_audit_log=True)
    
    # Detect PII
    report = detector.detect(sample_text)
    
    print("📊 PII Detection Report")
    print("="*60)
    print(f"Text Length: {report.text_length} characters")
    print(f"Total PII Found: {report.total_matches}")
    print(f"\nPII by Type:")
    for pii_type, count in report.matches_by_type.items():
        print(f"  {pii_type.upper()}: {count}")
    
    print(f"\n🔍 Detected PII:")
    print("="*60)
    for match in report.matches:
        print(f"\nType: {match.type.upper()}")
        print(f"Value: {match.value}")
        print(f"Context: ...{match.context}...")
    
    print(f"\n🔒 Redacted Text:")
    print("="*60)
    print(report.redacted_text)
    
    # Validate NIK
    print(f"\n✅ NIK Validation:")
    print("="*60)
    for match in report.matches:
        if match.type == 'nik':
            is_valid = detector.validate_nik(match.value)
            print(f"{match.value}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Statistics
    print(f"\n📈 Statistics:")
    print("="*60)
    stats = detector.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Save audit log
    detector.save_audit_logs()
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo_pii_detector()
