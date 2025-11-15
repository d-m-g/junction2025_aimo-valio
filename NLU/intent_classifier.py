"""
Intent Classification Module
Classifies user intent from text using rule-based patterns
"""

import re
from typing import Dict, Optional, Tuple

from config import config

try:
    from semantic_intent_classifier import SemanticIntentClassifier
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticIntentClassifier = None


class IntentClassifier:
    """Classifies intents using regex patterns and context"""
    
    # Intent patterns by language
    INTENT_PATTERNS = {
        'confirm_substitution': {
            'en': [
                # Positive confirmation words (negation will be handled separately)
                r'\b(yes|yeah|yep|ok|okay|accept|agreed|sure|fine|good|approved|confirm|confirmed)\b',
                r'\b(i accept|i agree|that works|sounds good|go ahead|proceed)\b',
                r'\b(i\'?ll take|i want|i\'?d like|i\'?ll accept|take it|give me|send me)\b.*\b(replacement|substitute|alternative|instead)\b',
                r'\b(replace|substitute|swap).*\b(it|them|this|that)\b'
            ],
            'fi': [
                r'\b(kyllä|joo|okei|hyväksyn|sopii|hyvä|hyväksytty|vahvistan|sama käy|sopii mulle|ota se|anna se|lähetä se)\b',
                r'\b(otan|haluan|saan).*\b(korvauksen|vaihtoehdon|tilalle)\b'
            ],
            'sv': [
                r'\b(ja|okej|acceptera|godkänd|bekräfta|det fungerar|det låter bra|gå vidare|jag tar|jag vill ha|skicka)\b',
                r'\b(ersättning|alternativ|istället)\b'
            ]
        },
        'reject_substitution': {
            'en': [
                r'\b(no|nope|nah|decline|reject|refuse)\b',
                r'\b(don\'?t want|don\'?t need|don\'?t like|don\'?t accept)\b',
                r'\b(i don\'?t want|i don\'?t need|i don\'?t like|i don\'?t accept)\b',
                r'\b(no thanks|no thank you|not that|not interested|not acceptable)\b',
                r'\b(skip|cancel|remove|without|without it|leave it out|don\'?t send|don\'?t include)\b',
                r'\b(not|don\'?t|won\'?t|can\'?t).*\b(agree|accept|want|need|like)\b'
            ],
            'fi': [
                r'\b(ei|en halua|en tarvitse|hylkään|kieltäydyn|ei kiitos|ohita|poista|peruuta)\b',
                r'\b(ilman|jätä pois|älä lähetä|älä sisällytä)\b'
            ],
            'sv': [
                r'\b(nej|avvisa|jag vill inte|jag behöver inte|inte intresserad|hoppa över|ta bort|avbryt)\b',
                r'\b(utan|utan den|lämna bort|skicka inte|inkludera inte)\b'
            ]
        },
        'request_callback': {
            'en': [
                r'\b(call me|call back|callback|speak to|talk to|human|person|agent|representative|customer service)\b',
                r'\b(i want to|i need to|can i|may i|i would like to).*\b(speak|talk|call)\b',
                r'\b(contact me|reach me|get in touch)\b',
                r'\b(speak to|talk to).*\b(someone|human|person|agent|representative)\b',
                r'\b(i need|i want).*\b(to speak|to talk|to call|someone|human|person)\b'
            ],
            'fi': [
                r'\b(soita|soita takaisin|puhu|ihminen|henkilö|asiakaspalvelu|edustaja)\b',
                r'\b(haluan|tarvitsen|voinko).*\b(puhua|soittaa)\b',
                r'\b(ota yhteyttä|yhteydenotto)\b'
            ],
            'sv': [
                r'\b(ring mig|ring tillbaka|tala med|människa|person|agent|kundtjänst)\b',
                r'\b(jag vill|jag behöver|kan jag).*\b(tala|prata|ringa)\b',
                r'\b(kontakta mig|nå mig)\b'
            ]
        },
        'report_issue': {
            'en': [
                r'\b(missing|missed|didn\'?t receive|did not receive|not received|never received|didn\'?t get|did not get|not got|wrong|incorrect|damaged|broken|defective|problem|issue|complaint)\b',
                r'\b(item|product|order|delivery).*\b(missing|wrong|damaged|broken|not here|not delivered|didn\'?t arrive|did not arrive)\b',
                r'\b(there\'?s|there is|i have|i\'?m missing|i am missing).*\b(problem|issue|complaint|missing)\b',
                r'\b(i didn\'?t|i did not|i haven\'?t|i have not).*\b(receive|get|receive|obtain)\b',
                r'\b(only|just|merely).*\b(\d+).*\b(not|instead of|but not|but got|but received).*\b(\d+)\b',  # Quantity discrepancy: "only 2, not 3"
                r'\b(should be|should have|expected|supposed to be).*\b(\d+).*\b(but|got|received|have|is|are).*\b(\d+)\b',  # "should be 3 but got 2"
                r'\b(i see|i notice|i notice that|there is|there are).*\b(only|just|merely).*\b(\d+)\b',  # "I see there is only 2"
                r'\b(quantity|amount|number).*\b(wrong|incorrect|not right|not correct|doesn\'?t match|does not match)\b',
                # Patterns for "there is no X" or "not in my order"
                r'\b(there is|there\'?s|there are).*\b(no|not).*\b(in|from|with).*\b(my|the).*\b(order|delivery)\b',
                r'\b(in|from|with).*\b(my|the).*\b(order|delivery).*\b(there is|there\'?s|there are).*\b(no|not)\b',
                r'\b(not|no).*\b(in|from|with).*\b(my|the).*\b(order|delivery)\b',
                r'\b(my|the).*\b(order|delivery).*\b(doesn\'?t|does not|has no|have no|is missing|are missing)\b',
                r'\b(there is|there\'?s).*\b(no|not).*\b(product|item|thing)\b',  # "there is no milk"
            ],
            'fi': [
                r'\b(puuttuu|puuttui|ei tullut|ei saapunut|väärä|vahingoittunut|rikki|viallinen|ongelma|valitus)\b',
                r'\b(tuote|tilaus|toimitus).*\b(puuttuu|väärä|vahingoittunut|rikki|ei täällä|ei toimitettu)\b',
                r'\b(minulla on|siellä on).*\b(ongelma|valitus)\b'
            ],
            'sv': [
                r'\b(saknas|saknades|fick inte|mottog inte|fel|skadad|trasig|defekt|problem|klagomål)\b',
                r'\b(produkt|beställning|leverans).*\b(saknas|fel|skadad|trasig|inte här|inte levererad)\b',
                r'\b(det finns|jag har).*\b(problem|klagomål)\b'
            ]
        },
        'confirm_delivery': {
            'en': [
                r'\b(received|got it|arrived|delivered|everything is|all good|all here|complete|perfect|thank you)\b',
                r'\b(delivery|order).*\b(received|arrived|here|complete|good|perfect)\b',
                r'\b(everything|all items).*\b(here|received|arrived|good)\b'
            ],
            'fi': [
                r'\b(sain|tuli|saapui|toimitettu|kaikki on|kaikki hyvin|valmis|täydellinen|kiitos)\b',
                r'\b(toimitus|tilaus).*\b(saapui|täällä|valmis|hyvä|täydellinen)\b',
                r'\b(kaikki|kaikki tuotteet).*\b(täällä|saapui|hyvä)\b'
            ],
            'sv': [
                r'\b(mottog|kom|anlände|levererad|allt är|allt bra|komplett|perfekt|tack)\b',
                r'\b(leverans|beställning).*\b(anlände|här|komplett|bra|perfekt)\b',
                r'\b(allt|alla produkter).*\b(här|anlände|bra)\b'
            ]
        },
        'query_order_status': {
            'en': [
                r'\b(status|where is|when will|track|tracking|location|when|where)\b.*\b(order|delivery|package|shipment)\b',
                r'\b(what|when|where).*\b(order|delivery|package)\b',
                r'\b(is my|check my|my order|order status)\b',
                r'\b(i need|i want|i have to).*\b(get|receive|have).*\b(it|order|delivery)\b'  # "I have to get it tomorrow"
            ],
            'fi': [
                r'\b(tila|missä on|milloin|seuranta|sijainti|milloin|missä)\b.*\b(tilaus|toimitus|paketti)\b',
                r'\b(mikä|milloin|missä).*\b(tilaus|toimitus)\b',
                r'\b(minun tilaus|tilauksen tila|tarkista tilaus)\b'
            ],
            'sv': [
                r'\b(status|var är|när kommer|spårning|plats|när|var)\b.*\b(beställning|leverans|paket)\b',
                r'\b(vad|när|var).*\b(beställning|leverans)\b',
                r'\b(min beställning|beställningsstatus|kolla beställning)\b'
            ]
        },
        'provide_feedback': {
            'en': [
                r'\b(feedback|review|rating|rate|comment|opinion|suggestion|improve)\b',
                r'\b(how was|how did|what do you think|tell us|let us know)\b',
                r'\b(i want to|i\'?d like to).*\b(give|provide|leave).*\b(feedback|review|comment)\b'
            ],
            'fi': [
                r'\b(palautetta|arvostelu|arvio|kommentti|mielipide|ehdotus|parantaa)\b',
                r'\b(miten|mitä mieltä|kerro meille|kerro meille)\b',
                r'\b(haluan|haluaisin).*\b(antaa|jättää).*\b(palautetta|arvostelua|kommenttia)\b'
            ],
            'sv': [
                r'\b(feedback|recension|betyg|kommentar|åsikt|förslag|förbättra)\b',
                r'\b(hur var|hur gick|vad tycker du|berätta|låt oss veta)\b',
                r'\b(jag vill|jag skulle vilja).*\b(ge|lämna).*\b(feedback|recension|kommentar)\b'
            ]
        },
        'greeting': {
            'en': [
                r'\b^(hello|hi|hey|good morning|good afternoon|good evening|greetings)\b',
                r'\b(hello|hi|hey)\b.*\b(there|you)\b'
            ],
            'fi': [
                r'\b^(hei|moi|terve|hyvää päivää|päivää|iltaa)\b',
                r'\b(hei|moi|terve)\b.*\b(siellä|sinä)\b'
            ],
            'sv': [
                r'\b^(hej|hallå|god morgon|god eftermiddag|god kväll|hälsningar)\b',
                r'\b(hej|hallå)\b.*\b(där|du)\b'
            ]
        },
        'query_substitution': {
            'en': [
                r'\b(what|which|tell me about).*\b(replacement|substitute|alternative|substitution)\b',
                r'\b(what did you|what are you).*\b(suggest|propose|recommend|offer)\b',
                r'\b(what.*replacement|which.*substitute|what.*alternative)\b',
                r'\b(tell me|show me|what is).*\b(the replacement|the substitute|the alternative)\b'
            ],
            'fi': [
                r'\b(mikä|mitä|kerro).*\b(korvaus|vaihtoehto|korvaava)\b',
                r'\b(mikä on|mitä on).*\b(korvaus|vaihtoehto)\b',
                r'\b(kerro|näytä).*\b(korvaus|vaihtoehto)\b'
            ],
            'sv': [
                r'\b(vad|vilken|berätta).*\b(ersättning|alternativ|ersättare)\b',
                r'\b(vad är|vilken är).*\b(ersättning|alternativ)\b',
                r'\b(berätta|visa).*\b(ersättning|alternativ)\b'
            ]
        },
        'thank_you': {
            'en': [
                r'\b(thank you|thanks|thank|appreciate|appreciated|much appreciated|grateful)\b',
                r'\b(thanks a lot|thank you very much|thank you so much)\b',
                r'\b(i appreciate|i\'m grateful|many thanks)\b'
            ],
            'fi': [
                r'\b(kiitos|kiitoksia|kiitän|kiitoksia paljon|paljon kiitoksia)\b',
                r'\b(kiitos avusta|kiitos paljon)\b'
            ],
            'sv': [
                r'\b(tack|tack så mycket|tusen tack|tackar)\b',
                r'\b(jag tackar|tack för hjälpen)\b'
            ]
        },
        'change_delivery': {
            'en': [
                r'\b(change|modify|reschedule|move|shift).*\b(delivery|deliver|delivery time|delivery date|delivery address)\b',
                r'\b(different|another|new).*\b(time|date|address|location|place)\b.*\b(delivery|deliver)\b',
                r'\b(can i|can you|i want to|i need to|i have to).*\b(change|reschedule|modify|get|receive).*\b(delivery|deliver|it|order)\b',
                r'\b(deliver|delivery).*\b(to|at|on).*\b(different|another|new)\b',
                r'\b(i need|i want|i have to).*\b(get|receive|have).*\b(it|order|delivery).*\b(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(need|want|have to).*\b(it|order|delivery).*\b(tomorrow|today|by|on|at)\b'
            ],
            'fi': [
                r'\b(muuta|vaihda|siirrä|uudelleen).*\b(toimitus|toimitusaika|toimituspäivä|toimitusosoite)\b',
                r'\b(eri|toinen|uusi).*\b(aika|päivä|osoite|paikka).*\b(toimitus|toimitukselle)\b',
                r'\b(voinko|voisitko|haluan|tarvitsen).*\b(muuttaa|vaihtaa|siirtää).*\b(toimitus)\b'
            ],
            'sv': [
                r'\b(ändra|flytta|omplanera|förändra).*\b(leverans|leveransdag|leveranstid|leveransadress)\b',
                r'\b(annan|ny|annan).*\b(tid|datum|adress|plats).*\b(leverans|leverans)\b',
                r'\b(kan jag|kan du|jag vill|jag behöver).*\b(ändra|flytta|omplanera).*\b(leverans)\b'
            ]
        },
        'cancel_order': {
            'en': [
                r'\b(cancel|stop|canceled|cancelled).*\b(order|my order|the order|delivery)\b',
                r'\b(don\'?t|do not).*\b(deliver|send|ship)\b',
                r'\b(i want to|i need to|please).*\b(cancel|stop).*\b(order|delivery)\b',
                r'\b(cancel|stop|abort).*\b(it|the order|my order)\b'
            ],
            'fi': [
                r'\b(peruuta|peru|lopeta).*\b(tilaus|minun tilaus|tilaukseni|toimitus)\b',
                r'\b(älä|ei tarvitse).*\b(toimita|lähetä)\b',
                r'\b(haluan|tarvitsen|voisitko).*\b(peruuttaa|lopettaa).*\b(tilaus|toimitus)\b'
            ],
            'sv': [
                r'\b(avbryt|stoppa|avbokning).*\b(beställning|min beställning|leverans)\b',
                r'\b(leverera inte|skicka inte)\b',
                r'\b(jag vill|jag behöver|kan du).*\b(avbryta|stoppa).*\b(beställning|leverans)\b'
            ]
        },
        'query_products': {
            'en': [
                r'\b(do you have|do you sell|is available|is in stock|have available)\b',
                r'\b(what products|which products|what items|tell me about).*\b(do you have|are available)\b',
                r'\b(product info|product information|tell me about).*\b(product|item)\b',
                r'\b(is|are).*\b(available|in stock|you have)\b',
                r'\b(what|which).*\b(products|items).*\b(do you|are available|can i get)\b'
            ],
            'fi': [
                r'\b(onko teillä|myyttekö|on saatavilla|on varastossa)\b',
                r'\b(mitä tuotteita|mitkä tuotteet|kerro).*\b(onko|myyttekö|on saatavilla)\b',
                r'\b(tuotetiedot|tuotteen tiedot|kerro).*\b(tuotteesta|tuotteesta)\b',
                r'\b(onko|ovatko).*\b(saatavilla|varastossa|teillä)\b'
            ],
            'sv': [
                r'\b(har ni|säljer ni|finns|är tillgänglig|är i lager)\b',
                r'\b(vilka produkter|vilka varor|berätta).*\b(har ni|finns|är tillgängliga)\b',
                r'\b(produktinfo|produktinformation|berätta).*\b(om produkt|om varan)\b',
                r'\b(finns|är).*\b(tillgänglig|i lager|har ni)\b'
            ]
        }
    }
    
    def __init__(self):
        """Initialize intent classifier"""
        # Compile patterns for performance
        self.compiled_patterns = {}
        for intent, lang_patterns in self.INTENT_PATTERNS.items():
            self.compiled_patterns[intent] = {}
            for lang, patterns in lang_patterns.items():
                self.compiled_patterns[intent][lang] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]
        
        # Initialize semantic classifier if available and enabled
        self.semantic_classifier = None
        if SEMANTIC_AVAILABLE and config.get('nlu.use_semantic_fallback', True):
            try:
                self.semantic_classifier = SemanticIntentClassifier()
                if not self.semantic_classifier.is_available():
                    self.semantic_classifier = None
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize semantic classifier: {e}")
                self.semantic_classifier = None
    
    def classify(self, text: str, language: str, context: Optional[Dict] = None) -> Tuple[str, float]:
        """
        Classify intent from text
        
        Args:
            text: Input text to classify
            language: Detected language code
            context: Optional context (order_number, customer_id, conversation_stage, etc.)
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        if not text:
            return 'unknown', 0.0
        
        text_lower = text.lower()
        intent_scores: Dict[str, float] = {}
        
        # Get conversation stage from context for context-aware boosting
        conversation_stage = context.get('conversation_stage') if context else None
        
        # Check for negation first
        has_negation = self._has_negation(text_lower, language)
        
        # Check each intent pattern
        for intent, lang_patterns in self.compiled_patterns.items():
            score = 0.0
            patterns = lang_patterns.get(language, lang_patterns.get('en', []))
            
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                if matches:
                    # Score based on number of matches and pattern specificity
                    score += len(matches) * 0.3
                    # Boost if full match (not just partial)
                    if pattern.search(text_lower):
                        score += 0.5
            
            # Penalize confirm_substitution if negation is present
            if intent == 'confirm_substitution' and has_negation:
                score *= 0.1  # Heavily penalize
            
            # Boost reject_substitution if negation is present
            if intent == 'reject_substitution' and has_negation:
                score *= 1.5  # Boost
            
            # Prioritize request_callback over report_issue when callback phrases are present
            if intent == 'request_callback':
                callback_phrases = ['speak to', 'talk to', 'need to speak', 'want to speak', 'someone', 'human', 'person', 'agent']
                if any(phrase in text_lower for phrase in callback_phrases):
                    score *= 1.5  # Boost callback intent
            
            # Penalize report_issue if request_callback phrases are present
            if intent == 'report_issue':
                callback_phrases = ['speak to', 'talk to', 'need to speak', 'want to speak', 'someone', 'human', 'person', 'agent']
                if any(phrase in text_lower for phrase in callback_phrases):
                    score *= 0.3  # Heavily penalize report_issue when callback intent is more appropriate
            
            # Boost report_issue if quantity discrepancy patterns are detected
            if intent == 'report_issue':
                # Check for quantity discrepancy phrases
                discrepancy_phrases = [
                    'only', 'not', 'should be', 'expected', 'but got', 'but received',
                    'instead of', 'quantity', 'amount', 'number'
                ]
                if any(phrase in text_lower for phrase in discrepancy_phrases):
                    # Check if there are numbers in the text (likely quantities)
                    numbers = re.findall(r'\b\d+\b', text_lower)
                    if len(numbers) >= 2:  # At least 2 numbers suggests quantity comparison
                        score *= 1.5
                
                # Boost for "there is no" or "not in my order" patterns
                issue_phrases = ['there is no', "there's no", 'there are no', 'not in my order', 'missing from my order', 'in my order there is no']
                if any(phrase in text_lower for phrase in issue_phrases):
                    score *= 2.0  # Strong boost for these patterns
            
            # Penalize reject_substitution when "in my order" is present (more likely to be report_issue)
            if intent == 'reject_substitution':
                if 'in my order' in text_lower or 'from my order' in text_lower:
                    score *= 0.3  # Heavily penalize - this is likely report_issue, not rejection
            
            # Boost change_delivery or query_order_status for time-related requests
            if intent in ['change_delivery', 'query_order_status']:
                time_words = ['tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'next week']
                need_words = ['need', 'want', 'have to', 'must', 'should', 'get', 'receive']
                if any(time_word in text_lower for time_word in time_words) and any(need_word in text_lower for need_word in need_words):
                    score *= 1.4  # Boost if time word + need word present
            
            if score > 0:
                intent_scores[intent] = score
        
        # Context-based adjustments based on conversation stage
        if conversation_stage == 'pre_order_substitution':
            # Pre-order: Boost substitution-related intents
            if 'confirm_substitution' in intent_scores:
                intent_scores['confirm_substitution'] *= 1.8
            if 'reject_substitution' in intent_scores:
                intent_scores['reject_substitution'] *= 1.8
            if 'query_substitution' in intent_scores:
                intent_scores['query_substitution'] *= 1.5
            # Lower threshold for simple yes/no responses
            if text_lower.strip() in ['yes', 'yeah', 'yep', 'ok', 'okay', 'sure']:
                if 'confirm_substitution' not in intent_scores:
                    intent_scores['confirm_substitution'] = 0.7
            if text_lower.strip() in ['no', 'nope', 'nah']:
                if 'reject_substitution' not in intent_scores:
                    intent_scores['reject_substitution'] = 0.7
        
        elif conversation_stage == 'post_delivery_investigation':
            # Post-delivery: Boost issue-related intents
            if 'report_issue' in intent_scores:
                intent_scores['report_issue'] *= 1.8
            if 'confirm_delivery' in intent_scores:
                intent_scores['confirm_delivery'] *= 1.5
            if 'query_order_status' in intent_scores:
                intent_scores['query_order_status'] *= 1.5
            # If proposed_solution exists, boost solution acceptance/rejection
            if context and context.get('proposed_solution'):
                if 'confirm_substitution' in intent_scores:
                    intent_scores['confirm_substitution'] *= 1.5
                if 'reject_substitution' in intent_scores:
                    intent_scores['reject_substitution'] *= 1.5
            # Boost report_issue for phrases like "didn't receive", "missing", "there is no", etc.
            issue_indicators = ["didn't receive", "did not receive", "not receive", "missing", "didn't get", 
                              "there is no", "there's no", "not in my order", "missing from my order"]
            if any(phrase in text_lower for phrase in issue_indicators):
                if 'report_issue' not in intent_scores:
                    intent_scores['report_issue'] = 0.7
                else:
                    intent_scores['report_issue'] *= 1.5
        
        # Legacy context-based adjustments (for backward compatibility)
        if context and not conversation_stage:
            # If context has substitution info, boost substitution intents
            if 'substitution' in str(context).lower() or 'replacement' in str(context).lower():
                if 'confirm_substitution' in intent_scores:
                    intent_scores['confirm_substitution'] *= 1.5
                if 'reject_substitution' in intent_scores:
                    intent_scores['reject_substitution'] *= 1.5
        
        # Normalize scores and calculate confidence
        if intent_scores:
            max_score = max(intent_scores.values())
            total_score = sum(intent_scores.values())
            
            # Normalize by max score
            for intent in intent_scores:
                intent_scores[intent] = intent_scores[intent] / max(max_score, 1.0)
            
            # Get best intent
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            base_confidence = best_intent[1]
            
            # Adjust confidence based on:
            # 1. How dominant the best intent is (if multiple intents match, lower confidence)
            # 2. Text length and specificity (shorter/vague text = lower confidence)
            num_matching_intents = len(intent_scores)
            dominance_ratio = base_confidence / max(total_score / max_score, 1.0) if total_score > 0 else base_confidence
            
            # Penalize for vague text (short, common words)
            text_words = len(text.split())
            vague_penalty = 1.0
            if text_words <= 4:  # Very short text
                vague_penalty = 0.85
            if num_matching_intents > 1:  # Multiple intents matched
                vague_penalty *= 0.9
            
            # Calculate final confidence
            confidence = min(base_confidence * dominance_ratio * vague_penalty, 0.95)  # Cap at 95%
            
            # Ensure minimum confidence for matched intents
            confidence = max(confidence, 0.5)
            
            rule_based_intent = best_intent[0]
            rule_based_confidence = confidence
            rule_based_scores = intent_scores.copy()  # Keep scores for combination
        else:
            rule_based_intent = 'unknown'
            rule_based_confidence = 0.3
            rule_based_scores = {}
        
        # Hybrid approach: Use semantic similarity as fallback
        semantic_threshold = config.get('nlu.semantic_threshold', 0.5)
        use_semantic = config.get('nlu.use_semantic_fallback', True)
        
        if use_semantic and self.semantic_classifier and self.semantic_classifier.is_available():
            # Use semantic if rule-based confidence is low or intent is unknown
            if rule_based_confidence < semantic_threshold or rule_based_intent == 'unknown':
                semantic_results = self.semantic_classifier.classify(text, language, top_k=3)
                
                if semantic_results:
                    semantic_intent, semantic_score = semantic_results[0]
                    semantic_weight = config.get('nlu.semantic_weight', 0.8)
                    weighted_semantic_score = semantic_score * semantic_weight
                    
                    # Combine scores: take max of rule-based and weighted semantic
                    if rule_based_intent and rule_based_intent != 'unknown' and rule_based_intent in rule_based_scores:
                        # Both methods have results - combine them
                        rule_score = rule_based_scores.get(rule_based_intent, 0.0)
                        combined_score = max(rule_score, weighted_semantic_score)
                        
                        # If semantic is significantly better, use it
                        if weighted_semantic_score > rule_score * 1.2:
                            return semantic_intent, min(weighted_semantic_score, 0.95)
                        else:
                            return rule_based_intent, min(combined_score, 0.95)
                    else:
                        # Rule-based failed, use semantic
                        return semantic_intent, min(weighted_semantic_score, 0.95)
        
        # Return rule-based result (or unknown if no scores)
        return rule_based_intent, rule_based_confidence
    
    def _has_negation(self, text: str, language: str) -> bool:
        """
        Check if text contains negation
        
        Args:
            text: Input text (should be lowercase)
            language: Detected language
            
        Returns:
            True if negation is detected
        """
        negation_words = {
            'en': ['no', 'not', "don't", "doesn't", "didn't", "won't", "can't", "couldn't", "shouldn't", "wouldn't", "isn't", "aren't", "wasn't", "weren't", 'never', 'nothing', 'nobody'],
            'fi': ['ei', 'en', 'et', 'emme', 'ette', 'eivät', 'ei ole', 'ei ollut', 'ei koskaan'],
            'sv': ['inte', 'ej', 'aldrig', 'ingenting', 'ingen', 'är inte', 'var inte']
        }
        
        words = negation_words.get(language, negation_words['en'])
        return any(word in text for word in words)

