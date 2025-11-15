# MVP Plan for Valio Aimo Delivery Reliability AI Solution

## Introduction

Valio Aimo aims to reinvent delivery reliability using predictive AI and multilingual, automated customer care (voice-first, text-second). The goal is to proactively handle missing or out-of-stock items in orders before they impact the customer, thereby improving customer satisfaction and saving significant operational effort.

This MVP focuses on two key AI capabilities—predictive inventory risk modeling and automated customer communication—integrated into a cohesive workflow. Given a tight 36-hour development window, we will implement core features first in English (with a design ready for multilingual expansion) and outline enhancements for future development.

## Solution Overview and Key Components

Our solution consists of components that work together to predict issues and engage customers in real time:

### 1) Out-of-Stock Prediction Model

We will develop a predictive model that evaluates each order line for its likelihood of being out-of-stock or short-supplied before or during picking. This model uses features such as historical supplier reliability, product seasonality, recent quality incidents, current stock levels, and timing (e.g., picking time windows). Trained on order, stock, and supplier datasets, the model outputs a probability or score per item indicating risk of shortage. High-risk items trigger proactive handling.

For the MVP, we’ll likely use a straightforward machine learning model (e.g., Random Forest or XGBoost) for quick turnaround, given the limited time.

### 2) Replacement Recommendation Engine

When a potential or actual shortage is identified, the system suggests optimal substitute products (good–better–best). This module leverages product data to find suitable alternatives—e.g., same category or similar usage (if Milk 1L is out, suggest the same milk of a different brand or a larger pack). We also apply business rules (e.g., allergen/dietary compatibility, recipe suitability).

For the MVP, we may start with simple text similarity and category matching, with the design allowing more sophisticated NLP/embedding models (e.g., via Featherless.ai) later. Substitutions should prefer in-stock options.

### 3) Automated Customer Communication (Voice-First Agent)

An AI voice agent proactively contacts the customer in their preferred language when a shortage is confirmed (or predicted during picking). It notifies about the unavailable item, presents recommended substitutes, and collects the customer’s decision (accept, choose different, or cancel). Voice is prioritized for immediacy; SMS/text acts as backup.

For the MVP, we integrate a voice AI system using n8n + Twilio. The AI agent can be an Ultravox-style voice bot or a custom Python+LLM service. Twilio connects the call and streams audio for two-way conversation (STT/NLP/TTS). If full conversational AI is too complex, we use a simpler IVR interaction (e.g., “Press 1 to accept the suggested replacement or 2 to decline”) via TwiML. All interactions and decisions are logged.

### 4) Post-Delivery Remediation Workflow

If a shortage is discovered after delivery, the system automatically initiates outreach (apology + corrective delivery offer). Triggered after each delivery by comparing ordered vs delivered quantities, the workflow (via n8n) can send a templated SMS or email to inform the customer a replacement order will be scheduled, or optionally place a call. This turns a negative surprise into proactive service recovery.

### 5) Multimodal Claim Handling (Images/Video) – Future Enhancement

Future versions can incorporate image/video analysis for discrepancy claims. Customers or drivers could upload a photo of delivered crates; a vision model checks for missing items (e.g., counting products or recognizing SKUs). While challenging within 36 hours due to data needs, we will keep the architecture open for a proof-of-concept using pre-trained detectors where feasible.

### 6) Tech Stack and Integration

- Models & Logic: Python (pandas, scikit-learn or similar; optional lightweight Flask app for Twilio webhooks or custom logic). Featherless.ai’s serverless AI platform can host ML/NLP components for scale.
- Workflow Orchestration: n8n as the central workflow engine (data triggers, model predictions, communications). Scheduled runs and branching logic for calls/SMS/emails.
- External Services:
  - Twilio: outbound calls and SMS. Use a Twilio number for the demo. TwiML for IVR if needed.
  - Ultravox or LLM-based Voice Agent: configure an agent with a suitable system prompt and connect via API (Ultravox template) or custom Python backend.
- Data Inputs: load CSVs/JSON into in-memory dataframes or a small database.
- Language: MVP interactions in English; architecture supports easy i18n.

## Data Files Used (repo)

- `Data/Valio Aimo Product Data 2025.json`
- `Data/Valio Aimo Sales Deliveries 2025.csv`
- `Data/Valio Aimo Replacement Orders 2025.csv`
- `Data/Valio Aimo Purchases 2025.csv`

## MVP Implementation Plan (36-Hour To-Do List)

### 1) Data Understanding and Feature Engineering (4–6 hours)

- Load sales orders and deliveries; analyze shortages (delivered_qty < ordered).
- Identify patterns (by product, supplier, day-of-week, etc.) predictive of stockouts.
- Load purchase orders to see supply patterns (lead times, partial deliveries) and join with sales for features (e.g., upcoming purchase delays).
- Prepare features per order line: product ID, customer ID/segment, order day/time, delivery day, supplier ID, historical fill rate (product/supplier), stock-on-hand vs ordered quantity, etc.
- Create binary target flag (shortage yes/no) from delivered quantities.
- If time allows, incorporate exception/quality logs and supplier delivery history.

### 2) Train Out-of-Stock Prediction Model (≈4 hours)

- Choose a simple approach (gradient-boosted trees or random forest). Train on historical order lines (older months), test on recent months. Validate accuracy.
- Rule-based fallback if needed: e.g., flag high risk if stock < ordered, or supplier 4-week fill rate < threshold.
- Save the model and provide a scoring function for real-time use. For demo, simulate “new orders” with chosen examples.

### 3) Build Substitution Recommendation Logic (3–4 hours)

- Parse the product JSON into a structured catalog. Group by category and similar attributes; ge
nerate a mapping `{product → [sub1, sub2, sub3]}`.
- Implement a function to get top-N substitutes via text similarity (name/description) and category; filter by availability likelihood (based on stock/purchases).
- Test with examples (e.g., “Valio whole milk 1L” → similar milk substitute). Prepare reusable suggestion sentences for the agent/messages.

### 4) Set Up Customer Contact Workflows (6–8 hours)

- Voice Call Workflow in n8n:
  - Trigger: manual for demo or JSON input representing a flagged order.
  - Node: initiate outbound call via Twilio to a demo phone.
  - Connect to AI agent (Ultravox template or custom LLM backend). If IVR fallback, use TwiML with `<Gather>` to collect keypad input.
  - Script: “Hello, this is Valio Aimo. We’re calling about your order [order ID]—one item, [Product Name], is not available. We recommend [Substitute Name] as a replacement. Would you like this substitute?” Handle yes/no (AI or keypad).
  - No-answer handling: fall back to SMS with summary and replace option.
  - Log outcomes (accepted/rejected/needs follow-up).
- SMS/Text Backup: Twilio template message, e.g., “Valio Aimo: One item in your order is out of stock. Suggested replacement: [Product B]. Reply YES to accept or NO to skip.” (Reply parsing optional for MVP.)
- Post-Delivery Follow-up: Trigger after delivery completion for missed items; send templated apology and corrective plan via SMS/email.

### 5) Integration and Flow Testing (≈4 hours)

- Integrate prediction model and substitution logic into the n8n workflow (code node invoking model + recommender; branch to communications).
- Test scenarios:
  - Scenario 1: Predicted shortage before delivery; customer accepts substitute; confirm change.
  - Scenario 2: Last-minute shortage during picking; handle via later call or SMS.
  - Scenario 3: Post-delivery issue; trigger follow-up message and remediation.
- Debug workflow, credentials, timing, and branching issues.

### 6) Demo Preparation (2–3 hours)

- Prepare a short presentation highlighting:
  - Feasibility: realistic architecture using off-the-shelf components.
  - AI & CX quality: smooth call flow and instant confirmation.
  - Operational impact: manual work saved by proactive swaps. Calculate saved costs estimate(!!project assessment requirement!!)
  - Completeness: coverage across pre-picking, during-picking, and post-delivery.
- Record or live-demo an AI call on speaker.
- Show backend view: n8n workflow, model outputs (e.g., “Item X: 90% stockout risk”), and selected substitute.
- Emphasize 36-hour build and roadmap to production (advanced models, OMS integration, multilingual voice, image recognition).

## Future Considerations

- Multilingual Support: Extend voice/text to Finnish and other languages using multilingual NLP or translation. Keep dialogue content separate from logic for easy localization.
- Stronger AI Models: Improve prediction accuracy with real-time inventory, weather/seasonal events, etc. Refine substitution with learning-to-rank from customer choices. Consider routing/slot optimization for re-deliveries.
- Image/Video Claims Automation: Integrate computer vision for verifying deliveries (customer/driver photo uploads; AI compares expected vs actual).
- Robust Voice AI and Logging: Advanced intent handling, graceful fallbacks, escalation to humans, and comprehensive call/message logging for analytics and continuous improvement (privacy-aware).

## Sources

- Annmaria Philip, “Predicting Out-of-Stock Items with DeepAR: A Comprehensive Guide.”
- n8n Workflow Template, “Automated Outbound Calls: Ultravox AI Agents with Twilio.”
- ParallelDots Blog, “Retail Image Recognition for Out-of-Stock Detection.”


