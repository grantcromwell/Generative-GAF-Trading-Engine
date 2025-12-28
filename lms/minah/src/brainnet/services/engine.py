"""
Trading Engine - Core analysis and trading loop logic
Provides reusable functions for GUI and CLI interfaces

Supports both LLM-based analysis and ConvNeXt neural pattern recognition.
"""

import time
from datetime import datetime
from typing import Optional

import yfinance as yf

from typing import List, Dict, Optional, Tuple
import time
from datetime import datetime

import yfinance as yf
import numpy as np

from brainnet.agents import ResearchAgent, ReasoningAgent, _CONVNEXT_AVAILABLE
from brainnet.core import MemoryManager, load_config
from brainnet.services.data_flywheel import DataFlywheel
from brainnet.services.performance import calculate_metrics, format_metrics


def run_single_analysis(symbol: str = "ES=F", interval: str = "5m") -> dict:
    """
    Run a single GAF analysis on a symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC-USD', 'ETH-USD', 'ES=F', 'NQ=F')
        interval: Data interval
        
    Returns:
        Dictionary with analysis results
    """
    print(f"\n{'='*60}")
    print(f"  BRAINNET ANALYSIS: {symbol}")
    print(f"{'='*60}")
    
    # Initialize agents
    research = ResearchAgent()
    reasoning = ReasoningAgent()
    flywheel = DataFlywheel()
    
    # Fetch data
    print(f"\n[1/4] Fetching {symbol} data...")
    data = yf.download(symbol, period="1d", interval=interval, progress=False)
    
    if data.empty:
        print("⚠ No data received")
        return {"symbol": symbol, "error": "No data", "decision": None, "confidence": 0}
    
    # Handle multi-index columns from yfinance
    try:
        latest_price = float(data['Close'].iloc[-1].iloc[0]) if hasattr(data['Close'].iloc[-1], 'iloc') else float(data['Close'].iloc[-1])
    except:
        latest_price = float(data['Close'].iloc[-1])
    
    print(f"    {len(data)} bars | Latest: ${latest_price:.2f}")
    
    # GAF Analysis
    print(f"\n[2/4] Running GAF Pattern Analysis...")
    analysis = research.research(data)
    
    # Show features
    print(f"\n    GAF Features:")
    for k, v in analysis['features'].items():
        indicator = ''
        if k == 'trend_score':
            indicator = ' ← UPTREND' if v > 0.1 else ' ← DOWNTREND' if v < -0.1 else ' ← NEUTRAL'
        elif k == 'momentum':
            indicator = ' ← STRENGTHENING' if v > 0 else ' ← WEAKENING'
        print(f"      {k:22s}: {v:+.4f}{indicator}")
    
    # Confidence
    print(f"\n[3/4] Computing Confidence (BSC Model)...")
    confidence = reasoning.compute_confidence(analysis['analysis'])
    print(f"    Confidence: {confidence:.3f}")
    print(f"    Threshold:  0.780")
    
    # Refinement loop if needed
    refinements = 0
    config = load_config()
    memory = None
    try:
        memory = MemoryManager(config)
    except:
        pass
    
    memory_context = ""
    while confidence < 0.78 and refinements < 3:
        refinements += 1
        print(f"\n    ⟳ Refinement {refinements}/3")
        if memory:
            memory_context += " " + memory.get_context("pattern refinement")
        analysis = research.research(data, memory_context)
        confidence = reasoning.compute_confidence(analysis['analysis'])
        print(f"    New confidence: {confidence:.3f}")
    
    # Decision
    print(f"\n[4/4] Making Trading Decision...")
    decision = reasoning.decide(analysis['analysis'], confidence)
    
    # Parse decision
    if "long" in decision.lower():
        pos, emoji = "LONG", "📈"
    elif "short" in decision.lower():
        pos, emoji = "SHORT", "📉"
    elif "flat" in decision.lower():
        pos, emoji = "FLAT", "⏸"
    else:
        pos, emoji = "REFINE", "🔄"
    
    print(f"\n    {emoji} {pos} | Confidence: {confidence:.1%}")
    
    # Store in memory
    if memory:
        try:
            memory.add({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "decision": pos,
                "confidence": confidence,
                "refinements": refinements,
            })
            print("    ✓ Stored in memory")
        except:
            pass
    
    # Collect data in flywheel
    result = {
        "symbol": symbol,
        "price": latest_price,
        "decision": pos,
        "confidence": confidence,
        "trend": "Bullish" if analysis['features']['trend_score'] > 0 else "Bearish",
        "momentum": "Positive" if analysis['features']['momentum'] > 0 else "Negative",
        "features": analysis['features'],
        "refinements": refinements,
    }
    flywheel.collect_trading_data(result)
    print("    ✓ Collected in Data Flywheel")
    
    # Summary
    trend = "Bullish" if analysis['features']['trend_score'] > 0 else "Bearish"
    momentum = "Positive" if analysis['features']['momentum'] > 0 else "Negative"
    
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Symbol:     {symbol}")
    print(f"  Price:      ${latest_price:.2f}")
    print(f"  Trend:      {trend}")
    print(f"  Momentum:   {momentum}")
    print(f"  Confidence: {confidence:.1%}")
    print(f"  Signal:     {pos}")
    print(f"{'='*60}\n")
    
    return result


def run_trading_loop(symbol: str = "ES=F", interval: str = "5m", delay: int = 300):
    """
    Continuous trading loop with periodic analysis.
    
    Args:
        symbol: Trading symbol
        interval: Data interval
        delay: Seconds between iterations
    """
    config = load_config()
    
    try:
        memory = MemoryManager(config)
        print("✓ Memory initialized")
    except Exception as e:
        print(f"⚠ Memory failed: {e}")
        memory = None
    
    research = ResearchAgent()
    reasoning = ReasoningAgent()
    print("✓ Agents initialized")
    
    iteration = 0
    
    while True:
        iteration += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*50}")
        print(f"Iteration {iteration} | {ts}")
        
        try:
            print(f"\n[1/5] Fetching {symbol} {interval} data...")
            data = yf.download(symbol, period="1d", interval=interval, progress=False)
            
            if data.empty:
                print("⚠ No data")
                time.sleep(60)
                continue
            
            # Handle multi-index
            try:
                latest = float(data['Close'].iloc[-1].iloc[0]) if hasattr(data['Close'].iloc[-1], 'iloc') else float(data['Close'].iloc[-1])
            except:
                latest = float(data['Close'].iloc[-1])
            
            print(f"    {len(data)} bars, latest: ${latest:.2f}")
            
            memory_context = ""
            if memory:
                print("\n[2/5] Getting memory context...")
                memory_context = memory.get_context("recent trades")
            
            print("\n[3/5] GAF analysis...")
            analysis = research.research(data, memory_context)
            print(f"    {analysis['analysis'][:100]}...")
            
            print("\n[4/5] Computing confidence...")
            confidence = reasoning.compute_confidence(analysis['analysis'])
            print(f"    Confidence: {confidence:.3f}")
            
            # Adaptive refinement loop
            refinements = 0
            while confidence < 0.78 and refinements < 3:
                refinements += 1
                print(f"\n    ⟳ Refinement {refinements}/3")
                if memory:
                    memory_context += " " + memory.get_context("pattern refinement")
                analysis = research.research(data, memory_context)
                confidence = reasoning.compute_confidence(analysis['analysis'])
                print(f"    New confidence: {confidence:.3f}")
            
            print("\n[5/5] Decision...")
            decision = reasoning.decide(analysis['analysis'], confidence)
            
            if "long" in decision.lower():
                pos, emoji = "LONG", "📈"
            elif "short" in decision.lower():
                pos, emoji = "SHORT", "📉"
            else:
                pos, emoji = "FLAT", "⏸"
            
            print(f"\n    {emoji} {pos} | Conf: {confidence:.3f}")
            
            if memory:
                memory.add({
                    "timestamp": ts,
                    "symbol": symbol,
                    "decision": pos,
                    "confidence": confidence,
                    "refinements": refinements,
                })
                print("    ✓ Stored")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        print(f"\nSleeping {delay}s...")
        time.sleep(delay)


def run_convnext_analysis(
    symbol: str = "ES=F",
    interval: str = "5m",
    combine_with_llm: bool = True,
    device: str = "auto",
) -> dict:
    """
    Run ConvNeXt-enhanced GAF analysis.
    
    Uses ConvNeXt-Tiny neural network to analyze 3-channel GAF images
    for regime detection, directional bias, and volatility forecasting.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC-USD', 'ETH-USD', 'ES=F')
        interval: Data interval (e.g., '1m', '5m', '15m')
        combine_with_llm: Whether to also run LLM analysis for ensemble
        device: Compute device ("auto", "cuda", "mps", "cpu")
        
    Returns:
        Dictionary with ConvNeXt predictions and optionally LLM analysis
        
    Raises:
        ImportError: If PyTorch is not installed
    """
    if not _CONVNEXT_AVAILABLE:
        raise ImportError(
            "ConvNeXt requires PyTorch. Install with: pip install torch torchvision"
        )
    
    from brainnet.agents import ConvNeXtPredictor
    
    print(f"\n{'='*60}")
    print(f"  BRAINNET ConvNeXt ANALYSIS: {symbol}")
    print(f"{'='*60}")
    
    # Initialize agents
    research = ResearchAgent()
    convnext = ConvNeXtPredictor(device=device)
    
    print(f"\n    Model: ConvNeXt-Tiny (28M params)")
    print(f"    Device: {convnext.device}")
    
    # Fetch data
    print(f"\n[1/4] Fetching {symbol} data...")
    data = yf.download(symbol, period="1d", interval=interval, progress=False)
    
    if data.empty:
        print("⚠ No data received")
        return {"symbol": symbol, "error": "No data", "decision": None}
    
    # Handle multi-index columns from yfinance
    try:
        latest_price = float(data['Close'].iloc[-1].iloc[0]) if hasattr(data['Close'].iloc[-1], 'iloc') else float(data['Close'].iloc[-1])
    except Exception:
        latest_price = float(data['Close'].iloc[-1])
    
    print(f"    {len(data)} bars | Latest: ${latest_price:.2f}")
    
    # Extract close prices
    close = data['Close'].values.flatten()[-100:]  # Last 100 bars
    
    # Generate 3-channel GAF
    print(f"\n[2/4] Generating 3-channel GAF (224x224)...")
    gaf_rgb = research.generate_gaf_3channel(close, image_size=224)
    print(f"    Shape: {gaf_rgb.shape} | Dtype: {gaf_rgb.dtype}")
    print(f"    Channels: GASF (red), GADF (green), Heatmap (blue)")
    
    # ConvNeXt prediction
    print(f"\n[3/4] Running ConvNeXt inference...")
    start = time.perf_counter()
    prediction = convnext.predict(gaf_rgb, return_features=False)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"    Inference time: {elapsed_ms:.1f}ms")
    print(f"\n    Predictions:")
    print(f"      Regime:     {prediction.regime:16s} ({prediction.regime_confidence:.1%})")
    print(f"      Direction:  {prediction.direction:16s} ({prediction.direction_confidence:.1%})")
    print(f"      Volatility: {prediction.volatility:16s} ({prediction.volatility_confidence:.1%})")
    
    result = {
        "symbol": symbol,
        "price": latest_price,
        "convnext": prediction.to_dict(),
        "inference_ms": elapsed_ms,
    }
    
    # Optionally combine with LLM analysis for ensemble
    if combine_with_llm:
        print(f"\n[4/4] Running LLM analysis for ensemble...")
        reasoning = ReasoningAgent()
        
        llm_analysis = research.research(data)
        confidence = reasoning.compute_confidence(llm_analysis['analysis'])
        
        result["llm"] = {
            "features": llm_analysis['features'],
            "confidence": confidence,
            "scores": llm_analysis.get('scores', {}),
        }
        
        # Ensemble decision logic
        # Weight ConvNeXt direction by its confidence, LLM by BSC confidence
        convnext_weight = prediction.direction_confidence
        llm_weight = confidence
        
        # Map directions to scores
        dir_scores = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
        trend_sign = 1.0 if llm_analysis['features']['trend_score'] > 0 else -1.0
        
        # Weighted average of directional signals
        total_weight = convnext_weight + llm_weight + 1e-8
        ensemble_score = (
            dir_scores[prediction.direction] * convnext_weight +
            trend_sign * llm_weight
        ) / total_weight
        
        # Decision thresholds
        if ensemble_score > 0.2:
            final_decision = "LONG"
            emoji = "📈"
        elif ensemble_score < -0.2:
            final_decision = "SHORT"
            emoji = "📉"
        else:
            final_decision = "FLAT"
            emoji = "⏸"
        
        result["ensemble_decision"] = final_decision
        result["ensemble_score"] = round(ensemble_score, 4)
        result["ensemble_confidence"] = round((convnext_weight + llm_weight) / 2, 4)
        
        print(f"\n    LLM Confidence: {confidence:.1%}")
        print(f"    Ensemble Score: {ensemble_score:+.3f}")
        print(f"\n    {emoji} Ensemble Decision: {final_decision}")
    else:
        # ConvNeXt-only decision
        if prediction.direction == "bullish" and prediction.direction_confidence > 0.5:
            final_decision = "LONG"
            emoji = "📈"
        elif prediction.direction == "bearish" and prediction.direction_confidence > 0.5:
            final_decision = "SHORT"
            emoji = "📉"
        else:
            final_decision = "FLAT"
            emoji = "⏸"
        
        result["decision"] = final_decision
        print(f"\n    {emoji} Decision: {final_decision}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Symbol:     {symbol}")
    print(f"  Price:      ${latest_price:.2f}")
    print(f"  Regime:     {prediction.regime}")
    print(f"  Direction:  {prediction.direction} ({prediction.direction_confidence:.1%})")
    print(f"  Volatility: {prediction.volatility}")
    if combine_with_llm:
        print(f"  Ensemble:   {final_decision} (score: {ensemble_score:+.3f})")
    else:
        print(f"  Signal:     {final_decision}")
    print(f"{'='*60}\n")
    
    return result


class TradeTracker:
    """Tracks trades and calculates performance metrics."""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0  # 0: flat, 1: long, -1: short
        self.entry_price = 0.0
        self.trades: List[Dict] = []
        self.equity_curve = [initial_balance]
        self.returns: List[float] = []
        
    def enter_trade(self, direction: int, price: float, timestamp: str, confidence: float) -> None:
        """Enter a new trade."""
        if self.position != 0:
            self.exit_trade(price, timestamp, "Switching position")
            
        self.position = direction
        self.entry_price = price
        self.trades.append({
            'entry_time': timestamp,
            'entry_price': price,
            'direction': direction,
            'confidence': confidence,
            'exit_time': None,
            'exit_price': None,
            'pnl': None,
            'return_pct': None,
            'exit_reason': None
        })
    
    def exit_trade(self, price: float, timestamp: str, reason: str = "Exit signal") -> Optional[Dict]:
        """Exit the current trade if any."""
        if self.position == 0:
            return None
            
        # Calculate P&L
        if self.position == 1:  # Long
            pnl = price - self.entry_price
        else:  # Short
            pnl = self.entry_price - price
            
        return_pct = pnl / self.entry_price
        
        # Update trade record
        if self.trades and self.trades[-1]['exit_time'] is None:
            trade = self.trades[-1]
            trade.update({
                'exit_time': timestamp,
                'exit_price': price,
                'pnl': pnl,
                'return_pct': return_pct,
                'exit_reason': reason
            })
            
            # Update balance and equity curve
            self.balance += pnl
            self.equity_curve.append(self.balance)
            self.returns.append(return_pct)
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            
            return trade
        return None
    
    def get_performance_metrics(self) -> Dict:
        """Calculate and return performance metrics."""
        if not self.returns:
            return {}
            
        return calculate_metrics(
            returns=self.returns,
            equity_curve=self.equity_curve,
            trades=[t for t in self.trades if t.get('exit_time') is not None]
        )


def run_confidence_trading_loop(
    symbol: str = "ES=F",
    interval: str = "5m",
    delay: int = 300,
    initial_balance: float = 10000.0,
    position_size: float = 0.1,  # 10% of balance per trade
    risk_free_rate: float = 0.05,  # 5% annual risk-free rate
    combine_with_llm: bool = True,
    device: str = "auto",
) -> None:
    """
    Run a trading loop that uses confidence scores for trading decisions.
    
    Strategy:
    - Go LONG when confidence is 80-100
    - Go SHORT when confidence is 0-20
    - Exit positions when confidence returns to 20-80
    
    Args:
        symbol: Trading symbol (e.g., 'ES=F', 'BTC-USD')
        interval: Data interval (e.g., '1m', '5m', '1h')
        delay: Seconds between iterations
        initial_balance: Starting capital
        position_size: Fraction of balance per trade
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        combine_with_llm: Whether to ensemble with LLM analysis
        device: Compute device for ConvNeXt
    """
    if not _CONVNEXT_AVAILABLE:
        raise ImportError(
            "ConvNeXt requires PyTorch. Install with: pip install torch torchvision"
        )
    
    from brainnet.agents import ConvNeXtPredictor
    
    config = load_config()
    
    # Initialize memory
    try:
        memory = MemoryManager(config)
        print("✓ Memory initialized")
    except Exception as e:
        print(f"⚠ Memory failed: {e}")
        memory = None
    
    # Initialize agents
    research = ResearchAgent()
    convnext = ConvNeXtPredictor(device=device)
    reasoning = ReasoningAgent() if combine_with_llm else None
    
    print(f"✓ ConvNeXt initialized on {convnext.device}")
    print(f"✓ Agents ready")
    
    iteration = 0
    
    while True:
        iteration += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*50}")
        print(f"Iteration {iteration} | {ts}")
        
        try:
            # Fetch data
            print(f"\n[1/4] Fetching {symbol} {interval} data...")
            data = yf.download(symbol, period="1d", interval=interval, progress=False)
            
            if data.empty:
                print("⚠ No data")
                time.sleep(60)
                continue
            
            # Handle multi-index
            try:
                latest = float(data['Close'].iloc[-1].iloc[0]) if hasattr(data['Close'].iloc[-1], 'iloc') else float(data['Close'].iloc[-1])
            except Exception:
                latest = float(data['Close'].iloc[-1])
            
            print(f"    {len(data)} bars, latest: ${latest:.2f}")
            
            # Generate GAF
            print(f"\n[2/4] Generating 3-channel GAF...")
            close = data['Close'].values.flatten()[-100:]
            gaf_rgb = research.generate_gaf_3channel(close)
            
            # ConvNeXt prediction
            print(f"\n[3/4] ConvNeXt inference...")
            start = time.perf_counter()
            prediction = convnext.predict(gaf_rgb)
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            print(f"    {prediction.regime} | {prediction.direction} | {prediction.volatility}")
            print(f"    Inference: {elapsed_ms:.1f}ms")
            
            # Ensemble with LLM if enabled
            if combine_with_llm and reasoning:
                memory_context = ""
                if memory:
                    memory_context = memory.get_context("recent analysis")
                
                llm_analysis = research.research(data, memory_context)
                confidence = reasoning.compute_confidence(llm_analysis['analysis'])
                
                # Ensemble logic
                dir_scores = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
                trend_sign = 1.0 if llm_analysis['features']['trend_score'] > 0 else -1.0
                
                total_weight = prediction.direction_confidence + confidence + 1e-8
                ensemble_score = (
                    dir_scores[prediction.direction] * prediction.direction_confidence +
                    trend_sign * confidence
                ) / total_weight
                
                if ensemble_score > 0.2:
                    decision, emoji = "LONG", "📈"
                elif ensemble_score < -0.2:
                    decision, emoji = "SHORT", "📉"
                else:
                    decision, emoji = "FLAT", "⏸"
                
                print(f"\n[4/4] Ensemble: {emoji} {decision} (score: {ensemble_score:+.3f})")
            else:
                # ConvNeXt-only decision
                if prediction.direction == "bullish" and prediction.direction_confidence > 0.5:
                    decision, emoji = "LONG", "📈"
                elif prediction.direction == "bearish" and prediction.direction_confidence > 0.5:
                    decision, emoji = "SHORT", "📉"
                else:
                    decision, emoji = "FLAT", "⏸"
                
                print(f"\n[4/4] Decision: {emoji} {decision}")
            
            # Store in memory
            if memory:
                memory.add({
                    "timestamp": ts,
                    "symbol": symbol,
                    "decision": decision,
                    "convnext_regime": prediction.regime,
                    "convnext_direction": prediction.direction,
                    "convnext_confidence": prediction.direction_confidence,
                })
                print("    ✓ Stored")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        print(f"\nSleeping {delay}s...")
        time.sleep(delay)
