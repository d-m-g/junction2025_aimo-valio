"""
Text Normalization Module
Handles voice-to-text transcription characteristics and normalizes text for better parsing
"""

import re
from typing import Dict


class TextNormalizer:
    """Normalizes text from voice-to-text converters"""
    
    # Filler words and hesitations (language-specific)
    FILLER_WORDS = {
        'en': ['um', 'uh', 'er', 'ah', 'like', 'you know', 'actually', 'basically', 'literally', 'so', 'well', 'hmm'],
        'fi': ['öö', 'ää', 'tuota', 'niin', 'siis', 'no', 'no niin'],
        'sv': ['öhm', 'eh', 'alltså', 'liksom', 'typ', 'va']
    }
    
    # Number word mappings
    NUMBER_WORDS = {
        'en': {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
            'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20',
            'thirty': '30', 'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
            'eighty': '80', 'ninety': '90', 'hundred': '100',
            'a couple': '2', 'a few': '3', 'several': '5'
        },
        'fi': {
            'nolla': '0', 'yksi': '1', 'kaksi': '2', 'kolme': '3', 'neljä': '4', 'viisi': '5',
            'kuusi': '6', 'seitsemän': '7', 'kahdeksan': '8', 'yhdeksän': '9', 'kymmenen': '10',
            'pari': '2', 'muutama': '3'
        },
        'sv': {
            'noll': '0', 'en': '1', 'ett': '1', 'två': '2', 'tre': '3', 'fyra': '4', 'fem': '5',
            'sex': '6', 'sju': '7', 'åtta': '8', 'nio': '9', 'tio': '10',
            'ett par': '2', 'några': '3'
        }
    }
    
    # Common transcription errors (homophones, misheard words)
    TRANSCRIPTION_FIXES = {
        'en': {
            r'\bto\b': 'two',  # Context-dependent, but common
            r'\bfor\b': 'four',  # Context-dependent
            r'\bhash\b': '#',
            r'\bnumber sign\b': '#',
            r'\bpound sign\b': '#',
        }
    }
    
    def __init__(self):
        """Initialize text normalizer"""
        pass
    
    def normalize(self, text: str, language: str = 'en') -> str:
        """
        Normalize text from voice-to-text
        
        Args:
            text: Input text from voice-to-text
            language: Detected language
            
        Returns:
            Normalized text
        """
        if not text:
            return text
        
        # Step 1: Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Step 2: Remove filler words
        text = self._remove_filler_words(text, language)
        
        # Step 3: Normalize contractions (handle both with and without apostrophe)
        text = self._normalize_contractions(text, language)
        
        # Step 4: Fix common transcription errors
        text = self._fix_transcription_errors(text, language)
        
        # Step 5: Normalize spoken numbers (optional - can be done in entity extraction)
        # text = self._normalize_spoken_numbers(text, language)
        
        # Step 6: Normalize punctuation and spacing
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = text.strip()
        
        return text
    
    def _remove_filler_words(self, text: str, language: str) -> str:
        """Remove filler words and hesitations"""
        fillers = self.FILLER_WORDS.get(language, self.FILLER_WORDS['en'])
        text_lower = text.lower()
        
        for filler in fillers:
            # Remove filler words with word boundaries
            pattern = r'\b' + re.escape(filler) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_contractions(self, text: str, language: str) -> str:
        """Normalize contractions to handle both forms"""
        if language != 'en':
            return text
        
        # Common contractions - normalize to standard form
        contractions = {
            r"don't": "do not",
            r"doesn't": "does not",
            r"didn't": "did not",
            r"won't": "will not",
            r"can't": "cannot",
            r"couldn't": "could not",
            r"shouldn't": "should not",
            r"wouldn't": "would not",
            r"isn't": "is not",
            r"aren't": "are not",
            r"wasn't": "was not",
            r"weren't": "were not",
            r"haven't": "have not",
            r"hasn't": "has not",
            r"hadn't": "had not",
            r"i'm": "i am",
            r"you're": "you are",
            r"we're": "we are",
            r"they're": "they are",
            r"it's": "it is",
            r"that's": "that is",
            r"what's": "what is",
            r"i'll": "i will",
            r"you'll": "you will",
            r"we'll": "we will",
            r"i'd": "i would",
            r"you'd": "you would",
            r"i've": "i have",
            r"you've": "you have",
        }
        
        for contraction, expansion in contractions.items():
            text = re.sub(contraction, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_transcription_errors(self, text: str, language: str) -> str:
        """Fix common voice-to-text transcription errors"""
        if language not in self.TRANSCRIPTION_FIXES:
            return text
        
        fixes = self.TRANSCRIPTION_FIXES[language]
        for pattern, replacement in fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_spoken_number(self, text: str, language: str = 'en') -> str:
        """
        Convert spoken numbers to digits (e.g., "two" -> "2")
        This is optional and can be called separately if needed
        """
        number_words = self.NUMBER_WORDS.get(language, self.NUMBER_WORDS['en'])
        
        for word, digit in number_words.items():
            # Replace with word boundaries
            pattern = r'\b' + re.escape(word) + r'\b'
            text = re.sub(pattern, digit, text, flags=re.IGNORECASE)
        
        return text

