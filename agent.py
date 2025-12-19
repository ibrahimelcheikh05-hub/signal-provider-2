"""
Trading Signal Evaluation Module

This module evaluates market data and technical indicators to generate
trading signals with risk management parameters.

NOW FULLY TIMEFRAME-AGNOSTIC - Works on ANY timeframe without 4H dependency.
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
            - timeframe (str): Chart timeframe (e.g., '15m', '1H', '4H', '1D')
            - timestamp (str/int): Current timestamp
            - close (float): Current market price
            - RSI (float): RSI on current timeframe
            - RSI_HTF (float): RSI on higher timeframe (for context)
            - EMA50_HTF (float): 50-period EMA on higher timeframe
            - Additional indicator data
    
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
        "timeframe",       # Chart timeframe (any timeframe accepted)
        "close",           # Current closing price
        "high",            # Current/recent high price
        "low",             # Current/recent low price
        "RSI",             # RSI indicator on current timeframe
        "ATR"              # Average True Range for volatility
    ]
    
    # Optional but recommended fields (higher timeframe context)
    optional_htf_fields = ["RSI_DAILY", "EMA50_daily"]
    
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
    
    # All validation checks passed - data is valid and ready for analysis
    
    
    # ============================================================================
    # MODULE 2: TREND FILTER (OPTIONAL - ADAPTABLE)
    # ============================================================================
    
    # Determine market trend using higher timeframe context IF AVAILABLE
    # If HTF data is not provided, we'll evaluate based on current timeframe only
    
    close = data["close"]
    
    # Check if higher timeframe EMA is provided
    use_htf_trend = "EMA50_daily" in data and data["EMA50_daily"] is not None
    
    if use_htf_trend:
        ema50_htf = data["EMA50_daily"]
        
        # Compare current close price to the higher timeframe 50 EMA
        if close > ema50_htf:
            trend = "bullish"
        else:
            trend = "bearish"
    else:
        # No HTF trend filter - allow both directions
        # We'll determine trend from RSI and price action on current timeframe
        rsi = data["RSI"]
        
        if rsi < 50:
            # RSI suggests oversold/bearish conditions - look for longs (reversal)
            trend = "bullish"
        else:
            # RSI suggests overbought/bullish conditions - look for shorts (reversal)
            trend = "bearish"
    
    
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
    # Check for RSI at extreme oversold/overbought levels on CURRENT timeframe
    
    rsi = data["RSI"]
    rsi_confluence_met = False
    
    if trend == "bullish":
        # For long entries: look for oversold conditions
        if strict_mode:
            # Strict mode: RSI must be extremely oversold (<=5)
            if rsi <= 5:
                rsi_confluence_met = True
                confluence_details.append(f"RSI extremely oversold: {rsi:.2f}")
        else:
            # Normal mode: RSI oversold (<=30)
            if rsi <= 30:
                rsi_confluence_met = True
                confluence_details.append(f"RSI oversold: {rsi:.2f}")
    
    elif trend == "bearish":
        # For short entries: look for overbought conditions
        if strict_mode:
            # Strict mode: RSI must be extremely overbought (>=95)
            if rsi >= 95:
                rsi_confluence_met = True
                confluence_details.append(f"RSI extremely overbought: {rsi:.2f}")
        else:
            # Normal mode: RSI overbought (>=70)
            if rsi >= 70:
                rsi_confluence_met = True
                confluence_details.append(f"RSI overbought: {rsi:.2f}")
    
    if rsi_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 2: CANDLE CONFIRMATION (OPTIONAL)
    # -------------------------------------------------------------------------
    
    candle_confluence_met = False
    candle_type = data.get("candle_type", None)
    
    if candle_type:
        bullish_candles = ["hammer", "bullish_engulfing", "morning_star", "bullish_pin_bar"]
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
    
    pattern_confluence_met = False
    
    pattern = data.get("pattern", None)
    if pattern:
        bullish_patterns = ["double_bottom", "inverse_head_shoulders", "ascending_triangle", 
                           "bullish_flag", "cup_and_handle"]
        bearish_patterns = ["double_top", "head_shoulders", "descending_triangle", 
                           "bearish_flag", "rising_wedge"]
        
        if trend == "bullish" and pattern.lower() in bullish_patterns:
            pattern_confluence_met = True
            confluence_details.append(f"Bullish pattern: {pattern}")
        elif trend == "bearish" and pattern.lower() in bearish_patterns:
            pattern_confluence_met = True
            confluence_details.append(f"Bearish pattern: {pattern}")
    
    divergence = data.get("divergence", False)
    if divergence:
        pattern_confluence_met = True
        confluence_details.append("Price/RSI divergence detected")
    
    if pattern_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE 4: HIGHER TIMEFRAME ALIGNMENT (OPTIONAL)
    # -------------------------------------------------------------------------
    # Only check HTF alignment if HTF data is provided
    
    trend_confluence_met = False
    
    if "RSI_DAILY" in data and data["RSI_DAILY"] is not None:
        rsi_htf = data["RSI_DAILY"]
        
        if trend == "bullish":
            # For bullish trend: HTF RSI should not be overbought
            if rsi_htf < 70:
                trend_confluence_met = True
                confluence_details.append(f"HTF trend aligned (RSI HTF: {rsi_htf:.2f})")
        
        elif trend == "bearish":
            # For bearish trend: HTF RSI should not be oversold
            if rsi_htf > 30:
                trend_confluence_met = True
                confluence_details.append(f"HTF trend aligned (RSI HTF: {rsi_htf:.2f})")
    else:
        # No HTF data - automatically grant this confluence
        trend_confluence_met = True
        confluence_details.append("HTF alignment: not required (no HTF data)")
    
    if trend_confluence_met:
        confluence_count += 1
    
    # -------------------------------------------------------------------------
    # CONFLUENCE REQUIREMENT CHECK
    # -------------------------------------------------------------------------
    # Minimum requirement: at least 2 out of 4 confluences must be met
    # (Reduced from 3 to make it less restrictive)
    
    min_confluences = 2
    
    if confluence_count < min_confluences:
        failed_confluences = []
        
        if not rsi_confluence_met:
            if trend == "bullish":
                threshold = 5 if strict_mode else 30
                failed_confluences.append(f"RSI not oversold ({rsi:.2f} > {threshold})")
            elif trend == "bearish":
                threshold = 95 if strict_mode else 70
                failed_confluences.append(f"RSI not overbought ({rsi:.2f} < {threshold})")
        
        if not candle_confluence_met:
            if candle_type:
                failed_confluences.append(f"Candle pattern '{candle_type}' does not support {trend} trend")
            else:
                failed_confluences.append("No candle confirmation provided")
        
        if not pattern_confluence_met:
            failed_confluences.append("No chart pattern or divergence detected")
        
        if not trend_confluence_met and "RSI_DAILY" in data:
            rsi_htf = data.get("RSI_DAILY", "N/A")
            if trend == "bullish":
                failed_confluences.append(f"HTF RSI too high ({rsi_htf} >= 70)")
            elif trend == "bearish":
                failed_confluences.append(f"HTF RSI too low ({rsi_htf} <= 30)")
        
        met_description = '; '.join(confluence_details) if confluence_details else 'None'
        failed_description = '; '.join(failed_confluences)
        
        confidence_map = {0: 0, 1: 35}
        calculated_confidence = confidence_map.get(confluence_count, 0)
        
        return {
            "status": "no_trade",
            "reason": "not_enough_confluences",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": calculated_confidence,
            "message": f"Only {confluence_count}/4 confluences met. Need at least {min_confluences}. Met: {met_description}. Failed: {failed_description}",
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    
    # ============================================================================
    # MODULE 4: ENTRY SIGNAL GENERATION
    # ============================================================================
    
    if trend == "bullish":
        signal_direction = "long"
    elif trend == "bearish":
        signal_direction = "short"
    
    entry_price = data["close"]
    
    
    # ============================================================================
    # MODULE 5: STOP LOSS & TAKE PROFIT CALCULATION
    # ============================================================================
    
    atr = data["ATR"]
    
    # Start with ATR-based stop loss distance
    sl_distance = 1.5 * atr  # Slightly wider than before for more breathing room
    
    recent_swing_low = data.get("recent_swing_low", None)
    recent_swing_high = data.get("recent_swing_high", None)
    
    if signal_direction == "long" and recent_swing_low is not None:
        structure_sl_distance = entry_price - recent_swing_low
        if structure_sl_distance > sl_distance:
            sl_distance = structure_sl_distance
    
    elif signal_direction == "short" and recent_swing_high is not None:
        structure_sl_distance = recent_swing_high - entry_price
        if structure_sl_distance > sl_distance:
            sl_distance = structure_sl_distance
    
    # Take profit: 2:1 minimum RRR
    tp_distance = 2.0 * sl_distance
    
    if signal_direction == "long":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    elif signal_direction == "short":
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
    
    rrr = tp_distance / sl_distance
    
    entry_price = round(entry_price, 5)
    stop_loss = round(stop_loss, 5)
    take_profit = round(take_profit, 5)
    rrr = round(rrr, 2)
    
    
    # ============================================================================
    # MODULE 6: CONFIDENCE SCORING
    # ============================================================================
    
    confidence_score = 0
    
    # COMPONENT 1: CONFLUENCES (40% weight)
    if confluence_count == 2:
        confluence_percentage = 28  # 2/4 = 70% of 40%
    elif confluence_count == 3:
        confluence_percentage = 34  # 3/4 = 85% of 40%
    elif confluence_count == 4:
        confluence_percentage = 38  # 4/4 = 95% of 40%
    else:
        confluence_percentage = (confluence_count / 4) * 40
    
    confidence_score += confluence_percentage
    
    # COMPONENT 2: RSI POSITIONING (30% weight)
    rsi_score = 0
    
    if trend == "bullish":
        if rsi <= 20:
            rsi_score = 30  # Deeply oversold - excellent
        elif rsi <= 30:
            rsi_score = 25  # Oversold - good
        elif rsi <= 40:
            rsi_score = 18  # Slightly oversold - acceptable
        else:
            rsi_score = 10  # Not oversold - weak
    
    elif trend == "bearish":
        if rsi >= 80:
            rsi_score = 30  # Deeply overbought - excellent
        elif rsi >= 70:
            rsi_score = 25  # Overbought - good
        elif rsi >= 60:
            rsi_score = 18  # Slightly overbought - acceptable
        else:
            rsi_score = 10  # Not overbought - weak
    
    confidence_score += rsi_score
    
    # COMPONENT 3: PATTERN/CANDLE QUALITY (30% weight)
    pattern_score = 0
    
    if candle_confluence_met and pattern_confluence_met:
        pattern_score = 30  # Both present - excellent
    elif candle_confluence_met or pattern_confluence_met:
        pattern_score = 20  # One present - good
    else:
        pattern_score = 10  # None present - still acceptable with other confluences
    
    confidence_score += pattern_score
    
    confidence_score = round(confidence_score, 1)
    
    # Lower threshold to 60% (was 70%)
    if confidence_score < 60:
        return {
            "status": "no_trade",
            "reason": "confidence_too_low",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "rrr": None,
            "confidence": confidence_score,
            "message": f"Confidence score {confidence_score}% is below minimum threshold of 60%.",
            "instrument": data.get("instrument"),
            "timeframe": data.get("timeframe"),
            "timestamp": data.get("timestamp")
        }
    
    # Cap at 95%
    if confidence_score > 95:
        confidence_score = 95
    
    
    # ============================================================================
    # MODULE 7: FINAL DECISION & RISK CHECKS
    # ============================================================================
    
    # Final validation
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
    
    # Generate final message
    htf_status = "with HTF filter" if use_htf_trend else "without HTF filter"
    message_parts = [
        f"Timeframe: {data.get('timeframe')}",
        f"Trend: {trend.upper()} ({htf_status})",
        f"Signal: {signal_direction.upper()}",
        f"Confluences ({confluence_count}/4): {'; '.join(confluence_details)}"
    ]
    
    final_message = " | ".join(message_parts)
    
    return {
        "status": signal_direction,
        "reason": "all_conditions_met",
        "entry": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rrr": rrr,
        "confidence": confidence_score,
        "message": final_message,
        "instrument": data.get("instrument"),
        "timeframe": data.get("timeframe"),
        "timestamp": data.get("timestamp")
    }
