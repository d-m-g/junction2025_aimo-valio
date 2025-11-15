# Substitution Service — MVP Description

## Goal

When an item in an order is unavailable, the substitution service suggests good, data‑driven replacement products that are actually used in practice, instead of random manual guesses.

---

## What it does

**Input:**
- Original product SKU that is short or out of stock
- Optional: order context (customer, quantities)
- Optional: warehouse inventory snapshot (JSON) to constrain suggestions to in‑stock items at the site fulfilling the order

**Output:**
- Top N recommended replacement SKUs
- Scores and basic info about each suggestion

**Example response:**

```json
{
  "sku": "ORIG_123",
  "recommendations": [
    { "sku": "REPL_001", "score": 0.91 },
    { "sku": "REPL_007", "score": 0.84 },
    { "sku": "REPL_015", "score": 0.72 }
  ]
}
```

This API is called by n8n when the prediction service says an item will be missing. The same endpoint can be used both for proactive calls (before delivery) and for post‑delivery remediation.

---

## Data used

For the MVP we stay in classic ML world, no external LLMs:

1. Replacement orders CSV  
   - Real historical pairs of `original product -> replacement product`  
   - Ground truth of which substitutions humans actually used

2. Sales and deliveries CSV  
   - Product‑level stats like: how often each SKU is ordered, average quantities, any available category/group/supplier fields  
   - These become features for the model

3. Optional lightweight text features (if product names are available)  
   - Product name per SKU  
   - TF‑IDF based similarity on names  
   - No LLMs, just classic NLP

---

## How it works

1. Build substitution pairs from history  
   - From replacement orders take every `(original_sku, replacement_sku)` as a positive example  
   - For each original SKU sample other SKUs not used as replacements as negative examples  
   - Produces dataset of pairs `(original, candidate, label)` where label 1 = chosen, 0 = not chosen

2. Engineer features for each pair  
   For each `(original, candidate)` compute features such as:
   - Same category flag
   - Same supplier flag
   - Difference in price or average ordered quantity
   - Popularity of candidate SKU
   - Name similarity based on TF‑IDF (if names exist)
   - All numeric features describing candidate suitability as a replacement

3. Train a simple ML model  
   - Use a standard scikit‑learn classifier (RandomForest or GradientBoosting) to predict probability that a candidate would be chosen as replacement for the original  
   - Trained purely on Valio Aimo data  
   - Evaluate with Hit@k: how often the historically chosen replacement appears in top‑1/top‑3

4. Serve recommendations via a small API  
   - Trained model and feature data loaded into a FastAPI service  
   - Endpoint `POST /recommend` accepts `{ "sku": "...", "k": 3 }`  
   - Service generates candidate pool (e.g., all SKUs in same category), applies warehouse availability filters when provided, scores with model, returns top‑k

---

## Model choice and MVP feature set (from data exploration)

**Model (MVP):** GradientBoostingClassifier or RandomForestClassifier (scikit‑learn), trained on pairwise examples `(original_sku, candidate_sku) → label`. Calibrate probabilities if needed for ranking stability.

**Primary features (catalog-driven, from product JSON):**
- Category match: `original.category == candidate.category` (boolean)
- Temperature proximity: absolute difference of `temperatureCondition` (bucketed 0, 1–3, >3)
- Brand/vendor match: `brand` and/or `vendorName` equality flags
- Pack/size ratio: ratio of key size fields (prefer `unitConversions.sizeInBaseUnits` at matching `unitId`; fallback to `allowedLotSize`)
- Allergen/diet compatibility: overlap and contradictions between `classifications.allergen/nonAllergen` and `nutritionalClaim` (penalize conflicts, reward compatibility)
- Name similarity: TF‑IDF similarity using multilingual `synkkaData.names[*].value` (concatenate available languages)

Notes:
- Use sales unit IDs (e.g., `ST`, `KI`, `RAS`, `SK`) to align size comparisons when present in both products’ `units.unitId`.
- If a mapping from transactional `product_code` to catalog GTIN is partially missing, degrade gracefully by using only features available for both sides (skip size/allergen/brand features if not joinable).

**Behavioral features (from replacement order history):**
- Candidate popularity as a replacement: count/fraction of times candidate chosen overall
- Conditional popularity: frequency candidate chosen for this original’s category
- Recency weighting: emphasize recent replacements (time‑decayed counts, if timestamps available)

**Operational features (optional MVP if joinable with sales/deliveries):**
- Candidate fill‑rate proxy: recent delivered_qty/order_qty ratio by candidate
- Supplier reliability proxy: if supplier/vendor grouping is available, recent shortage rate by supplier

**Ranking:**
- Score each candidate with the classifier’s probability of being chosen; return top‑k.
- Tie‑break by higher name similarity and higher candidate popularity.
- Apply a hard filter for availability: only candidates with available stock in the provided warehouse snapshot are considered (when the snapshot is supplied).

**Evaluation:**
- Hit@1 / Hit@3 on a held‑out slice of historical replacement pairs
- MAP@k (optional), and calibration check (reliability curve) for ranking stability

---

## How it connects to the rest of the system

- Prediction service flags an item as likely missing  
- n8n calls the substitution service with the original SKU and, when possible, the warehouse inventory snapshot for the fulfillment site  
- Substitution service returns a ranked list of replacements  
- These replacements are used by the AI agent in phone/SMS: “We suggest X instead of Y, do you accept?”

Later, the same service can be used in the ecommerce frontend to show “similar items” when something is not available.

---

## Why this MVP is strong

- Fully learned from Valio Aimo history — reflects real human decisions rather than arbitrary rules  
- Simple to deploy — one Python service, one model, one HTTP endpoint  
- Good enough for demo — clearly shows the AI is trained on real replacement behavior, not random similarity

---

## Limitations and obvious next steps

**MVP limitations:**
- Uses only structured data and simple text
- Does not yet understand deep recipe compatibility and niche constraints
- No multilingual reasoning in the model itself yet

**Next steps:**
- Incorporate richer product attributes from JSON (allergens, dietary flags, temperature class) as features
- Replace/augment TF‑IDF with embedding‑based similarity once Featherless or another embedding provider is added
- Add customer segment context: “this customer usually accepts house brand” or “prefers lactose free”
- Add integration with live warehouse/inventory API and enforce availability‑only substitutions by site and cutoff times

---

This description fits a tech spec, Confluence page, or a dedicated slide titled “Substitution Service MVP.”

