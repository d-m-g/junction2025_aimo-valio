"""
Language Detection Module
Detects language from text input (English, Finnish, Swedish)
"""

import re
from typing import Dict, List


class LanguageDetector:
    """Detects language using character patterns and common words"""
    
    # Common words/phrases for each language
    LANGUAGE_INDICATORS = {
        'en': [
            r'\b(yes|no|ok|okay|accept|reject|confirm|decline|hello|hi|thanks|thank you|please|sorry|problem|issue|delivery|order|status|feedback)\b',
            r'\b(that|this|would|could|should|will|can|want|need|like)\b'
        ],
        'fi': [
            r'\b(kyllä|ei|okei|hyväksy|hylkää|vahvista|kiitos|hei|moi|anteeksi|ongelma|toimitus|tilaus|tila|palautetta)\b',
            r'\b(se|tämä|tuo|voisi|voisit|haluan|tarvitsen|pitäisi)\b'
        ],
        'sv': [
            r'\b(ja|nej|okej|acceptera|avvisa|bekräfta|tack|hej|hejdå|ursäkta|problem|leverans|beställning|status|feedback)\b',
            r'\b(det|den|skulle|kunde|vill|behöver|gillar)\b'
        ]
    }
    
    # Character-based patterns
    FINNISH_CHARS = r'[äöåÄÖÅ]'
    SWEDISH_CHARS = r'[åäöÅÄÖ]'
    
    def detect(self, text: str) -> str:
        """
        Detect language from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code: 'en', 'fi', 'sv', or 'en' as default
        """
        if not text:
            return 'en'
        
        text_lower = text.lower()
        scores: Dict[str, float] = {'en': 0.0, 'fi': 0.0, 'sv': 0.0}
        
        # Check for Finnish characters
        if re.search(self.FINNISH_CHARS, text):
            scores['fi'] += 2.0
        
        # Check for Swedish characters
        if re.search(self.SWEDISH_CHARS, text):
            scores['sv'] += 2.0
        
        # Check language indicators
        for lang, patterns in self.LANGUAGE_INDICATORS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                scores[lang] += matches * 0.5
        
        # Normalize scores by text length
        text_length = len(text.split())
        if text_length > 0:
            for lang in scores:
                scores[lang] = scores[lang] / max(text_length, 1)
        
        # Return language with highest score, default to English
        detected_lang = max(scores.items(), key=lambda x: x[1])[0]
        
        # If no strong indicators, default to English
        if scores[detected_lang] < 0.1:
            return 'en'
        
        return detected_lang

