# NLU Parser API

Natural Language Understanding (NLU) parser for the Valio Aimo delivery system. Converts text or voice transcripts into structured intents and entities.

## Features

- **Multilingual Support**: Detects and processes English, Finnish, and Swedish
- **Intent Classification**: Identifies 14 different intents including substitution confirmations, issue reports, order queries, and more
- **Entity Extraction**: Extracts products, quantities, order numbers, dates, reasons, sentiment, and urgency from text
- **Voice-to-Text Optimized**: Text normalization handles filler words, contractions, and common transcription errors
- **Hybrid Approach**: Combines rule-based regex patterns with semantic similarity (sentence embeddings) for better generalization
- **Product Catalog Integration**: Matches product mentions against product catalog using GTIN codes and names with fuzzy matching
- **Session Management**: Tracks conversation context for better intent disambiguation
- **Confidence Filtering**: Filters low-confidence results and flags uncertain predictions

## Quick Start

### macOS / Linux

1. **Setup** (first time only):
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Prepare the environment

2. **Run the server**:
   ```bash
   ./run.sh
   ```
   Or manually:
   ```bash
   source venv/bin/activate
   python app.py
   ```

### Windows

1. **Setup** (first time only):
   ```cmd
   setup.bat
   ```
   This will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Prepare the environment

2. **Run the server**:
   ```cmd
   run.bat
   ```
   Or manually:
   ```cmd
   venv\Scripts\activate.bat
   python app.py
   ```

### Manual Installation

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will start on `http://0.0.0.0:5000` (accessible at `http://localhost:5000`)

**Note**: The hybrid approach uses `scikit-learn` for semantic similarity. All dependencies are lightweight and will be installed automatically.

### API Endpoints

#### POST `/nlu/parse`

General-purpose text parsing endpoint. Use for standard NLU parsing without specific conversation context.

#### POST `/nlu/pre-parse`

Parse customer responses during **pre-order substitution conversations** (before picking/delivery).

**When to use:**
- Order is being processed
- Item shortage detected (out of stock)
- System proactively calls customer
- System offers substitute product

**Request Example:**
```json
{
  "text": "Yes, I'll accept the replacement milk",
  "session_id": "session-123",
  "context": {
    "order_number": "10000000",
    "original_product": "Valio Whole Milk 1L",
    "proposed_substitute": "Valio Whole Milk 1.5L"
  }
}
```

**Response includes:**
- `metadata.conversation_stage`: "pre_order_substitution"
- `metadata.priority_entities`: ["products", "quantities"]
- Boosted intent confidence for `confirm_substitution`, `reject_substitution`, `query_substitution`

#### POST `/nlu/post-parse`

Parse customer responses during **post-delivery issue investigation** (after delivery is complete).

**When to use:**
- Delivery is complete
- Customer contacts system saying items are missing/wrong, OR
- System detects discrepancy (delivered_qty < ordered_qty) and proactively calls customer
- System asks clarifying questions and proposes solutions

**Request Example:**
```json
{
  "text": "Yes, I'm missing 2 packs of milk from order 10000000 that was delivered yesterday",
  "session_id": "session-456",
  "context": {
    "order_number": "10000000",
    "delivery_date": "2024-09-02",
    "detected_discrepancy": true,
    "missing_items": ["product_code_123"],
    "proposed_solution": "replacement_delivery"
  }
}
```

**Response includes:**
- `metadata.conversation_stage`: "post_delivery_investigation"
- `metadata.priority_entities`: ["order_numbers", "dates", "reasons", "products"]
- `metadata.missing_order_warning`: true if `report_issue` intent but no order_number found
- Boosted intent confidence for `report_issue`, `confirm_delivery`, `query_order_status`

### General Parse Endpoint

#### POST `/nlu/parse`

Parse text input and extract intent, entities, and metadata.

**Request Body:**
```json
{
  "text": "Yes, I'll accept the replacement milk",
  "context": {
    "order_number": "ORD-12345",
    "customer_id": "CUST-001"
  },
  "session_id": "session-abc123"
}
```

**Response:**
```json
{
  "intent": "confirm_substitution",
  "confidence": 0.85,
  "parameters": {
    "entities": {
      "products": [
        {
          "name": "Valio Whole Milk 1L",
          "gtin": "6410405081234",
          "confidence": 0.8
        }
      ],
      "quantities": [],
      "order_numbers": [],
      "dates": [],
      "reasons": [],
      "sentiment": {
        "polarity": "positive",
        "confidence": 0.6
      },
      "urgency": {
        "level": "low",
        "confidence": 0.3
      },
      "language": "en"
    },
    "language": "en",
    "context": {
      "order_number": "ORD-12345",
      "customer_id": "CUST-001"
    }
  },
  "timestamp": "2025-01-15T10:30:00.000Z",
  "session_id": "session-abc123"
}
```

### Health Check

#### GET `/health`

Returns service health status.

## Supported Intents

- `confirm_substitution` - Accept replacement products
- `reject_substitution` - Decline proposed substitutions
- `request_callback` - Ask for human contact
- `report_issue` - Report delivery problems
- `confirm_delivery` - Confirm successful delivery
- `query_order_status` - Check order status
- `query_substitution` - Ask about proposed substitutions
- `thank_you` - Express gratitude
- `change_delivery` - Request delivery time/location changes
- `cancel_order` - Request order cancellation
- `query_products` - Ask about product availability/info
- `provide_feedback` - Give service feedback
- `greeting` - Initial greeting
- `unknown` - Fallback intent

## Entity Types

- **Products**: Matched against product catalog using GTIN codes and names (with fuzzy matching)
- **Quantities**: Extracted numerical quantities and units (supports spoken numbers)
- **Order Numbers**: Extracted order IDs (e.g., "order #123", "order 456") - voice-to-text aware
- **Dates**: Extracted relative dates (today, yesterday, tomorrow) and specific dates
- **Reasons**: Extracted issue reasons (damaged, missing, wrong, expired, etc.)
- **Sentiment**: Detected positive/negative/neutral tone (using TextBlob + pattern matching)
- **Urgency**: Identified time-sensitive requests (high/medium/low)
- **Language**: Auto-detected input language (en/fi/sv)

## Product Catalog

The system automatically looks for product data at:
- `../Data/Valio Aimo Product Data 2025.json`
- `../data/Valio Aimo Product Data 2025.json`
- `../Valio Aimo Product Data 2025.json`

If no catalog is found, product extraction will be limited but the system will still function.

## Architecture

- `app.py` - Flask API server and endpoint handlers
- `text_normalizer.py` - Text normalization for voice-to-text input (removes filler words, normalizes contractions)
- `language_detector.py` - Language detection using character patterns and common words
- `intent_classifier.py` - Hybrid intent classification (regex patterns + semantic similarity, 14 intents)
- `semantic_intent_classifier.py` - Semantic intent classification using sentence embeddings
- `intent_examples.py` - Example sentences for each intent (used for semantic matching)
- `entity_extractor.py` - Entity extraction (products, quantities, order_numbers, dates, reasons, sentiment, urgency)
- `product_catalog.py` - Product catalog loader and manager with comprehensive name mapping
- `session_manager.py` - Session and conversation context management
- `config.py` - Configuration management
- `validators.py` - Input validation and sanitization
- `errors.py` - Structured error handling

## Example Usage

```python
import requests

response = requests.post('http://localhost:5000/nlu/parse', json={
    'text': 'I need to speak to someone about my missing order',
    'session_id': 'test-123'
})

print(response.json())
# {
#   "intent": "request_callback",
#   "confidence": 0.75,
#   ...
# }
```

## Testing

Test the endpoint with curl:

```bash
curl -X POST http://localhost:5000/nlu/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Yes, I accept the replacement",
    "session_id": "test-123"
  }'
```

## Logging

The service logs all parsing requests and results at INFO level. Logs include:
- Input text (truncated to 100 chars)
- Detected intent and confidence
- Session IDs for tracking

## Future Enhancements

- Machine learning-based intent classification for improved accuracy
- More sophisticated product name matching using embeddings
- Support for additional languages
- Context-aware conversation state management
- Integration with voice transcription services

