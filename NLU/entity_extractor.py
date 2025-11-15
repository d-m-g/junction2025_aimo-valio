"""
Entity Extraction Module
Extracts entities like products, quantities, sentiment, urgency from text
"""

import re
from typing import Dict, List, Optional

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

try:
    from textblob import TextBlob
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

from config import config
from product_catalog import ProductCatalog


class EntityExtractor:
    """Extracts entities from text using patterns and product catalog"""
    
    def __init__(self):
        """Initialize entity extractor"""
        self.product_catalog = ProductCatalog()
        self.fuzzy_threshold = config.get('product_matching.fuzzy_threshold', 0.7)
        self.max_fuzzy_results = config.get('product_matching.max_fuzzy_results', 5)
        
        # Quantity patterns
        self.quantity_patterns = [
            r'\b(\d+)\s*(?:x|×|pcs?|pieces?|units?|kpl|kappaletta|st|stycken)\b',
            r'\b(\d+)\s*(?:pack|packs?|paketti|paket|förpackning)\b',
            r'\b(\d+)\s*(?:liter|l|liters?|litra|liter)\b',
            r'\b(\d+)\s*(?:kg|kilogram|kilograms?|kilo|kilogramma)\b',
            r'\b(\d+)\s*(?:g|gram|grams?|gramma)\b',
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten|yksi|kaksi|kolme|neljä|viisi|en|två|tre|fyra|fem)\b'
        ]
        
        # Urgency indicators
        self.urgency_patterns = {
            'en': [
                r'\b(urgent|asap|as soon as possible|immediately|right away|now|today|quickly|fast|rush)\b',
                r'\b(need|needed).*\b(urgent|immediately|now|today)\b'
            ],
            'fi': [
                r'\b(kiireellinen|heti|nyt|tänään|pikaisesti|nopeasti|kiire)\b',
                r'\b(tarvitsen|tarvitaan).*\b(heti|nyt|tänään|kiireellisesti)\b'
            ],
            'sv': [
                r'\b(brådskande|snabbt|nu|idag|omedelbart|skyndsamt|bråttom)\b',
                r'\b(behöver|behövs).*\b(nu|idag|omedelbart|brådskande)\b'
            ]
        }
        
        # Negation patterns for better sentiment detection
        self.negation_patterns = {
            'en': [
                r'\b(no|not|don\'?t|doesn\'?t|didn\'?t|won\'?t|can\'?t|couldn\'?t|shouldn\'?t|wouldn\'?t|isn\'?t|aren\'?t|wasn\'?t|weren\'?t)\b',
                r'\b(never|nothing|nobody|nowhere|neither|nor)\b'
            ],
            'fi': [
                r'\b(ei|en|et|emme|ette|eivät|ei ole|ei ollut)\b',
                r'\b(ei koskaan|ei mitään|ei kukaan)\b'
            ],
            'sv': [
                r'\b(inte|ej|aldrig|ingenting|ingen)\b',
                r'\b(är inte|var inte|skulle inte)\b'
            ]
        }
    
    def extract(self, text: str, language: str, context: Optional[Dict] = None, priority_entities: Optional[List[str]] = None, detected_intent: Optional[str] = None) -> Dict:
        """
        Extract entities from text
        
        Args:
            text: Input text
            language: Detected language
            context: Optional context
            priority_entities: Optional list of entity types to prioritize (boost confidence)
            detected_intent: Optional detected intent (used for context-aware sentiment)
            
        Returns:
            Dictionary of extracted entities
        """
        # Extract all entities
        entities = {
            'products': self._extract_products(text, language, context),
            'quantities': self._extract_quantities(text),
            'order_numbers': self._extract_order_numbers(text, language),
            'dates': self._extract_dates(text, language),
            'reasons': self._extract_reasons(text, language),
            'sentiment': self._extract_sentiment(text, language, detected_intent),
            'urgency': self._extract_urgency(text, language),
            'language': language
        }
        
        # Apply priority boosting if specified
        if priority_entities:
            for entity_type in priority_entities:
                if entity_type in entities:
                    if isinstance(entities[entity_type], list):
                        # Boost confidence for list entities
                        for entity in entities[entity_type]:
                            if isinstance(entity, dict) and 'confidence' in entity:
                                entity['confidence'] = min(1.0, entity['confidence'] * 1.2)
                    elif isinstance(entities[entity_type], dict) and 'confidence' in entities[entity_type]:
                        # Boost confidence for dict entities
                        entities[entity_type]['confidence'] = min(1.0, entities[entity_type]['confidence'] * 1.2)
        
        return entities
    
    def _extract_products(self, text: str, language: str, context: Optional[Dict] = None) -> List[Dict]:
        """
        Extract product mentions from text
        
        Args:
            text: Input text
            language: Detected language
            context: Optional context (may contain proposed_substitute to boost matching)
            
        Returns:
            List of product entities with GTIN, name, confidence
        """
        products = []
        text_lower = text.lower()
        
        # Check if context has proposed_substitute to boost matching
        proposed_substitute = None
        if context and 'proposed_substitute' in context:
            proposed_substitute = context['proposed_substitute']
        
        # Get product catalog
        catalog = self.product_catalog.get_catalog()
        
        if not catalog:
            # If no catalog, try to extract product names from text
            # Simple heuristic: look for capitalized words that might be product names
            product_words = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
            for word in product_words[:3]:  # Limit to first 3 matches
                if len(word.split()) <= 4:  # Reasonable product name length
                    products.append({
                        'name': word,
                        'gtin': None,
                        'confidence': 0.3
                    })
            return products
        
        # Match against product catalog
        for product in catalog:
            product_name = product.get('name', '').lower()
            product_name_variants = product.get('name_variants', [])
            
            # Check main name
            if product_name and product_name in text_lower:
                products.append({
                    'name': product.get('name'),
                    'gtin': product.get('gtin'),
                    'confidence': 0.8
                })
                continue
            
            # Check variants
            for variant in product_name_variants:
                if variant.lower() in text_lower:
                    products.append({
                        'name': product.get('name'),
                        'gtin': product.get('gtin'),
                        'confidence': 0.7
                    })
                    break
            
            # Partial match (word-level)
            product_words = product_name.split()
            if len(product_words) > 1:
                matched_words = sum(1 for word in product_words if word in text_lower)
                if matched_words >= len(product_words) * 0.6:  # 60% word match
                    products.append({
                        'name': product.get('name'),
                        'gtin': product.get('gtin'),
                        'confidence': 0.5
                    })
        
        # Fuzzy matching if available and no exact matches
        if FUZZY_AVAILABLE and len(products) < 3:
            fuzzy_products = self._fuzzy_match_products(text_lower, catalog)
            # Add fuzzy matches that aren't already in products
            existing_names = {p.get('name', '').lower() for p in products}
            for fp in fuzzy_products:
                if fp.get('name', '').lower() not in existing_names:
                    products.append(fp)
        
        # Boost proposed_substitute if mentioned in text
        if proposed_substitute:
            proposed_lower = proposed_substitute.lower()
            for product in products:
                if product.get('name', '').lower() == proposed_lower or proposed_lower in product.get('name', '').lower():
                    product['confidence'] = min(1.0, product.get('confidence', 0.5) * 1.3)
                    # Move to front of list
                    products.remove(product)
                    products.insert(0, product)
                    break
        
        # Remove duplicates
        seen = set()
        unique_products = []
        for product in products:
            key = (product.get('gtin'), product.get('name'))
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products[:self.max_fuzzy_results]
    
    def _fuzzy_match_products(self, text_lower: str, catalog: List[Dict]) -> List[Dict]:
        """
        Use fuzzy matching to find products
        
        Args:
            text_lower: Lowercase input text
            catalog: Product catalog
            
        Returns:
            List of matched products with confidence
        """
        if not FUZZY_AVAILABLE or not catalog:
            return []
        
        # Extract potential product names from text (capitalized words, quoted strings)
        potential_names = []
        # Look for quoted strings
        quoted = re.findall(r'"([^"]+)"', text_lower)
        potential_names.extend(quoted)
        # Look for capitalized sequences
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text_lower)
        potential_names.extend(capitalized)
        
        if not potential_names:
            # Try matching against all catalog products
            product_names = [p.get('name', '') for p in catalog if p.get('name')]
            if not product_names:
                return []
            
            # Find best matches in text
            best_matches = process.extract(
                text_lower,
                product_names,
                limit=self.max_fuzzy_results,
                scorer=fuzz.partial_ratio
            )
            
            results = []
            for match_name, score, _ in best_matches:
                if score >= self.fuzzy_threshold * 100:  # Convert to 0-100 scale
                    # Find product in catalog
                    for product in catalog:
                        if product.get('name') == match_name:
                            results.append({
                                'name': product.get('name'),
                                'gtin': product.get('gtin'),
                                'confidence': score / 100.0  # Convert back to 0-1
                            })
                            break
            
            return results
        
        # Match potential names against catalog
        results = []
        for potential_name in potential_names[:3]:  # Limit to first 3
            product_names = [p.get('name', '') for p in catalog if p.get('name')]
            if not product_names:
                continue
            
            best_match = process.extractOne(
                potential_name,
                product_names,
                scorer=fuzz.ratio
            )
            
            if best_match:
                match_name, score, _ = best_match
                if score >= self.fuzzy_threshold * 100:
                    # Find product in catalog
                    for product in catalog:
                        if product.get('name') == match_name:
                            results.append({
                                'name': product.get('name'),
                                'gtin': product.get('gtin'),
                                'confidence': score / 100.0
                            })
                            break
        
        return results
    
    def _extract_quantities(self, text: str) -> List[Dict]:
        """
        Extract quantities from text
        
        Args:
            text: Input text
            
        Returns:
            List of quantity entities
        """
        quantities = []
        text_lower = text.lower()
        
        # Number word mapping
        number_words = {
            'en': {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10},
            'fi': {'yksi': 1, 'kaksi': 2, 'kolme': 3, 'neljä': 4, 'viisi': 5, 'kuusi': 6, 'seitsemän': 7, 'kahdeksan': 8, 'yhdeksän': 9, 'kymmenen': 10},
            'sv': {'en': 1, 'två': 2, 'tre': 3, 'fyra': 4, 'fem': 5, 'sex': 6, 'sju': 7, 'åtta': 8, 'nio': 9, 'tio': 10}
        }
        
        # Extract numeric quantities
        for pattern in self.quantity_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1) if match.groups() else match.group(0)
                
                # Try to parse as number
                try:
                    value = int(value_str)
                except ValueError:
                    # Try word mapping
                    value = None
                    for lang_words in number_words.values():
                        if value_str.lower() in lang_words:
                            value = lang_words[value_str.lower()]
                            break
                    
                    if value is None:
                        continue
                
                unit = match.group(0).replace(value_str, '').strip()
                quantities.append({
                    'value': value,
                    'unit': unit if unit else 'unit',
                    'confidence': 0.8
                })
        
        # Extract standalone numbers (potential quantities)
        standalone_numbers = re.findall(r'\b(\d+)\b', text)
        for num_str in standalone_numbers[:3]:  # Limit to first 3
            num = int(num_str)
            if 1 <= num <= 100:  # Reasonable quantity range
                quantities.append({
                    'value': num,
                    'unit': 'unit',
                    'confidence': 0.4
                })
        
        return quantities[:5]  # Limit to top 5
    
    def _extract_sentiment(self, text: str, language: str, detected_intent: Optional[str] = None) -> Dict:
        """
        Extract sentiment from text using TextBlob (if available) combined with pattern matching
        
        Args:
            text: Input text
            language: Detected language
            detected_intent: Optional detected intent (for context-aware sentiment)
            
        Returns:
            Sentiment entity with polarity and confidence
        """
        text_lower = text.lower()
        has_negation = self._has_negation(text, language)
        
        # Check for questions and cancel words early
        is_question = text_lower.strip().endswith('?') or \
                     any(text_lower.startswith(q) for q in ['do you', 'can you', 'will you', 'are you', 'is it', 'is there', 'what', 'when', 'where', 'how', 'why', 'which'])
        cancel_words = ['cancel', 'stop', 'remove', 'delete', 'refund', 'return', 'reject', 'decline', 'refuse']
        has_cancel = any(word in text_lower for word in cancel_words)
        
        # Use TextBlob for English if available, but combine with pattern matching
        textblob_score = None
        if SENTIMENT_AVAILABLE and language == 'en':
            try:
                blob = TextBlob(text)
                textblob_score = blob.sentiment.polarity  # Range: -1.0 to 1.0
                subjectivity = blob.sentiment.subjectivity
                
                # Override TextBlob for questions (make neutral)
                if is_question:
                    textblob_score = 0.0  # Force neutral for all questions
                
                # Override TextBlob for cancel words (make negative)
                if has_cancel and textblob_score > 0:
                    textblob_score = -0.3
                
                # Override TextBlob for report_issue (make negative)
                if detected_intent == 'report_issue' and textblob_score > -0.2:
                    textblob_score = -0.4
            except Exception:
                pass
        
        # Get pattern-based sentiment (pass detected_intent for context-aware handling)
        pattern_result = self._extract_sentiment_patterns(text, language, detected_intent)
        
        # If TextBlob is available, combine both methods
        if textblob_score is not None:
            # TextBlob polarity
            if textblob_score > 0.05:  # Lower threshold
                textblob_polarity = 'positive'
                textblob_confidence = min(abs(textblob_score), 1.0)
            elif textblob_score < -0.05:  # Lower threshold
                textblob_polarity = 'negative'
                textblob_confidence = min(abs(textblob_score), 1.0)
            else:
                textblob_polarity = 'neutral'
                textblob_confidence = 0.3
            
            # If negation is present, flip TextBlob result
            if has_negation and textblob_polarity == 'positive':
                textblob_polarity = 'negative'
                textblob_confidence = min(textblob_confidence + 0.2, 1.0)
            
            # Combine TextBlob and pattern results (weighted average)
            if pattern_result['polarity'] == textblob_polarity:
                # Both agree - boost confidence
                final_polarity = textblob_polarity
                final_confidence = min(
                    (textblob_confidence * 0.6 + pattern_result['confidence'] * 0.4) * 1.2,
                    1.0
                )
            elif pattern_result['confidence'] > 0.6:
                # Pattern is more confident, use it
                final_polarity = pattern_result['polarity']
                final_confidence = pattern_result['confidence']
            else:
                # Use TextBlob if pattern is uncertain
                final_polarity = textblob_polarity
                final_confidence = textblob_confidence
            
            return {
                'polarity': final_polarity,
                'confidence': final_confidence,
                'method': 'textblob+pattern'
            }
        
        # Fallback: Pattern-based only
        return pattern_result
    
    def _has_negation(self, text: str, language: str) -> bool:
        """
        Check if text contains negation
        
        Args:
            text: Input text
            language: Detected language
            
        Returns:
            True if negation is detected
        """
        text_lower = text.lower()
        patterns = self.negation_patterns.get(language, self.negation_patterns['en'])
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_sentiment_patterns(self, text: str, language: str, detected_intent: Optional[str] = None) -> Dict:
        """
        Pattern-based sentiment extraction with improved word lists
        
        Args:
            text: Input text
            language: Detected language
            detected_intent: Optional detected intent (for context-aware sentiment)
            
        Returns:
            Sentiment entity with polarity and confidence
        """
        text_lower = text.lower()
        
        # Check for negation first
        has_negation = self._has_negation(text, language)
        
        # Expanded positive/negative word detection
        positive_words = {
            'en': [
                'yes', 'yeah', 'yep', 'good', 'great', 'excellent', 'perfect', 'wonderful', 'amazing',
                'thanks', 'thank you', 'thank', 'appreciate', 'agree', 'agreed', 'accept', 'accepted',
                'fine', 'ok', 'okay', 'sure', 'love', 'liked', 'happy', 'pleased', 'satisfied',
                'received', 'everything', 'all good', 'works', 'sounds good', 'please send', 'please do',
                'go ahead', 'proceed', 'that works', 'sounds good', 'i\'ll take', 'i will take', 'i want',
                'i\'d like', 'i would like', 'send it', 'send me', 'give me'
            ],
            'fi': ['kyllä', 'joo', 'hyvä', 'erinomainen', 'kiitos', 'sopii', 'okei', 'hyväksyn'],
            'sv': ['ja', 'bra', 'utmärkt', 'tack', 'okej', 'acceptera', 'godkänd']
        }
        
        negative_words = {
            'en': [
                'no', 'nope', 'nah', 'bad', 'terrible', 'awful', 'horrible', 'wrong', 'missing',
                'problem', 'issue', 'complaint', 'reject', 'refuse', 'decline', "don't", "won't", "can't",
                'disappointed', 'angry', 'upset', 'frustrated', 'unhappy', 'not interested', 'not good'
            ],
            'fi': ['ei', 'huono', 'ongelma', 'valitus', 'hylkään', 'kieltäydyn'],
            'sv': ['nej', 'dålig', 'problem', 'klagomål', 'avvisa']
        }
        
        pos_words = positive_words.get(language, positive_words['en'])
        neg_words = negative_words.get(language, negative_words['en'])
        
        # Count matches (word boundaries to avoid partial matches)
        positive_count = 0
        negative_count = 0
        
        for word in pos_words:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                positive_count += 1
        
        for word in neg_words:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                negative_count += 1
        
        # Special handling for phrases
        positive_phrases = {
            'en': [
                'i accept', 'i agree', 'that works', 'sounds good', 'go ahead', 'all good', 'thank you',
                'please send', 'please do', 'send it', 'send me', 'give me', 'yes please', 'yes i\'ll',
                'yes i will', 'i\'ll take', 'i will take', 'i want', 'i\'d like', 'i would like'
            ],
            'fi': ['sama käy', 'sopii mulle', 'lähetä', 'ota se'],
            'sv': ['det fungerar', 'det låter bra', 'skicka', 'ge mig', 'jag tar']
        }
        
        negative_phrases = {
            'en': ["don't want", "don't need", "don't like", "don't accept", 'no thanks', 'not interested'],
            'fi': ['en halua', 'ei kiitos'],
            'sv': ['vill inte', 'inte intresserad']
        }
        
        pos_phrases = positive_phrases.get(language, positive_phrases['en'])
        neg_phrases = negative_phrases.get(language, negative_phrases['en'])
        
        for phrase in pos_phrases:
            if phrase in text_lower:
                positive_count += 2  # Phrases are worth more
        
        for phrase in neg_phrases:
            if phrase in text_lower:
                negative_count += 2
        
        # Check for questions - questions should be neutral
        is_question = text_lower.strip().endswith('?') or \
                     any(text_lower.startswith(q) for q in ['do you', 'can you', 'will you', 'are you', 'is it', 'is there', 'what', 'when', 'where', 'how', 'why', 'which'])
        
        # Check for cancel/negative action words that override positive sentiment
        cancel_words = ['cancel', 'stop', 'remove', 'delete', 'refund', 'return', 'reject', 'decline', 'refuse']
        has_cancel = any(word in text_lower for word in cancel_words)
        
        # If negation is present, it likely negates positive sentiment
        if has_negation:
            if positive_count > 0:
                # Negation negates positive words
                negative_count += positive_count
                positive_count = 0
            elif negative_count == 0:
                # Just negation without other words = negative
                negative_count = 1
        
        # Cancel words override positive sentiment
        if has_cancel and positive_count > 0:
            negative_count += positive_count
            positive_count = 0
        
        # Questions are neutral unless there's strong negative/positive indicators
        if is_question:
            if negative_count > 2 or positive_count > 2:
                # Strong sentiment overrides question neutrality
                pass
            else:
                # Questions default to neutral
                polarity = 'neutral'
                confidence = 0.5
                return {
                    'polarity': polarity,
                    'confidence': confidence,
                    'method': 'pattern'
                }
        
        # Context-aware sentiment: request_callback and query intents are neutral
        # These are informational requests, not emotional expressions
        if detected_intent in ['request_callback', 'query_order_status', 'query_products', 'query_substitution']:
            # These intents are informational, not emotional - set to neutral
            # Only override if sentiment is weak (not strongly negative/positive)
            if negative_count <= 1 and positive_count <= 1:
                polarity = 'neutral'
                confidence = 0.5
                return {
                    'polarity': polarity,
                    'confidence': confidence,
                    'method': 'pattern+context'
                }
        
        # report_issue should always be negative (reporting a problem)
        if detected_intent == 'report_issue':
            polarity = 'negative'
            confidence = max(0.6, min(0.4 + (negative_count * 0.15), 0.95))
            return {
                'polarity': polarity,
                'confidence': confidence,
                'method': 'pattern+context'
            }
        
        # Determine polarity with better thresholds
        if negative_count > positive_count and negative_count > 0:
            polarity = 'negative'
            confidence = min(0.4 + (negative_count * 0.15), 0.95)
        elif positive_count > negative_count and positive_count > 0:
            polarity = 'positive'
            confidence = min(0.4 + (positive_count * 0.15), 0.95)
        else:
            polarity = 'neutral'
            confidence = 0.5
        
        return {
            'polarity': polarity,
            'confidence': confidence,
            'method': 'pattern'
        }
    
    def _extract_order_numbers(self, text: str, language: str) -> List[Dict]:
        """
        Extract order numbers from text (voice-to-text aware)
        
        Args:
            text: Input text
            language: Detected language
            
        Returns:
            List of order number entities
        """
        order_numbers = []
        text_lower = text.lower()
        
        # Common words to exclude from order number matches
        excluded_words = {'there', 'is', 'are', 'no', 'not', 'in', 'my', 'the', 'order', 'delivery', 
                         'this', 'that', 'these', 'those', 'was', 'were', 'has', 'have', 'had',
                         'from', 'with', 'to', 'for', 'of', 'on', 'at', 'by', 'a', 'an', 'the'}
        
        # Patterns for different languages (voice-to-text aware)
        patterns = {
            'en': [
                r'order\s(?:number)?\s(?:hash|#|number\s?sign)?\s*([A-Z0-9]{2,}[A-Z0-9\s-]*)',  # At least 2 alphanumeric chars, then more
                r'order\s#?\s*([A-Z0-9]{3,})',  # At least 3 alphanumeric chars (no spaces)
                r'order\s(?:number)?\s(?:one|two|three|four|five|six|seven|eight|nine|zero|\d+)\s*(?:one|two|three|four|five|six|seven|eight|nine|zero|\d+)\s*(?:one|two|three|four|five|six|seven|eight|nine|zero|\d+)',  # At least 3 number words
            ],
            'fi': [
                r'tilaus\s(?:numero)?\s(?:risuaita|#)?\s*([A-Z0-9\s-]+)',
                r'tilaus\s#?\s*([A-Z0-9-]+)',
            ],
            'sv': [
                r'beställning\s(?:nummer)?\s(?:hash|#)?\s*([A-Z0-9\s-]+)',
                r'beställning\s#?\s*([A-Z0-9-]+)',
            ]
        }
        
        lang_patterns = patterns.get(language, patterns['en'])
        
        for pattern in lang_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                order_num = match.group(1) if match.groups() else match.group(0)
                # Clean up: remove extra spaces, normalize
                order_num = re.sub(r'\s+', '', order_num.upper().strip())
                
                # Filter out common words that might be matched
                order_num_lower = order_num.lower()
                if order_num_lower in excluded_words:
                    continue
                
                # Check if it's mostly common words (should be mostly alphanumeric)
                if len(order_num) >= 2 and not all(c.isalnum() or c in '-_' for c in order_num):
                    # If it contains too many non-alphanumeric chars, skip
                    continue
                
                # Minimum reasonable order number length and should be mostly alphanumeric
                if order_num and len(order_num) >= 3 and sum(c.isalnum() for c in order_num) >= 2:
                    order_numbers.append({
                        'value': order_num,
                        'confidence': 0.8,
                        'raw_match': match.group(0)
                    })
        
        # Remove duplicates
        seen = set()
        unique_orders = []
        for order in order_numbers:
            if order['value'] not in seen:
                seen.add(order['value'])
                unique_orders.append(order)
        
        return unique_orders[:5]  # Limit to top 5
    
    def _extract_dates(self, text: str, language: str) -> List[Dict]:
        """
        Extract dates from text (relative and specific dates)
        
        Args:
            text: Input text
            language: Detected language
            
        Returns:
            List of date entities
        """
        dates = []
        text_lower = text.lower()
        
        # Relative date patterns
        relative_dates = {
            'en': {
                'today': 0,
                'tomorrow': 1,
                'yesterday': -1,
                'next week': 7,
                'last week': -7,
                'next monday': None,  # Will need calculation
                'this monday': None,
                'two days ago': -2,
                'in two days': 2,
            },
            'fi': {
                'tänään': 0,
                'huomenna': 1,
                'eilen': -1,
                'ensi viikko': 7,
                'viime viikko': -7,
            },
            'sv': {
                'idag': 0,
                'imorgon': 1,
                'igår': -1,
                'nästa vecka': 7,
                'förra veckan': -7,
            }
        }
        
        # Check for relative dates
        rel_dates = relative_dates.get(language, relative_dates['en'])
        for date_word, offset in rel_dates.items():
            if date_word in text_lower:
                dates.append({
                    'value': date_word,
                    'type': 'relative',
                    'offset_days': offset,
                    'confidence': 0.8
                })
        
        # Specific date patterns (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
        date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # DD/MM/YYYY or MM/DD/YYYY
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                parts = match.groups()
                if len(parts) == 3:
                    dates.append({
                        'value': match.group(0),
                        'type': 'specific',
                        'confidence': 0.7,
                        'raw_match': match.group(0)
                    })
        
        # Spoken date patterns (e.g., "the fifteenth", "on Monday")
        spoken_patterns = {
            'en': [
                r'\b(the|on)\s+(\d{1,2})(?:st|nd|rd|th)?\b',  # "the 15th", "on the 15th"
                r'\b(on|this|next|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            ],
            'fi': [
                r'\b(\d{1,2})\.?\s*(päivä|päivänä)\b',  # "15. päivä"
            ],
            'sv': [
                r'\b(på|den)\s+(\d{1,2})(?:e|a)?\b',  # "på 15:e"
            ]
        }
        
        lang_spoken = spoken_patterns.get(language, spoken_patterns['en'])
        for pattern in lang_spoken:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                dates.append({
                    'value': match.group(0),
                    'type': 'spoken',
                    'confidence': 0.6,
                    'raw_match': match.group(0)
                })
        
        # Remove duplicates
        seen = set()
        unique_dates = []
        for date in dates:
            key = date.get('value', '')
            if key and key not in seen:
                seen.add(key)
                unique_dates.append(date)
        
        return unique_dates[:5]  # Limit to top 5
    
    def _extract_reasons(self, text: str, language: str) -> List[Dict]:
        """
        Extract issue reasons from text
        
        Args:
            text: Input text
            language: Detected language
            
        Returns:
            List of reason entities
        """
        reasons = []
        text_lower = text.lower()
        
        # Reason patterns by language
        reason_patterns = {
            'en': {
                'damaged': ['damaged', 'broken', 'cracked', 'smashed', 'torn', 'ripped', 'bent', 'dented'],
                'missing': ['missing', 'not received', 'did not get', 'absent', 'gone', 'lost'],
                'wrong': ['wrong', 'incorrect', 'not what i ordered', 'different', 'not right', 'mistake'],
                'expired': ['expired', 'out of date', 'past due', 'old', 'stale'],
                'defective': ['defective', 'faulty', 'not working', 'broken', 'malfunctioning'],
                'incorrect_quantity': ['wrong amount', 'wrong quantity', 'too many', 'too few', 'not enough', 'too much'],
            },
            'fi': {
                'damaged': ['vahingoittunut', 'rikki', 'särkynyt', 'repeytynyt', 'taivutettu'],
                'missing': ['puuttuu', 'ei tullut', 'ei saapunut', 'kadonnut'],
                'wrong': ['väärä', 'virheellinen', 'ei oikea', 'eri', 'virhe'],
                'expired': ['vanhentunut', 'päättynyt', 'vanha'],
                'defective': ['viallinen', 'rikki', 'ei toimi'],
                'incorrect_quantity': ['väärä määrä', 'liikaa', 'liian vähän'],
            },
            'sv': {
                'damaged': ['skadad', 'trasig', 'söndrig', 'bucklad'],
                'missing': ['saknas', 'fick inte', 'mottog inte', 'försvunnen'],
                'wrong': ['fel', 'inkorrekt', 'inte rätt', 'annorlunda'],
                'expired': ['utgången', 'gammal', 'för gammal'],
                'defective': ['defekt', 'trasig', 'fungerar inte'],
                'incorrect_quantity': ['fel mängd', 'för mycket', 'för lite'],
            }
        }
        
        lang_reasons = reason_patterns.get(language, reason_patterns['en'])
        
        for reason_type, keywords in lang_reasons.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    reasons.append({
                        'type': reason_type,
                        'value': keyword,
                        'confidence': 0.7
                    })
                    break  # Only add once per reason type
        
        # Also check for phrases
        reason_phrases = {
            'en': [
                ('not working', 'defective'),
                ('did not arrive', 'missing'),
                ('never received', 'missing'),
                ('wrong item', 'wrong'),
                ('wrong product', 'wrong'),
            ],
            'fi': [
                ('ei toimi', 'defective'),
                ('ei tullut', 'missing'),
                ('väärä tuote', 'wrong'),
            ],
            'sv': [
                ('fungerar inte', 'defective'),
                ('kom inte', 'missing'),
                ('fel produkt', 'wrong'),
            ]
        }
        
        phrases = reason_phrases.get(language, reason_phrases['en'])
        for phrase, reason_type in phrases:
            if phrase in text_lower:
                # Check if we already have this reason type
                if not any(r['type'] == reason_type for r in reasons):
                    reasons.append({
                        'type': reason_type,
                        'value': phrase,
                        'confidence': 0.8
                    })
        
        return reasons[:5]  # Limit to top 5
    
    def _extract_urgency(self, text: str, language: str) -> Dict:
        """
        Extract urgency indicators from text
        
        Args:
            text: Input text
            language: Detected language
            
        Returns:
            Urgency entity with level and confidence
        """
        text_lower = text.lower()
        urgency_score = 0.0
        
        patterns = self.urgency_patterns.get(language, self.urgency_patterns['en'])
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            urgency_score += matches * 0.4
        
        if urgency_score > 0.3:
            level = 'high'
            confidence = min(urgency_score, 1.0)
        elif urgency_score > 0.1:
            level = 'medium'
            confidence = min(urgency_score, 0.7)
        else:
            level = 'low'
            confidence = 0.3
        
        return {
            'level': level,
            'confidence': confidence
        }

