"""
Example test script for NLU parser
Run this to test the NLU functionality without starting the full server
"""

from language_detector import LanguageDetector
from intent_classifier import IntentClassifier
from entity_extractor import EntityExtractor

# Initialize components
language_detector = LanguageDetector()
intent_classifier = IntentClassifier()
entity_extractor = EntityExtractor()

# Test cases
test_cases = [
    {
        "text": "Yes, I'll accept the replacement milk",
        "expected_intent": "confirm_substitution",
        "language": "en"
    },
    {
        "text": "No thanks, I don't want a substitute",
        "expected_intent": "reject_substitution",
        "language": "en"
    },
    {
        "text": "I need to speak to someone about my missing order",
        "expected_intent": "request_callback",
        "language": "en"
    },
    {
        "text": "My delivery is missing 2 items",
        "expected_intent": "report_issue",
        "language": "en"
    },
    {
        "text": "Kyllä, hyväksyn korvauksen",
        "expected_intent": "confirm_substitution",
        "language": "fi"
    },
    {
        "text": "Hej, jag vill ha min beställning",
        "expected_intent": "greeting",
        "language": "sv"
    }
]

print("Testing NLU Parser Components\n" + "=" * 50)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['text']}")
    print("-" * 50)
    
    # Detect language
    detected_lang = language_detector.detect(test['text'])
    print(f"Detected Language: {detected_lang} (expected: {test['language']})")
    
    # Classify intent
    intent, confidence = intent_classifier.classify(test['text'], detected_lang)
    print(f"Intent: {intent} (confidence: {confidence:.2f}, expected: {test['expected_intent']})")
    
    # Extract entities
    entities = entity_extractor.extract(test['text'], detected_lang)
    print(f"Entities:")
    print(f"  - Products: {len(entities['products'])} found")
    print(f"  - Quantities: {entities['quantities']}")
    print(f"  - Sentiment: {entities['sentiment']['polarity']} ({entities['sentiment']['confidence']:.2f})")
    print(f"  - Urgency: {entities['urgency']['level']} ({entities['urgency']['confidence']:.2f})")

print("\n" + "=" * 50)
print("Testing complete!")

