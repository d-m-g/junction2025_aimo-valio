Task: Implement NLU Parser API
Overview
Create a POST /nlu/parse endpoint that converts text or voice transcripts into intents and parameters for the Valio Aimo delivery system.

Requirements
Input
text: string (required) - Text input or voice transcript

context: object (optional) - Additional context like order number, customer info

session_id: string (optional) - Session identifier for conversation tracking

Output
intent: string - Detected intent (confirm_substitution, reject_substitution, report_issue, etc.)

confidence: float - Confidence score 0.0-1.0

parameters: object - Extracted entities and metadata

timestamp: string - ISO timestamp

session_id: string - Echoed session ID if provided

Key Features to Implement
Multilingual Support

Detect language (English, Finnish, Swedish)

Language-specific intent patterns

Product name matching in all languages

Intent Classification

confirm_substitution - Accept replacement products

reject_substitution - Decline proposed substitutions

request_callback - Ask for human contact

report_issue - Report delivery problems

confirm_delivery - Confirm successful delivery

query_order_status - Check order status

provide_feedback - Give service feedback

greeting - Initial greeting

unknown - Fallback intent

Entity Extraction

Products: Match against product catalog using GTIN codes and names

Quantities: Extract numerical quantities and units

Sentiment: Detect positive/negative/neutral tone

Urgency: Identify time-sensitive requests

Language: Auto-detect input language

Technical Requirements

Rule-based approach using regex patterns

Product name mappings from provided product data

Context awareness for better parsing

Confidence scoring for all detections

Graceful fallback to 'unknown' intent

Logging for audit purposes

Success Criteria
Handle common customer phrases about delivery issues

Accurately detect substitution confirmations/rejections

Support multiple languages (EN/FI/SV)

Extract product mentions from text

Provide reliable confidence scores

Work with minimal setup and dependencies

