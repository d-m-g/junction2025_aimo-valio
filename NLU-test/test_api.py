"""
Test script for NLU Parser API
Tests various intents, languages, and scenarios
"""

import requests
import json
from datetime import datetime
from typing import Dict, List

# API endpoint
API_URL = "http://localhost:5000/nlu/parse"

# Test cases with expected results
TEST_CASES = [
    {
        "name": "Confirm Substitution (English)",
        "text": "Yes, I'll accept the replacement milk",
        "expected_intent": "confirm_substitution",
        "expected_sentiment": "positive"
    },
    {
        "name": "Confirm Substitution (Vague)",
        "text": "Yes, i agree on this",
        "expected_intent": "confirm_substitution",
        "expected_sentiment": "positive"
    },
    {
        "name": "Reject Substitution",
        "text": "No thanks, I don't want a substitute",
        "expected_intent": "reject_substitution",
        "expected_sentiment": "negative"
    },
    {
        "name": "Request Callback",
        "text": "I need to speak to someone about my missing order",
        "expected_intent": "request_callback",
        "expected_sentiment": "neutral"
    },
    {
        "name": "Report Issue",
        "text": "My delivery is missing 2 items - the milk and bread",
        "expected_intent": "report_issue",
        "expected_sentiment": "negative"
    },
    {
        "name": "Confirm Delivery",
        "text": "Received everything, all good! Thank you",
        "expected_intent": "confirm_delivery",
        "expected_sentiment": "positive"
    },
    {
        "name": "Query Order Status",
        "text": "Where is my order? When will it arrive?",
        "expected_intent": "query_order_status",
        "expected_sentiment": "neutral"
    },
    {
        "name": "Provide Feedback",
        "text": "Great service! I'd like to leave some feedback",
        "expected_intent": "provide_feedback",
        "expected_sentiment": "positive"
    },
    {
        "name": "Finnish - Confirm Substitution",
        "text": "Kyllä, hyväksyn korvauksen",
        "expected_intent": "confirm_substitution",
        "expected_sentiment": "positive"
    },
    {
        "name": "Swedish - Reject Substitution",
        "text": "Nej, jag vill inte ha ersättningen",
        "expected_intent": "reject_substitution",
        "expected_sentiment": "negative"
    },
    {
        "name": "Query Substitution",
        "text": "What replacement did you suggest?",
        "expected_intent": "query_substitution",
        "expected_sentiment": "neutral"
    },
    {
        "name": "Thank You",
        "text": "Thank you very much for your help",
        "expected_intent": "thank_you",
        "expected_sentiment": "positive"
    },
    {
        "name": "Change Delivery",
        "text": "Can I change my delivery time to tomorrow?",
        "expected_intent": "change_delivery",
        "expected_sentiment": "neutral"
    },
    {
        "name": "Cancel Order",
        "text": "I want to cancel my order number 12345",
        "expected_intent": "cancel_order",
        "expected_sentiment": "negative"
    },
    {
        "name": "Query Products",
        "text": "Do you have milk available?",
        "expected_intent": "query_products",
        "expected_sentiment": "neutral"
    },
    {
        "name": "Report Issue with Order Number",
        "text": "Order number 456 is missing 2 items that are damaged",
        "expected_intent": "report_issue",
        "expected_sentiment": "negative"
    },
    {
        "name": "Report Issue with Date",
        "text": "My delivery from yesterday was wrong",
        "expected_intent": "report_issue",
        "expected_sentiment": "negative"
    },
    {
        "name": "Pre-Order: Accept Substitution",
        "text": "Yes, I'll take the replacement",
        "expected_intent": "confirm_substitution",
        "expected_sentiment": "positive",
        "endpoint": "pre-parse",
        "context": {
            "order_number": "10000000",
            "original_product": "Valio Whole Milk 1L",
            "proposed_substitute": "Valio Whole Milk 1.5L"
        }
    },
    {
        "name": "Pre-Order: Reject Substitution",
        "text": "No thanks, I don't want a substitute",
        "expected_intent": "reject_substitution",
        "expected_sentiment": "negative",
        "endpoint": "pre-parse",
        "context": {
            "order_number": "10000000",
            "original_product": "Valio Whole Milk 1L"
        }
    },
    {
        "name": "Post-Delivery: Report Missing Items",
        "text": "I didn't receive the bread from order 10000000 yesterday",
        "expected_intent": "report_issue",
        "expected_sentiment": "negative",
        "endpoint": "post-parse",
        "context": {
            "order_number": "10000000",
            "delivery_date": "2024-09-02",
            "detected_discrepancy": True
        }
    },
    {
        "name": "Post-Delivery: Accept Solution",
        "text": "Yes, please send the replacement",
        "expected_intent": "confirm_substitution",
        "expected_sentiment": "positive",
        "endpoint": "post-parse",
        "context": {
            "order_number": "10000000",
            "proposed_solution": "replacement_delivery"
        }
    }
]


def print_result(test_name: str, response: Dict, expected: Dict):
    """Print formatted test result"""
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"{'='*70}")
    print(f"Input: \"{expected['text']}\"")
    print(f"\nResults:")
    print(f"  Intent: {response.get('intent', 'N/A')} (expected: {expected.get('expected_intent', 'N/A')})")
    print(f"  Confidence: {response.get('confidence', 0):.1%}")
    
    entities = response.get('parameters', {}).get('entities', {})
    sentiment = entities.get('sentiment', {})
    print(f"  Sentiment: {sentiment.get('polarity', 'N/A')} (expected: {expected.get('expected_sentiment', 'N/A')}) "
          f"[confidence: {sentiment.get('confidence', 0):.1%}]")
    print(f"  Language: {entities.get('language', 'N/A')}")
    
    products = entities.get('products', [])
    if products:
        print(f"  Products found: {len(products)}")
        for p in products[:3]:
            print(f"    - {p.get('name', 'Unknown')} (GTIN: {p.get('gtin', 'N/A')})")
    
    quantities = entities.get('quantities', [])
    if quantities:
        qty_strs = [f"{q.get('value')} {q.get('unit')}" for q in quantities[:3]]
        print(f"  Quantities: {', '.join(qty_strs)}")
    
    urgency = entities.get('urgency', {})
    if urgency.get('level') != 'low':
        print(f"  Urgency: {urgency.get('level', 'N/A')} [confidence: {urgency.get('confidence', 0):.1%}]")
    
    # Order numbers
    order_numbers = entities.get('order_numbers', [])
    if order_numbers:
        print(f"  Order Numbers: {', '.join([o.get('value', 'N/A') for o in order_numbers[:3]])}")
    
    # Dates
    dates = entities.get('dates', [])
    if dates:
        print(f"  Dates: {', '.join([d.get('value', 'N/A') for d in dates[:3]])}")
    
    # Reasons
    reasons = entities.get('reasons', [])
    if reasons:
        print(f"  Reasons: {', '.join([r.get('type', 'N/A') for r in reasons[:3]])}")
    
    # Metadata (for pre-parse and post-parse endpoints)
    metadata = response.get('metadata', {})
    if metadata:
        conversation_stage = metadata.get('conversation_stage')
        if conversation_stage:
            print(f"  Conversation Stage: {conversation_stage}")
        priority_entities = metadata.get('priority_entities', [])
        if priority_entities:
            print(f"  Priority Entities: {', '.join(priority_entities)}")
        if metadata.get('missing_order_warning'):
            print(f"  ⚠️  Warning: Missing order number for issue report")
    
    # Check if expectations match
    intent_match = response.get('intent') == expected.get('expected_intent')
    sentiment_match = sentiment.get('polarity') == expected.get('expected_sentiment')
    
    if intent_match and sentiment_match:
        print(f"\n✅ PASS - Intent and sentiment match expectations")
    elif intent_match:
        print(f"\n⚠️  PARTIAL - Intent matches, but sentiment is {sentiment.get('polarity')} (expected {expected.get('expected_sentiment')})")
    elif sentiment_match:
        print(f"\n⚠️  PARTIAL - Sentiment matches, but intent is {response.get('intent')} (expected {expected.get('expected_intent')})")
    else:
        print(f"\n❌ FAIL - Intent: {response.get('intent')} (expected {expected.get('expected_intent')}), "
              f"Sentiment: {sentiment.get('polarity')} (expected {expected.get('expected_sentiment')})")


def run_tests():
    """Run all test cases"""
    print("🧪 NLU Parser API Test Suite")
    print("=" * 70)
    print(f"API Endpoint: {API_URL}")
    print(f"Test Cases: {len(TEST_CASES)}")
    print("=" * 70)
    
    # Check if server is running
    try:
        health_response = requests.get(API_URL.replace('/nlu/parse', '/health'), timeout=2)
        if health_response.status_code == 200:
            print("✅ API server is running\n")
        else:
            print("⚠️  API server health check returned non-200 status\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API server at {API_URL}")
        print(f"   Error: {e}")
        print(f"\n   Make sure the server is running:")
        print(f"   cd NLU && python app.py")
        return
    
    results = {
        'total': len(TEST_CASES),
        'passed': 0,
        'partial': 0,
        'failed': 0,
        'errors': 0
    }
    
    for i, test_case in enumerate(TEST_CASES, 1):
        try:
            # Determine which endpoint to use
            endpoint = test_case.get('endpoint', 'parse')
            if endpoint == 'pre-parse':
                url = API_URL.replace('/nlu/parse', '/nlu/pre-parse')
            elif endpoint == 'post-parse':
                url = API_URL.replace('/nlu/parse', '/nlu/post-parse')
            else:
                url = API_URL
            
            # Make API request
            # Generate valid session_id (replace dots with underscores)
            timestamp = str(datetime.now().timestamp()).replace('.', '_')
            session_id = f'test_{i}_{timestamp}'
            
            # Build request payload
            payload = {
                'text': test_case['text'],
                'session_id': session_id
            }
            
            # Add context if provided
            if 'context' in test_case:
                payload['context'] = test_case['context']
            
            response = requests.post(
                url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print_result(test_case['name'], data, test_case)
                
                # Check results
                intent_match = data.get('intent') == test_case.get('expected_intent')
                sentiment_match = data.get('parameters', {}).get('entities', {}).get('sentiment', {}).get('polarity') == test_case.get('expected_sentiment')
                
                if intent_match and sentiment_match:
                    results['passed'] += 1
                elif intent_match or sentiment_match:
                    results['partial'] += 1
                else:
                    results['failed'] += 1
            else:
                print(f"\n❌ Test {i} failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                results['errors'] += 1
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Test {i} error: {e}")
            results['errors'] += 1
        except Exception as e:
            print(f"\n❌ Test {i} unexpected error: {e}")
            results['errors'] += 1
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}")
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"⚠️  Partial: {results['partial']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"💥 Errors: {results['errors']}")
    print(f"{'='*70}")
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print()


if __name__ == '__main__':
    run_tests()

