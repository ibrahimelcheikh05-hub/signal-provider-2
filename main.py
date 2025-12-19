"""
Trading Signal API Server

This FastAPI application exposes a REST API endpoint for generating trading signals
by evaluating market data and technical indicators through the agent.py module.

Usage:
    Development: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    Production:  uvicorn main:app --host 0.0.0.0 --port 8000
    
    Or simply: python main.py

Endpoint:
    POST /generate-signal
    
Example curl request:
    curl -X POST "http://localhost:8000/generate-signal" \
         -H "Content-Type: application/json" \
         -d '{
           "instrument": "EURUSD",
           "timeframe": "1H",
           "timestamp": "2024-01-15T10:00:00Z",
           "close": 1.0850,
           "high": 1.0865,
           "low": 1.0835,
           "RSI": 18.5,
           "RSI_DAILY": 45.2,
           "ATR": 0.0025,
           "EMA50_daily": 1.0800,
           "candle_type": "hammer",
           "pattern": "double_bottom",
           "divergence": true,
           "recent_swing_low": 1.0820,
           "recent_swing_high": null,
           "strict_mode": false
         }'
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
from agent import evaluate_signal


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Trading Signal Generator API",
    description="REST API for generating trading signals based on market data and technical indicators",
    version="1.0.0"
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MarketDataRequest(BaseModel):
    """
    Market data input schema for signal generation.
    All required fields for the trading signal evaluation.
    """
    # Required fields
    instrument: str = Field(..., description="Trading instrument symbol (e.g., EURUSD, BTCUSD)")
    timeframe: str = Field(..., description="Chart timeframe (e.g., 1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W)")
    timestamp: str = Field(..., description="Timestamp of the market data")
    close: float = Field(..., description="Current closing price")
    high: float = Field(..., description="Current/recent high price")
    low: float = Field(..., description="Current/recent low price")
    RSI: float = Field(..., description="RSI indicator on the current timeframe")
    RSI_DAILY: float = Field(..., description="RSI indicator on daily timeframe")
    ATR: float = Field(..., description="Average True Range for volatility measurement")
    EMA50_daily: float = Field(..., description="50-period EMA on daily timeframe")
    
    # Optional fields
    candle_type: Optional[str] = Field(None, description="Candlestick pattern type (e.g., hammer, shooting_star)")
    pattern: Optional[str] = Field(None, description="Chart pattern (e.g., double_top, head_shoulders)")
    divergence: Optional[bool] = Field(False, description="Whether price/RSI divergence is present")
    recent_swing_low: Optional[float] = Field(None, description="Recent swing low price for stop loss calculation")
    recent_swing_high: Optional[float] = Field(None, description="Recent swing high price for stop loss calculation")
    strict_mode: Optional[bool] = Field(False, description="Enable strict mode for RSI thresholds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "instrument": "EURUSD",
                "timeframe": "1H",
                "timestamp": "2024-01-15T10:00:00Z",
                "close": 1.0850,
                "high": 1.0865,
                "low": 1.0835,
                "RSI": 18.5,
                "RSI_DAILY": 45.2,
                "ATR": 0.0025,
                "EMA50_daily": 1.0800,
                "candle_type": "hammer",
                "pattern": "double_bottom",
                "divergence": True,
                "recent_swing_low": 1.0820,
                "recent_swing_high": None,
                "strict_mode": False
            }
        }


class SignalResponse(BaseModel):
    """
    Trading signal output schema.
    Contains the trade decision and all relevant parameters.
    """
    status: str = Field(..., description="Trade status: 'long', 'short', or 'no_trade'")
    reason: str = Field(..., description="Reason for the decision")
    entry: Optional[float] = Field(None, description="Entry price level")
    stop_loss: Optional[float] = Field(None, description="Stop loss price level")
    take_profit: Optional[float] = Field(None, description="Take profit price level")
    rrr: Optional[float] = Field(None, description="Risk-to-reward ratio")
    confidence: float = Field(..., description="Confidence score (0-100)")
    message: str = Field(..., description="Human-readable message with trade details")
    instrument: str = Field(..., description="Trading instrument")
    timeframe: str = Field(..., description="Chart timeframe")
    timestamp: str = Field(..., description="Signal timestamp")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Health check endpoint.
    Returns basic API information.
    """
    return {
        "service": "Trading Signal Generator API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate-signal": "Generate trading signal from market data",
            "GET /docs": "Interactive API documentation",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and deployment platforms.
    """
    return {"status": "healthy"}


@app.post("/generate-signal", response_model=SignalResponse)
async def generate_signal(market_data: MarketDataRequest):
    """
    Generate a trading signal based on market data and technical indicators.
    
    This endpoint evaluates the provided market data through multiple filters:
    - Data validation
    - Trend analysis
    - Confluence checks
    - Risk management calculations
    - Confidence scoring
    
    Args:
        market_data: Market data and technical indicators
        
    Returns:
        SignalResponse: Complete trading signal with entry, SL, TP, and confidence
        
    Raises:
        HTTPException: 500 Internal Server Error if signal generation fails
    """
    try:
        # Convert Pydantic model to dictionary for agent.py
        data_dict = market_data.model_dump()
        
        # Call the signal evaluation function from agent.py
        signal = evaluate_signal(data_dict)
        
        # Return the signal as JSON response
        return signal
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error generating signal: {str(e)}")
        
        # Return error response with details
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Signal generation failed",
                "message": str(e),
                "type": type(e).__name__
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    Ensures all errors return a consistent JSON response.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url)
        }
    )


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    """
    Run the FastAPI server directly with uvicorn.
    
    Configuration:
    - host: 0.0.0.0 (accessible from any network interface)
    - port: 8000 (default, can be changed via PORT env variable)
    - reload: False in production (enable for development)
    """
    import os
    
    # Get port from environment variable (for Railway, Render, Replit)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Set to True for development
    )
