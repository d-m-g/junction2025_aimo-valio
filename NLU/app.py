"""
NLU Parser API for Valio Aimo Delivery System
Provides intent classification and entity extraction from text/voice transcripts
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import config
from errors import InternalError, ParseError, ValidationError, NLUError
from language_detector import LanguageDetector
from intent_classifier import IntentClassifier
from entity_extractor import EntityExtractor
from product_catalog import ProductCatalog
from session_manager import session_manager
from text_normalizer import TextNormalizer
from validators import validate_batch_request, validate_context, validate_session_id, validate_text

# Configure logging
log_level = getattr(logging, config.get('logging.level', 'INFO'))
logging.basicConfig(
    level=log_level,
    format=config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
cors_origins = config.get('cors.origins', '*')
if config.get('cors.enabled', True):
    if cors_origins == '*' or isinstance(cors_origins, str):
        CORS(app)
    else:
        CORS(app, origins=cors_origins)

# Initialize components
text_normalizer = TextNormalizer()
language_detector = LanguageDetector()
intent_classifier = IntentClassifier()
entity_extractor = EntityExtractor()
product_catalog = ProductCatalog()

# Track startup time for health check
_startup_time = time.time()


def apply_confidence_filters(intent: str, confidence: float, entities: Dict) -> Dict:
    """
    Apply confidence filters to filter out low-confidence results
    
    Args:
        intent: Detected intent
        confidence: Intent confidence
        entities: Extracted entities
        
    Returns:
        Filtered entities with uncertainty flag
    """
    min_intent_confidence = config.get('confidence.min_intent_confidence', 0.3)
    min_entity_confidence = config.get('confidence.min_entity_confidence', 0.4)
    uncertain_threshold = config.get('confidence.uncertain_threshold', 0.6)
    
    # Filter products by confidence
    if 'products' in entities:
        entities['products'] = [
            p for p in entities['products']
            if p.get('confidence', 0) >= min_entity_confidence
        ]
    
    # Filter quantities by confidence
    if 'quantities' in entities:
        entities['quantities'] = [
            q for q in entities['quantities']
            if q.get('confidence', 0) >= min_entity_confidence
        ]
    
    # Add uncertainty flag
    uncertain = confidence < uncertain_threshold
    
    return {
        'entities': entities,
        'uncertain': uncertain,
        'confidence_below_threshold': confidence < min_intent_confidence
    }


def parse_single_text(text: str, context: Optional[Dict] = None, session_id: Optional[str] = None) -> Dict:
    """
    Parse a single text input
    
    Args:
        text: Input text
        context: Optional context
        session_id: Optional session ID
        
    Returns:
        Parsed result dictionary
    """
    start_time = time.time()
    
    # Normalize text (handle voice-to-text characteristics)
    # First detect language on original text, then normalize
    detected_language = language_detector.detect(text)
    normalized_text = text_normalizer.normalize(text, detected_language)
    
    # Get session context if available
    session_context = {}
    if session_id:
        session_context = session_manager.get_context(session_id)
        # Merge with provided context
        if context:
            context = {**session_context, **context}
        else:
            context = session_context
    
    # Use normalized text for parsing
    text = normalized_text
    
    # Classify intent
    intent, intent_confidence = intent_classifier.classify(text, detected_language, context)
    
    # Extract entities (pass detected intent for context-aware sentiment)
    entities = entity_extractor.extract(text, detected_language, context, detected_intent=intent)
    
    # Apply confidence filters
    filtered = apply_confidence_filters(intent, intent_confidence, entities)
    
    # Build response
    response = {
        'intent': intent,
        'confidence': intent_confidence,
        'parameters': {
            'entities': filtered['entities'],
            'language': detected_language,
            'context': context or {}
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'session_id': session_id,
        'uncertain': filtered['uncertain'],
        'processing_time_ms': int((time.time() - start_time) * 1000)
    }
    
    # Add to session history
    if session_id:
        session_manager.add_to_history(session_id, intent, text, filtered['entities'])
    
    logger.info(
        f"Parsed intent: {intent} (confidence: {intent_confidence:.2f}, "
        f"time: {response['processing_time_ms']}ms, session: {session_id})"
    )
    
    return response


def parse_pre_order(text: str, context: Optional[Dict] = None, session_id: Optional[str] = None) -> Dict:
    """
    Parse customer responses during pre-order substitution conversations
    
    Args:
        text: Input text
        context: Optional context (should include order_number, original_product, proposed_substitute)
        session_id: Optional session ID
        
    Returns:
        Parsed result dictionary with pre-order metadata
    """
    # Ensure conversation_stage is set
    if context is None:
        context = {}
    context = context.copy()
    context['conversation_stage'] = 'pre_order_substitution'
    
    # Parse using base function
    response = parse_single_text(text, context, session_id)
    
    # Add pre-order specific metadata
    response['metadata'] = {
        'conversation_stage': 'pre_order_substitution',
        'context_used': bool(context.get('proposed_substitute') or context.get('original_product')),
        'priority_entities': ['products', 'quantities']
    }
    
    # Boost order_number extraction if context has it
    if context.get('order_number') and not response['parameters']['entities'].get('order_numbers'):
        # Try to extract order number from context
        response['parameters']['entities']['order_numbers'] = [{
            'value': str(context['order_number']),
            'confidence': 0.9,
            'source': 'context'
        }]
    
    return response


def parse_post_delivery(text: str, context: Optional[Dict] = None, session_id: Optional[str] = None) -> Dict:
    """
    Parse customer responses during post-delivery issue investigation
    
    Args:
        text: Input text
        context: Optional context (should include order_number, delivery_date, detected_discrepancy, etc.)
        session_id: Optional session ID
        
    Returns:
        Parsed result dictionary with post-delivery metadata
    """
    # Ensure conversation_stage is set
    if context is None:
        context = {}
    context = context.copy()
    context['conversation_stage'] = 'post_delivery_investigation'
    
    # Parse using base function with priority entities
    start_time = time.time()
    
    # Normalize text
    detected_language = language_detector.detect(text)
    normalized_text = text_normalizer.normalize(text, detected_language)
    
    # Get session context if available
    session_context = {}
    if session_id:
        session_context = session_manager.get_context(session_id)
        if context:
            context = {**session_context, **context}
        else:
            context = session_context
    
    text = normalized_text
    
    # Classify intent
    intent, intent_confidence = intent_classifier.classify(text, detected_language, context)
    
    # Extract entities with priority for post-delivery (pass detected intent for context-aware sentiment)
    priority_entities = ['order_numbers', 'dates', 'reasons', 'products']
    entities = entity_extractor.extract(text, detected_language, context, priority_entities=priority_entities, detected_intent=intent)
    
    # Apply confidence filters
    filtered = apply_confidence_filters(intent, intent_confidence, entities)
    
    # Boost order_number from context if not extracted
    if context.get('order_number') and not filtered['entities'].get('order_numbers'):
        filtered['entities']['order_numbers'] = [{
            'value': str(context['order_number']),
            'confidence': 0.95,
            'source': 'context'
        }]
    
    # Flag if order_number is missing for issue reports
    missing_order_warning = False
    if intent == 'report_issue' and not filtered['entities'].get('order_numbers'):
        missing_order_warning = True
    
    # Build response
    response = {
        'intent': intent,
        'confidence': intent_confidence,
        'parameters': {
            'entities': filtered['entities'],
            'language': detected_language,
            'context': context or {}
        },
        'metadata': {
            'conversation_stage': 'post_delivery_investigation',
            'context_used': bool(context.get('order_number') or context.get('detected_discrepancy')),
            'priority_entities': priority_entities,
            'missing_order_warning': missing_order_warning
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'session_id': session_id,
        'uncertain': filtered['uncertain'],
        'processing_time_ms': int((time.time() - start_time) * 1000)
    }
    
    # Add to session history
    if session_id:
        session_manager.add_to_history(session_id, intent, text, filtered['entities'])
    
    logger.info(
        f"Post-delivery parsed intent: {intent} (confidence: {intent_confidence:.2f}, "
        f"time: {response['processing_time_ms']}ms, session: {session_id})"
    )
    
    return response


@app.errorhandler(NLUError)
def handle_nlu_error(error: NLUError):
    """Handle NLU errors"""
    logger.warning(f"NLU Error: {error.error_code} - {error.message}")
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(Exception)
def handle_generic_error(e: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    error = InternalError("An unexpected error occurred", details={'type': type(e).__name__})
    return jsonify(error.to_dict()), error.status_code


@app.route('/', methods=['GET'])
def root():
    """Provide a simple landing response for the service root."""
    return jsonify({
        'service': 'nlu-parser',
        'message': 'NLU Parser API is running. Try /health or POST /nlu/parse.',
        'routes': ['/health', '/nlu/parse', '/nlu/pre-parse', '/nlu/post-parse', '/nlu/parse/batch']
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Enhanced health check endpoint"""
    try:
        # Check components
        catalog_loaded = len(product_catalog.get_catalog()) > 0
        
        health_data = {
            'status': 'healthy',
            'service': 'nlu-parser',
            'version': '1.0.0',
            'uptime_seconds': int(time.time() - _startup_time),
            'components': {
                'language_detector': True,
                'intent_classifier': True,
                'entity_extractor': True,
                'product_catalog': catalog_loaded,
                'product_count': len(product_catalog.get_catalog()),
                'semantic_classifier': intent_classifier.semantic_classifier.is_available() if hasattr(intent_classifier, 'semantic_classifier') and intent_classifier.semantic_classifier else False
            },
            'config': {
                'session_enabled': config.get('session.enabled', True),
                'fuzzy_matching_available': hasattr(entity_extractor, 'fuzzy_threshold')
            }
        }
        
        # Determine overall health
        all_healthy = all([
            health_data['components']['language_detector'],
            health_data['components']['intent_classifier'],
            health_data['components']['entity_extractor']
        ])
        
        status_code = 200 if all_healthy else 503
        health_data['status'] = 'healthy' if all_healthy else 'degraded'
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/nlu/parse', methods=['POST'])
def parse():
    """
    Parse text input and extract intent, entities, and metadata
    
    Request body:
    {
        "text": "string (required)",
        "context": {"order_number": "...", "customer_id": "..."} (optional),
        "session_id": "string" (optional)
    }
    
    Response:
    {
        "intent": "string",
        "confidence": float,
        "parameters": {...},
        "timestamp": "ISO string",
        "session_id": "string",
        "uncertain": bool,
        "processing_time_ms": int
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")
        
        # Validate text
        text, error = validate_text(data.get('text'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate context
        context, error = validate_context(data.get('context'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate session_id
        session_id, error = validate_session_id(data.get('session_id'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Parse text
        response = parse_single_text(text, context, session_id)
        
        return jsonify(response), 200
        
    except ValidationError as e:
        raise  # Will be handled by error handler
    except Exception as e:
        logger.error(f"Error parsing text: {str(e)}", exc_info=True)
        raise InternalError("Failed to parse text", details={'error': str(e)})


@app.route('/nlu/pre-parse', methods=['POST'])
def pre_parse():
    """
    Parse customer responses during pre-order substitution conversations
    
    Use this endpoint when:
    - Order is being processed
    - Item shortage detected (out of stock)
    - System proactively calls customer
    - System offers substitute product
    
    Request body:
    {
        "text": "string (required)",
        "context": {
            "order_number": "string (optional)",
            "original_product": "string (optional)",
            "proposed_substitute": "string (optional)",
            "conversation_stage": "pre_order_substitution" (optional, auto-set)
        },
        "session_id": "string" (optional)
    }
    
    Response includes metadata with conversation_stage and priority_entities
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")
        
        # Validate text
        text, error = validate_text(data.get('text'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate context
        context, error = validate_context(data.get('context'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate session_id
        session_id, error = validate_session_id(data.get('session_id'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Parse text with pre-order context
        response = parse_pre_order(text, context, session_id)
        
        return jsonify(response), 200
        
    except ValidationError as e:
        raise  # Will be handled by error handler
    except Exception as e:
        logger.error(f"Error parsing pre-order text: {str(e)}", exc_info=True)
        raise InternalError("Failed to parse pre-order text", details={'error': str(e)})


@app.route('/nlu/post-parse', methods=['POST'])
def post_parse():
    """
    Parse customer responses during post-delivery issue investigation
    
    Use this endpoint when:
    - Delivery is complete
    - Customer contacts system saying items are missing/wrong, OR
    - System detects discrepancy (delivered_qty < ordered_qty) and proactively calls customer
    - System asks clarifying questions and proposes solutions
    
    Request body:
    {
        "text": "string (required)",
        "context": {
            "order_number": "string (optional)",
            "delivery_date": "string (optional)",
            "detected_discrepancy": bool (optional),
            "missing_items": ["product_code"] (optional),
            "proposed_solution": "string (optional)",
            "conversation_stage": "post_delivery_investigation" (optional, auto-set)
        },
        "session_id": "string" (optional)
    }
    
    Response includes metadata with conversation_stage, priority_entities, and missing_order_warning
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")
        
        # Validate text
        text, error = validate_text(data.get('text'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate context
        context, error = validate_context(data.get('context'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate session_id
        session_id, error = validate_session_id(data.get('session_id'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Parse text with post-delivery context
        response = parse_post_delivery(text, context, session_id)
        
        return jsonify(response), 200
        
    except ValidationError as e:
        raise  # Will be handled by error handler
    except Exception as e:
        logger.error(f"Error parsing post-delivery text: {str(e)}", exc_info=True)
        raise InternalError("Failed to parse post-delivery text", details={'error': str(e)})


@app.route('/nlu/parse/batch', methods=['POST'])
def parse_batch():
    """
    Parse multiple texts in a single request
    
    Request body:
    {
        "texts": ["text1", "text2", ...] (required, max 100),
        "context": {...} (optional, applied to all),
        "session_id": "string" (optional)
    }
    
    Response:
    {
        "results": [
            {
                "intent": "string",
                "confidence": float,
                ...
            },
            ...
        ],
        "count": int,
        "processing_time_ms": int
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required", "MISSING_BODY")
        
        # Validate texts
        texts, error = validate_batch_request(data.get('texts', []))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate context (applied to all)
        context, error = validate_context(data.get('context'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Validate session_id
        session_id, error = validate_session_id(data.get('session_id'))
        if error:
            raise ValidationError(error.message, error.error_code)
        
        # Parse all texts
        start_time = time.time()
        results = []
        for text in texts:
            try:
                result = parse_single_text(text, context, session_id)
                results.append(result)
            except Exception as e:
                # Add error result instead of failing entire batch
                results.append({
                    'error': str(e),
                    'text': text[:100],
                    'intent': 'unknown',
                    'confidence': 0.0
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = {
            'results': results,
            'count': len(results),
            'processing_time_ms': processing_time
        }
        
        return jsonify(response), 200
        
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Error parsing batch: {str(e)}", exc_info=True)
        raise InternalError("Failed to parse batch", details={'error': str(e)})


@app.route('/nlu/session/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """Get session information"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                'error': 'SESSION_NOT_FOUND',
                'message': 'Session not found or expired'
            }), 404
        
        return jsonify({
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'interaction_count': len(session.get('history', [])),
            'history': list(session.get('history', []))[-5:],  # Last 5 interactions
            'context': session.get('context', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise InternalError("Failed to get session", details={'error': str(e)})


@app.route('/nlu/session/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete a session"""
    try:
        # Session manager doesn't have explicit delete, but we can clear it
        # by letting it expire naturally, or we can add delete method
        return jsonify({
            'message': 'Session will expire naturally based on TTL'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise InternalError("Failed to delete session", details={'error': str(e)})


if __name__ == '__main__':
    host = config.get('api.host', '0.0.0.0')
    port = config.get('api.port', 6060)
    debug = config.get('api.debug', False)
    
    logger.info(f"Starting NLU Parser API on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
