"""
Simple Out-of-Stock Prediction API
Uses random heuristics to predict stock availability

Install: pip install fastapi uvicorn pydantic
Run: uvicorn main:app --reload
Test: curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @order.json
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import hashlib

app = FastAPI(
    title="Stock Availability Predictor",
    description="Heuristic-based stock availability prediction",
    version="1.0.0"
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CustomerContact(BaseModel):
    phone: str
    email: str
    language: str


class OrderItem(BaseModel):
    line_id: int
    product_code: str
    name: str
    qty: float
    unit: str


class OrderRequest(BaseModel):
    order_id: str
    customer_id: str
    created_at: str
    delivery_date: str
    customer_contact: CustomerContact
    items: List[OrderItem]


class ItemPrediction(BaseModel):
    line_id: int
    product_code: str
    name: str
    qty: float
    in_stock: bool
    probability: float
    risk_level: str


class PredictionResponse(BaseModel):
    order_id: str
    prediction: bool  # True if ALL items available
    items: List[ItemPrediction]
    overall_probability: float
    timestamp: str


# ============================================================================
# HEURISTIC LOGIC
# ============================================================================

def calculate_stock_probability(product_code: str, qty: float, unit: str, delivery_date: str) -> float:
    """
    Calculate probability that item is in stock using heuristics.
    Uses deterministic randomness based on product code for consistency.
    
    Args:
        product_code: Product code
        qty: Order quantity
        unit: Unit type
        delivery_date: Delivery date
        
    Returns:
        Probability between 0.0 and 1.0
    """
    # Use product code as seed for deterministic randomness
    seed_value = int(hashlib.md5(product_code.encode()).hexdigest()[:8], 16)
    random.seed(seed_value)
    
    # Base probability (70-95% for most products)
    base_probability = random.uniform(0.70, 0.95)
    
    # INCREASED quantity penalty - larger orders are MUCH riskier
    if qty > 50:
        # Very large orders: -30% to -50% penalty
        quantity_penalty = min(0.50, 0.30 + (qty - 50) * 0.02)
        base_probability -= quantity_penalty
    elif qty > 20:
        # Large orders: -15% to -30% penalty
        quantity_penalty = min(0.30, 0.15 + (qty - 20) * 0.005)
        base_probability -= quantity_penalty
    elif qty > 10:
        # Medium orders: -5% to -15% penalty
        quantity_penalty = min(0.15, (qty - 10) * 0.01)
        base_probability -= quantity_penalty
    # Small orders (qty <= 10): no penalty
    
    # Adjust for unit type (some units harder to stock)
    unit_adjustments = {
        'ST': 0.0,      # Standard
        'BOT': -0.05,   # Bottles slightly riskier
        'KG': -0.03,    # Weight-based slightly riskier
        'CS': -0.08,    # Cases more complex
        'PAK': -0.06,   # Packages
    }
    base_probability += unit_adjustments.get(unit, -0.02)
    
    # Parse delivery date and check urgency
    try:
        delivery = datetime.fromisoformat(delivery_date.replace('Z', '+00:00'))
        now = datetime.now(delivery.tzinfo)
        days_until = (delivery - now).days
        
        # Rush orders (< 2 days) are riskier
        if days_until < 2:
            base_probability -= 0.10
        elif days_until > 7:
            # Plenty of time = slightly better odds
            base_probability += 0.05
    except:
        pass  # If date parsing fails, use base probability
    
    # Add some random variation (±5%)
    random.seed(seed_value + int(qty))
    variation = random.uniform(-0.05, 0.05)
    base_probability += variation
    
    # Clamp to valid range
    return max(0.01, min(0.99, base_probability))


def get_risk_level(probability: float) -> str:
    """Convert probability to risk level."""
    if probability >= 0.70:
        return "LOW"
    elif probability >= 0.40:
        return "MEDIUM"
    else:
        return "HIGH"


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "service": "Stock Availability Predictor",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "predict": "POST /predict - Returns {prediction: true/false}",
            "predict_detailed": "POST /predict/detailed - Returns full details",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health_check():
    """Health check for monitoring."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/predict")
def predict_stock_availability(order: OrderRequest):
    """
    Predict stock availability for an order.
    
    Returns:
        {"prediction": true/false, "items": [...]}
    """
    try:
        item_predictions = []
        probabilities = []
        
        # Process each item
        for item in order.items:
            probability = calculate_stock_probability(
                product_code=item.product_code,
                qty=item.qty,
                unit=item.unit,
                delivery_date=order.delivery_date
            )
            
            in_stock = probability >= 0.50  # 50% threshold
            risk_level = get_risk_level(probability)
            
            item_predictions.append({
                "product_code": item.product_code,
                "name": item.name,
                "qty": item.qty,
                "risk_level": risk_level
            })
            
            probabilities.append(probability)
        
        # Overall prediction: ALL items must have >= 50% probability
        overall_prediction = all(p >= 0.50 for p in probabilities)
        
        return {
            "prediction": overall_prediction,
            "items": item_predictions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/detailed", response_model=PredictionResponse)
def predict_detailed(order: OrderRequest):
    """
    Detailed prediction with per-item breakdown.
    
    Returns full prediction details including probabilities and risk levels.
    """
    try:
        item_predictions = []
        probabilities = []
        
        # Process each item
        for item in order.items:
            probability = calculate_stock_probability(
                product_code=item.product_code,
                qty=item.qty,
                unit=item.unit,
                delivery_date=order.delivery_date
            )
            
            in_stock = probability >= 0.50  # 50% threshold
            risk_level = get_risk_level(probability)
            
            item_predictions.append(ItemPrediction(
                line_id=item.line_id,
                product_code=item.product_code,
                name=item.name,
                qty=item.qty,
                in_stock=in_stock,
                probability=round(probability, 4),
                risk_level=risk_level
            ))
            
            probabilities.append(probability)
        
        # Overall prediction: ALL items must be in stock
        overall_prediction = all(p.in_stock for p in item_predictions)
        
        # Overall probability: minimum of all items (weakest link)
        overall_probability = min(probabilities) if probabilities else 0.0
        
        return PredictionResponse(
            order_id=order.order_id,
            prediction=overall_prediction,
            items=item_predictions,
            overall_probability=round(overall_probability, 4),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("STOCK AVAILABILITY PREDICTION API")
    print("="*70)
    print("\nStarting server...")
    print("API will be available at: http://localhost:8000")
    print("\nEndpoints:")
    print("  GET  /                - Service info")
    print("  GET  /health          - Health check")
    print("  POST /predict         - Simple prediction (returns {prediction: true/false})")
    print("  POST /predict/detailed - Detailed prediction with probabilities")
    print("\nAPI docs: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop")
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)