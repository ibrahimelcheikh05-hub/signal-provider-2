"""
Trading Signal Evaluation Module

This module evaluates market data and technical indicators to generate
trading signals with risk management parameters.
"""

from typing import Dict, Any, Optional


def evaluate_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate market data and indicators to generate a trading signal.
    
    This function analyzes the provided market data including price action,
    technical indicators, and market conditions to determine whether to
    enter a trade (long/short) or stay out of the market.
    
    Args:
        data (dict): A dictionary containing market and indicator data with keys:
            - instrument (str): Trading instrument symbol
            - timeframe (str): Chart timeframe (e.g., '1h', '4h', '1d')
            - timestamp (str/int): Current timestamp
            - price (float): Current market price
            - Additional indicator data (RSI, MACD, moving averages, etc.)
    
    Returns:
        dict: A dictionary containing the trade decision with keys:
            - status (str): 'long', 'short', or 'no_trade'
            - reason (str): Explanation for the decision
            - entry (float|None): Suggested entry price
            - stop_loss (float|None): Stop loss price level
            - take_profit (float|None): Take profit price level
            - rrr (float|None): Risk-to-reward ratio
            - confidence (int): Confidence score (0-100)
            - message (str): Additional information or warnings
            - instrument (str): Trading instrument
            - timeframe (str): Chart timeframe
            - timestamp (str/int): Timestamp of the signal
    """
    
    # ============================================================================
    # MODULE 1: DATA VALIDATION
    # ============================================================================
    
    # Define all required fields for signal evaluation
    required_fields = [
        "instrument",      # Trading symbol (e.g., "EURUSD", "BTCUSD")
        "timeframe",       # Chart timeframe (must be "4H")
        "close",           # Current closing price
        "high",            # Current/recent high price
        "low",             # Current/recent low price
        "RSI_4H",          # RSI indicator on 4H timeframe
        "RSI_DAILY",       # RSI indicator on daily timeframe
        "ATR",             # Average True Range for volatility
        "EMA50_daily"      # 50-period EMA on daily timeframe
    ]
    
    # Check if all required fields are present in the input data
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    # If any required field is missing, return early with error status
    if missing_fields:
        return {
            "status": "no_trade",
            "reason": "data_invalid",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": 0,
            "message": f"Missing required fields: {', '.join(missing_fields)}",
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    # Check if any required field has a None value
    none_fields = []
    for field in required_fields:
        if data[field] is None:
            none_fields.append(field)
    
    # If any required field is None, return early with error status
    if none_fields:
        return {
            "status": "no_trade",
            "reason": "data_invalid",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": 0,
            "message": f"Fields with None values: {', '.join(none_fields)}",
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    # Timeframe validation removed - strategy now works with any timeframe
    # Accepts: 1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W, etc.
    # The strategy adapts to whatever timeframe is provided
    
    # All validation checks passed - data is valid and ready for analysis
    
    
    # ============================================================================
    # MODULE 2: TREND FILTER
    # ============================================================================
    
    # Determine market trend by comparing current price to the daily 50 EMA
    # The 50 EMA on the daily timeframe acts as a dynamic support/resistance
    # and helps identify the overall market direction
    
    # Extract values for trend analysis
    close = data["close"]
    ema50_daily = data["EMA50_daily"]
    
    # Compare current close price to the daily 50 EMA
    if close > ema50_daily:
        # Price is above the daily 50 EMA - uptrend
        trend = "bullish"
    else:
        # Price is below the daily 50 EMA - downtrend
        trend = "bearish"
    
    # The trend variable will be used to:
    # 1. Filter signals to align with the overall market direction (trend-following)
    # 2. Identify potential counter-trend reversal opportunities (with strong confluences)
    # 3. Determine the direction of trade entries (long in bullish, short in bearish)
    # 4. Adjust confidence scores based on trend alignment
    
    
    # ============================================================================
    # MODULE 3: CONFLUENCE ANALYSIS
    # ============================================================================
    
    # Initialize confluence tracking
    confluence_count = 0
    confluence_details = []
    
    # Determine if we're in strict mode for RSI (using optional parameter)
    strict_mode = data.get("strict_mode", False)
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 1: RSI EXTREME AT STRUCTURE
    # -------------------------------------------------------------------------
    # Check for RSI at extreme oversold/overbought levels
    # These extreme levels suggest potential reversal points
    
    rsi_4h = data["RSI_4H"]
    rsi_confluence_met = False
    
    if trend == "bullish":
        # For long entries: look for oversold conditions
        if strict_mode:
            # Strict mode: RSI must be extremely oversold (<=5)
            if rsi_4h <= 5:
                rsi_confluence_met = True
                confluence_details.append(f"RSI 4H extremely oversold: {rsi_4h:.2f}")
        else:
            # Normal mode: RSI oversold (<=20)
            if rsi_4h <= 20:
                rsi_confluence_met = True
                confluence_details.append(f"RSI 4H oversold: {rsi_4h:.2f}")
    
    elif trend == "bearish":
        # For short entries: look for overbought conditions
        if strict_mode:
            # Strict mode: RSI must be extremely overbought (>=95)
            if rsi_4h >= 95:
                rsi_confluence_met = True
                confluence_details.append(f"RSI 4H extremely overbought: {rsi_4h:.2f}")
        else:
            # Normal mode: RSI overbought (>=80)
            if rsi_4h >= 80:
                rsi_confluence_met = True
                confluence_details.append(f"RSI 4H overbought: {rsi_4h:.2f}")
    
    if rsi_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 2: CANDLE CONFIRMATION (OPTIONAL)
    # -------------------------------------------------------------------------
    # Check for specific candlestick patterns that support the trade direction
    # Examples: hammer, shooting star, engulfing, doji, etc.
    
    candle_confluence_met = False
    candle_type = data.get("candle_type", None)
    
    if candle_type:
        # List of bullish candle patterns
        bullish_candles = ["hammer", "bullish_engulfing", "morning_star", "bullish_pin_bar"]
        # List of bearish candle patterns
        bearish_candles = ["shooting_star", "bearish_engulfing", "evening_star", "bearish_pin_bar"]
        
        if trend == "bullish" and candle_type.lower() in bullish_candles:
            candle_confluence_met = True
            confluence_details.append(f"Bullish candle pattern: {candle_type}")
            confluence_count += 1
        elif trend == "bearish" and candle_type.lower() in bearish_candles:
            candle_confluence_met = True
            confluence_details.append(f"Bearish candle pattern: {candle_type}")
            confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 3: PATTERN OR DIVERGENCE
    # -------------------------------------------------------------------------
    # Check for chart patterns or RSI/price divergence
    # Patterns: double top/bottom, head and shoulders, triangles, etc.
    # Divergence: price makes new high/low but RSI doesn't (or vice versa)
    
    pattern_confluence_met = False
    
    # Check for pattern string
    pattern = data.get("pattern", None)
    if pattern:
        # List of bullish patterns
        bullish_patterns = ["double_bottom", "inverse_head_shoulders", "ascending_triangle", 
                           "bullish_flag", "cup_and_handle"]
        # List of bearish patterns
        bearish_patterns = ["double_top", "head_shoulders", "descending_triangle", 
                           "bearish_flag", "rising_wedge"]
        
        if trend == "bullish" and pattern.lower() in bullish_patterns:
            pattern_confluence_met = True
            confluence_details.append(f"Bullish pattern: {pattern}")
        elif trend == "bearish" and pattern.lower() in bearish_patterns:
            pattern_confluence_met = True
            confluence_details.append(f"Bearish pattern: {pattern}")
    
    # Check for divergence
    divergence = data.get("divergence", False)
    if divergence:
        pattern_confluence_met = True
        confluence_details.append("Price/RSI divergence detected")
    
    if pattern_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 4: TREND ALIGNMENT (DAILY TREND)
    # -------------------------------------------------------------------------
    # Check if the potential trade aligns with the daily trend
    # Trend-aligned trades generally have higher probability of success
    
    rsi_daily = data["RSI_DAILY"]
    trend_confluence_met = False
    
    if trend == "bullish":
        # For bullish trend: daily RSI should not be overbought
        # This ensures we're not buying at the top of a rally
        if rsi_daily < 70:
            trend_confluence_met = True
            confluence_details.append(f"Daily trend aligned (RSI Daily: {rsi_daily:.2f})")
    
    elif trend == "bearish":
        # For bearish trend: daily RSI should not be oversold
        # This ensures we're not selling at the bottom of a decline
        if rsi_daily > 30:
            trend_confluence_met = True
            confluence_details.append(f"Daily trend aligned (RSI Daily: {rsi_daily:.2f})")
    
    if trend_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE REQUIREMENT CHECK
    # -------------------------------------------------------------------------
    # Minimum requirement: at least 3 out of 4 confluences must be met
    # This ensures high-probability setups with multiple confirmations
    
    if confluence_count < 3:
        # Build detailed explanation of failed confluences
        failed_confluences = []
        
        # Check which confluences failed and explain why
        if not rsi_confluence_met:
            if trend == "bullish":
                if strict_mode:
                    failed_confluences.append(f"RSI 4H not extremely oversold ({rsi_4h:.2f} > 5)")
                else:
                    failed_confluences.append(f"RSI 4H not oversold ({rsi_4h:.2f} > 20)")
            elif trend == "bearish":
                if strict_mode:
                    failed_confluences.append(f"RSI 4H not extremely overbought ({rsi_4h:.2f} < 95)")
                else:
                    failed_confluences.append(f"RSI 4H not overbought ({rsi_4h:.2f} < 80)")
        
        if not candle_confluence_met:
            if candle_type:
                failed_confluences.append(f"Candle pattern '{candle_type}' does not support {trend} trend")
            else:
                failed_confluences.append("No bullish/bearish candle confirmation provided")
        
        if not pattern_confluence_met:
            if pattern and not divergence:
                failed_confluences.append(f"Pattern '{pattern}' does not align with {trend} trend")
            elif divergence and not pattern:
                failed_confluences.append("Divergence alone insufficient without supporting pattern")
            else:
                failed_confluences.append("No chart pattern or divergence detected")
        
        if not trend_confluence_met:
            if trend == "bullish":
                failed_confluences.append(f"Daily RSI too high ({rsi_daily:.2f} >= 70), potential trend exhaustion")
            elif trend == "bearish":
                failed_confluences.append(f"Daily RSI too low ({rsi_daily:.2f} <= 30), potential trend exhaustion")
        
        # Build human-readable message
        met_description = '; '.join(confluence_details) if confluence_details else 'None'
        failed_description = '; '.join(failed_confluences)
        
        # Check for conflicting signals
        conflicting_signals = []
        if pattern and candle_type:
            bullish_patterns = ["double_bottom", "inverse_head_shoulders", "ascending_triangle", 
                               "bullish_flag", "cup_and_handle"]
            bearish_patterns = ["double_top", "head_shoulders", "descending_triangle", 
                               "bearish_flag", "rising_wedge"]
            bullish_candles = ["hammer", "bullish_engulfing", "morning_star", "bullish_pin_bar"]
            bearish_candles = ["shooting_star", "bearish_engulfing", "evening_star", "bearish_pin_bar"]
            
            pattern_is_bullish = pattern.lower() in bullish_patterns
            pattern_is_bearish = pattern.lower() in bearish_patterns
            candle_is_bullish = candle_type.lower() in bullish_candles
            candle_is_bearish = candle_type.lower() in bearish_candles
            
            if (pattern_is_bullish and candle_is_bearish) or (pattern_is_bearish and candle_is_bullish):
                conflicting_signals.append(f"Pattern '{pattern}' conflicts with candle '{candle_type}'")
        
        # Determine reason code
        reason_code = "conflicting_signals" if conflicting_signals else "not_enough_confluences"
        
        # Construct final message
        if conflicting_signals:
            conflict_msg = ' '.join(conflicting_signals)
            message = f"Conflicting signals detected: {conflict_msg}. Only {confluence_count}/4 confluences met. Met: {met_description}. Failed: {failed_description}"
        else:
            message = f"Only {confluence_count}/4 confluences met. Need at least 3. Met: {met_description}. Failed: {failed_description}"
        
        # Calculate deterministic confidence based on confluence count
        confidence_map = {0: 0, 1: 25, 2: 50}
        calculated_confidence = confidence_map.get(confluence_count, 0)
        
        return {
            "status": "no_trade",
            "reason": reason_code,
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": calculated_confidence,
            "message": message,
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    # Confluences are sufficient - proceed to signal generation
    
    
    # ============================================================================
    # MODULE 4: ENTRY SIGNAL GENERATION
    # ============================================================================
    
    # Determine trade direction based on trend and confluences
    # Since we have sufficient confluences, we can generate an entry signal
    
    if trend == "bullish":
        signal_direction = "long"
    elif trend == "bearish":
        signal_direction = "short"
    
    # Set entry price to current close price
    entry_price = data["close"]
    
    
    # ============================================================================
    # MODULE 5: STOP LOSS & TAKE PROFIT CALCULATION
    # ============================================================================
    
    # Extract ATR for volatility-based stop loss calculation
    atr = data["ATR"]
    
    # -------------------------------------------------------------------------
    # STOP LOSS CALCULATION
    # -------------------------------------------------------------------------
    # Stop loss is determined by the larger of:
    # 1. 1.0 × ATR (volatility-based stop)
    # 2. Distance to recent swing high/low (structure-based stop)
    #
    # ATR-based stops adapt to market volatility
    # Structure-based stops respect key support/resistance levels
    
    # Start with ATR-based stop loss distance
    sl_distance = 1.0 * atr
    
    # Check if swing levels are provided for structure-based stops
    recent_swing_low = data.get("recent_swing_low", None)
    recent_swing_high = data.get("recent_swing_high", None)
    
    if signal_direction == "long" and recent_swing_low is not None:
        # For long trades: stop below recent swing low
        # Calculate distance from entry to swing low
        structure_sl_distance = entry_price - recent_swing_low
        
        # Use the larger of ATR-based or structure-based distance
        # This ensures we're beyond the swing low for better protection
        if structure_sl_distance > sl_distance:
            sl_distance = structure_sl_distance
    
    elif signal_direction == "short" and recent_swing_high is not None:
        # For short trades: stop above recent swing high
        # Calculate distance from entry to swing high
        structure_sl_distance = recent_swing_high - entry_price
        
        # Use the larger of ATR-based or structure-based distance
        # This ensures we're beyond the swing high for better protection
        if structure_sl_distance > sl_distance:
            sl_distance = structure_sl_distance
    
    # -------------------------------------------------------------------------
    # TAKE PROFIT CALCULATION
    # -------------------------------------------------------------------------
    # Take profit is set at minimum 2:1 risk-reward ratio
    # TP distance = 2 × SL distance
    # This ensures we're risking $1 to make at least $2
    
    tp_distance = 2.0 * sl_distance
    
    # -------------------------------------------------------------------------
    # CALCULATE ACTUAL PRICE LEVELS
    # -------------------------------------------------------------------------
    # Apply the calculated distances to entry price based on trade direction
    
    if signal_direction == "long":
        # Long trade: SL below entry, TP above entry
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    
    elif signal_direction == "short":
        # Short trade: SL above entry, TP below entry
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
    
    # -------------------------------------------------------------------------
    # RISK-REWARD RATIO CALCULATION
    # -------------------------------------------------------------------------
    # RRR = Reward (TP distance) / Risk (SL distance)
    # Minimum acceptable RRR is 2.0 (as enforced by TP calculation)
    
    rrr = tp_distance / sl_distance
    
    # -------------------------------------------------------------------------
    # ROUND ALL PRICE LEVELS
    # -------------------------------------------------------------------------
    # Round to appropriate decimal places for clean output
    # Most forex pairs use 5 decimals, stocks/crypto use 2-4
    
    entry_price = round(entry_price, 5)
    stop_loss = round(stop_loss, 5)
    take_profit = round(take_profit, 5)
    rrr = round(rrr, 2)
    
    
    # ============================================================================
    # MODULE 6: CONFIDENCE SCORING
    # ============================================================================
    
    # Confidence score is calculated as a weighted sum of multiple factors
    # Total: 100% = Confluences (25%) + Trend (20%) + Level (20%) + Candle (20%) + Market (15%)
    # Minimum acceptable confidence: 70%
    
    confidence_score = 0
    
    # -------------------------------------------------------------------------
    # COMPONENT 1: CONFLUENCES (25% weight)
    # -------------------------------------------------------------------------
    # Score based on number of confluences met (out of 4 possible)
    # Deterministic mapping: 3/4 = 75%, 4/4 = 90-95%
    
    if confluence_count == 3:
        confluence_percentage = 18.75  # 3/4 = 75% of 25% weight
    elif confluence_count == 4:
        confluence_percentage = 23.75  # 4/4 = 95% of 25% weight (slightly below max)
    else:
        confluence_percentage = (confluence_count / 4) * 25  # Fallback (shouldn't reach here)
    
    confidence_score += confluence_percentage
    
    # -------------------------------------------------------------------------
    # COMPONENT 2: TREND ALIGNMENT (20% weight)
    # -------------------------------------------------------------------------
    # Score based on how well the signal aligns with the daily trend
    # - Full points if RSI daily is in healthy range (not extreme)
    # - Partial points if RSI is getting extended
    
    trend_score = 0
    
    if trend == "bullish":
        # For bullish trades: check daily RSI positioning
        if rsi_daily < 50:
            # Strong pullback in uptrend - excellent entry
            trend_score = 20
        elif rsi_daily < 60:
            # Moderate pullback - good entry
            trend_score = 15
        elif rsi_daily < 70:
            # Shallow pullback - acceptable entry
            trend_score = 10
        else:
            # Overbought on daily - risky entry
            trend_score = 5
    
    elif trend == "bearish":
        # For bearish trades: check daily RSI positioning
        if rsi_daily > 50:
            # Strong rally in downtrend - excellent entry
            trend_score = 20
        elif rsi_daily > 40:
            # Moderate rally - good entry
            trend_score = 15
        elif rsi_daily > 30:
            # Shallow rally - acceptable entry
            trend_score = 10
        else:
            # Oversold on daily - risky entry
            trend_score = 5
    
    confidence_score += trend_score
    
    # -------------------------------------------------------------------------
    # COMPONENT 3: LEVEL QUALITY (20% weight)
    # -------------------------------------------------------------------------
    # Score based on proximity to key support/resistance levels
    # For now, using simplified default score of 20%
    # Future enhancement: calculate based on distance to S/R levels
    
    level_quality_score = 20  # Default: assume good level quality
    confidence_score += level_quality_score
    
    # -------------------------------------------------------------------------
    # COMPONENT 4: CANDLE CONFIRMATION QUALITY (20% weight)
    # -------------------------------------------------------------------------
    # Score based on strength of candlestick pattern
    # - Full points if strong reversal pattern present
    # - Partial points if pattern exists but weaker
    # - Reduced points if no candle confirmation
    
    candle_score = 0
    
    if candle_confluence_met:
        # Strong candle patterns get full points
        strong_patterns = ["hammer", "shooting_star", "bullish_engulfing", 
                          "bearish_engulfing", "morning_star", "evening_star"]
        if candle_type and candle_type.lower() in strong_patterns:
            candle_score = 20
        else:
            # Weaker patterns get partial points
            candle_score = 12
    else:
        # No candle confirmation: reduced score but not zero
        # (Other confluences may still be strong)
        candle_score = 8
    
    confidence_score += candle_score
    
    # -------------------------------------------------------------------------
    # COMPONENT 5: MARKET CONDITIONS (15% weight)
    # -------------------------------------------------------------------------
    # Score based on overall market environment and volatility
    # For now, using simplified default score of 15%
    # Future enhancement: factor in volume, volatility regime, session times
    
    market_conditions_score = 15  # Default: assume neutral market conditions
    confidence_score += market_conditions_score
    
    # -------------------------------------------------------------------------
    # CONFIDENCE THRESHOLD CHECK
    # -------------------------------------------------------------------------
    # Minimum confidence requirement: 70%
    # Below this threshold, signal quality is too low for trade execution
    
    confidence_score = round(confidence_score, 1)
    
    if confidence_score < 70:
        return {
            "status": "no_trade",
            "reason": "confidence_too_low",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": confidence_score,
            "message": f"Confidence score {confidence_score}% is below minimum threshold of 70%. "
                      f"Confluences: {confluence_percentage:.1f}%, Trend: {trend_score}, "
                      f"Level: {level_quality_score}, Candle: {candle_score}, Market: {market_conditions_score}",
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    # Confidence threshold met - proceed to final decision
    
    # Cap maximum confidence at 95% unless in strict mode with perfect conditions
    if confidence_score > 95 and not (strict_mode and confluence_count == 4):
        confidence_score = 95
    
    
    # ============================================================================
    # MODULE 7: FINAL DECISION & RISK CHECKS
    # ============================================================================
    
    # All validation checks have passed:
    # ✓ Data is valid and complete
    # ✓ Sufficient confluences (≥3/4)
    # ✓ Stop loss and take profit calculated
    # ✓ Confidence score meets threshold (≥70%)
    
    # -------------------------------------------------------------------------
    # FINAL RISK VALIDATION
    # -------------------------------------------------------------------------
    # Perform final sanity checks on risk parameters
    
    # Ensure stop loss and take profit are on correct side of entry
    if signal_direction == "long":
        if stop_loss >= entry_price or take_profit <= entry_price:
            return {
                "status": "no_trade",
                "reason": "invalid_risk_parameters",
                "entry": None,
                "stop_loss": None,
                "take_profit": None,
                "rrr": None,
                "confidence": confidence_score,
                "message": "Invalid SL/TP positioning for long trade",
                "instrument": data.get("instrument"),
                "timeframe": data.get("timeframe"),
                "timestamp": data.get("timestamp")
            }
    
    elif signal_direction == "short":
        if stop_loss <= entry_price or take_profit >= entry_price:
            return {
                "status": "no_trade",
                "reason": "invalid_risk_parameters",
                "entry": None,
                "stop_loss": None,
                "take_profit": None,
                "rrr": None,
                "confidence": confidence_score,
                "message": "Invalid SL/TP positioning for short trade",
                "instrument": data.get("instrument"),
                "timeframe": data.get("timeframe"),
                "timestamp": data.get("timestamp")
            }
    
    # -------------------------------------------------------------------------
    # GENERATE FINAL MESSAGE
    # -------------------------------------------------------------------------
    # Create a comprehensive message summarizing the trade setup
    
    # Build message with trend and confluence information
    message_parts = [
        f"Trend: {trend.upper()}",
        f"Signal: {signal_direction.upper()}",
        f"Confluences ({confluence_count}/4): {'; '.join(confluence_details)}"
    ]
    
    final_message = " | ".join(message_parts)
    
    # -------------------------------------------------------------------------
    # RETURN FINAL TRADE SIGNAL
    # -------------------------------------------------------------------------
    # All conditions met - return complete trade signal with all parameters
    
    return {
        "status": signal_direction,           # "long" or "short"
        "reason": "all_conditions_met",       # All checks passed
        "entry": entry_price,                 # Entry price level
        "stop_loss": stop_loss,               # Stop loss price level
        "take_profit": take_profit,           # Take profit price level
        "rrr": rrr,                           # Risk-to-reward ratio
        "confidence": confidence_score,       # Confidence percentage (0-100)
        "message": final_message,             # Summary of trade setup
        "instrument": data.get("instrument"), # Trading instrument
        "timeframe": data.get("timeframe"),   # Chart timeframe
        "timestamp": data.get("timestamp")    # Signal timestamp
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
# TODO: Add helper functions for each module as needed
# Example functions to implement:
# - validate_data(data: dict) -> tuple[bool, str]
# - calculate_trend(data: dict) -> str
# - check_confluences(data: dict) -> dict
# - calculate_stop_loss(entry: float, direction: str, atr: float) -> float
# - calculate_take_profit(entry: float, stop_loss: float, rrr: float) -> float
# - calculate_confidence(factors: dict) -> int
