#!/usr/bin/env python3
"""
TrendMonster Strategy - Live Signal Generator
==============================================

This module contains the core trading logic for the TrendMonster strategy.
It is designed to be integrated into a live dashboard or trading system.

STRATEGY OVERVIEW
-----------------
TrendMonster is a tactical allocation strategy that dynamically rotates between
SPY (S&P 500 ETF), TQQQ (3x Leveraged Nasdaq ETF), and Cash based on:

1. TREND FILTER (Weekly): Price vs 50-Week SMA
   - Uptrend: SPY weekly close > 50-week SMA → Equities allowed
   - Downtrend: SPY weekly close < 50-week SMA → 100% Cash

2. VOLATILITY ALLOCATION (Daily): VIX/VIX3M Ratio
   - Determines SPY/TQQQ mix when in uptrend
   - Lower ratio = more leverage (TQQQ)
   - Higher ratio = less leverage (SPY)

DATA REQUIREMENTS
-----------------
1. SPY Weekly Close - End of week (Friday 4:00 PM ET)
2. SPY 50-Week SMA - Calculated from weekly closes
3. VIX Daily Close - Previous day's close (4:15 PM ET)
4. VIX3M Daily Close - Previous day's close (4:15 PM ET)

SIGNAL TIMING
-------------
- Weekly signals: Evaluated after Friday close, executed Monday open
- Daily signals: Evaluated after market close, executed next day open
- No intraday signal changes

Author: TrendMonster Strategy
Version: 2.1
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional
from datetime import datetime


# ============================================================================
# STRATEGY PARAMETERS
# ============================================================================

class StrategyParams:
    """
    Core strategy parameters.
    Modify these to adjust strategy behavior.
    """
    # Trend filter
    SMA_WEEKS = 50  # 50-week simple moving average
    
    # VIX ratio thresholds (determines allocation buckets)
    VIX_VERY_LOW = 0.80    # Below: Maximum leverage
    VIX_LOW = 0.90         # Below: High leverage
    VIX_MODERATE = 0.95    # Below: Balanced
    VIX_ELEVATED = 1.05    # Below: Defensive
    # Above VIX_ELEVATED: Very defensive


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class Trend(Enum):
    """Market trend state based on weekly close vs 50-week SMA."""
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"


class Posture(Enum):
    """Strategy posture based on VIX ratio."""
    CASH = "CASH"              # Downtrend - no equity exposure
    AGGRESSIVE = "AGGRESSIVE"  # VIX ratio < 0.90
    BALANCED = "BALANCED"      # VIX ratio 0.90 - 1.05
    DEFENSIVE = "DEFENSIVE"    # VIX ratio > 1.05


class VIXLevel(Enum):
    """VIX ratio classification."""
    VERY_LOW = "VERY_LOW"      # < 0.80
    LOW = "LOW"                # 0.80 - 0.90
    MODERATE = "MODERATE"      # 0.90 - 0.95
    ELEVATED = "ELEVATED"      # 0.95 - 1.05
    HIGH = "HIGH"              # > 1.05


@dataclass
class Allocation:
    """Target portfolio allocation."""
    spy_weight: float      # SPY allocation (0.0 to 1.0)
    tqqq_weight: float     # TQQQ allocation (0.0 to 1.0)
    cash_weight: float     # Cash allocation (0.0 to 1.0)
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.spy_weight + self.tqqq_weight + self.cash_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def as_percentages(self) -> Tuple[float, float, float]:
        """Return allocations as percentages (0-100)."""
        return (
            self.spy_weight * 100,
            self.tqqq_weight * 100,
            self.cash_weight * 100
        )
    
    def __str__(self) -> str:
        spy, tqqq, cash = self.as_percentages()
        return f"SPY: {spy:.0f}% | TQQQ: {tqqq:.0f}% | Cash: {cash:.0f}%"


@dataclass
class MarketData:
    """
    Required market data inputs.
    
    All values should be from CONFIRMED closes only:
    - Weekly data: Previous Friday's close
    - Daily data: Previous day's close
    """
    # Weekly data (from last Friday's close)
    spy_weekly_close: float
    spy_50week_sma: float
    
    # Daily data (from yesterday's close)
    vix_close: float
    vix3m_close: float
    
    # Metadata
    weekly_as_of: Optional[datetime] = None  # Date of weekly close
    daily_as_of: Optional[datetime] = None   # Date of daily close
    
    @property
    def vix_ratio(self) -> float:
        """Calculate VIX/VIX3M ratio."""
        if self.vix3m_close == 0:
            raise ValueError("VIX3M cannot be zero")
        return self.vix_close / self.vix3m_close


@dataclass
class Signal:
    """
    Complete strategy signal output.
    
    This is the primary output for dashboard display and trade execution.
    """
    # Current state
    trend: Trend
    posture: Posture
    vix_level: VIXLevel
    
    # Target allocation
    allocation: Allocation
    
    # Raw values (for display)
    vix_ratio: float
    spy_close: float
    spy_sma: float
    
    # Rebalancing
    rebalance_required: bool
    rebalance_instructions: str
    
    # Timestamps
    signal_generated_at: datetime
    weekly_data_as_of: Optional[datetime]
    daily_data_as_of: Optional[datetime]
    
    def to_dict(self) -> dict:
        """Convert signal to dictionary for JSON serialization."""
        spy_pct, tqqq_pct, cash_pct = self.allocation.as_percentages()
        return {
            "trend": self.trend.value,
            "posture": self.posture.value,
            "vix_level": self.vix_level.value,
            "allocation": {
                "spy": spy_pct,
                "tqqq": tqqq_pct,
                "cash": cash_pct
            },
            "indicators": {
                "vix_ratio": round(self.vix_ratio, 4),
                "spy_close": round(self.spy_close, 2),
                "spy_sma": round(self.spy_sma, 2)
            },
            "rebalance_required": self.rebalance_required,
            "rebalance_instructions": self.rebalance_instructions,
            "timestamps": {
                "signal_generated": self.signal_generated_at.isoformat(),
                "weekly_data_as_of": self.weekly_data_as_of.isoformat() if self.weekly_data_as_of else None,
                "daily_data_as_of": self.daily_data_as_of.isoformat() if self.daily_data_as_of else None
            }
        }


# ============================================================================
# CORE SIGNAL LOGIC
# ============================================================================

def determine_trend(spy_close: float, spy_sma: float) -> Trend:
    """
    Determine market trend based on weekly close vs 50-week SMA.
    
    Args:
        spy_close: SPY weekly closing price (Friday close)
        spy_sma: 50-week simple moving average
    
    Returns:
        Trend.UPTREND if price > SMA, else Trend.DOWNTREND
    """
    return Trend.UPTREND if spy_close > spy_sma else Trend.DOWNTREND


def classify_vix_level(vix_ratio: float) -> VIXLevel:
    """
    Classify VIX ratio into volatility level.
    
    Args:
        vix_ratio: VIX / VIX3M ratio
    
    Returns:
        VIXLevel enum value
    """
    if vix_ratio < StrategyParams.VIX_VERY_LOW:
        return VIXLevel.VERY_LOW
    elif vix_ratio < StrategyParams.VIX_LOW:
        return VIXLevel.LOW
    elif vix_ratio < StrategyParams.VIX_MODERATE:
        return VIXLevel.MODERATE
    elif vix_ratio < StrategyParams.VIX_ELEVATED:
        return VIXLevel.ELEVATED
    else:
        return VIXLevel.HIGH


def determine_posture(trend: Trend, vix_ratio: float) -> Posture:
    """
    Determine strategy posture based on trend and VIX ratio.
    
    Args:
        trend: Current market trend
        vix_ratio: VIX / VIX3M ratio
    
    Returns:
        Posture enum value
    """
    if trend == Trend.DOWNTREND:
        return Posture.CASH
    
    # Uptrend - determine posture from VIX ratio
    if vix_ratio < StrategyParams.VIX_LOW:
        return Posture.AGGRESSIVE
    elif vix_ratio > StrategyParams.VIX_ELEVATED:
        return Posture.DEFENSIVE
    else:
        return Posture.BALANCED


def calculate_allocation(trend: Trend, vix_ratio: float) -> Allocation:
    """
    Calculate target allocation based on trend and VIX ratio.
    
    ALLOCATION TABLE:
    -----------------
    Downtrend (any VIX):     0% SPY /  0% TQQQ / 100% Cash
    
    Uptrend:
      VIX Ratio < 0.80:     30% SPY / 70% TQQQ /   0% Cash
      VIX Ratio 0.80-0.90:  50% SPY / 50% TQQQ /   0% Cash
      VIX Ratio 0.90-0.95:  60% SPY / 40% TQQQ /   0% Cash
      VIX Ratio 0.95-1.05:  75% SPY / 25% TQQQ /   0% Cash
      VIX Ratio > 1.05:     85% SPY / 15% TQQQ /   0% Cash
    
    Args:
        trend: Current market trend
        vix_ratio: VIX / VIX3M ratio
    
    Returns:
        Allocation object with SPY, TQQQ, and Cash weights
    """
    # Downtrend - 100% cash
    if trend == Trend.DOWNTREND:
        return Allocation(spy_weight=0.0, tqqq_weight=0.0, cash_weight=1.0)
    
    # Uptrend - allocate based on VIX ratio
    if vix_ratio < StrategyParams.VIX_VERY_LOW:
        return Allocation(spy_weight=0.30, tqqq_weight=0.70, cash_weight=0.0)
    
    elif vix_ratio < StrategyParams.VIX_LOW:
        return Allocation(spy_weight=0.50, tqqq_weight=0.50, cash_weight=0.0)
    
    elif vix_ratio < StrategyParams.VIX_MODERATE:
        return Allocation(spy_weight=0.60, tqqq_weight=0.40, cash_weight=0.0)
    
    elif vix_ratio < StrategyParams.VIX_ELEVATED:
        return Allocation(spy_weight=0.75, tqqq_weight=0.25, cash_weight=0.0)
    
    else:
        return Allocation(spy_weight=0.85, tqqq_weight=0.15, cash_weight=0.0)


def generate_rebalance_instructions(
    current_allocation: Allocation,
    target_allocation: Allocation
) -> Tuple[bool, str]:
    """
    Generate rebalancing instructions by comparing current vs target allocation.
    
    Args:
        current_allocation: Current portfolio allocation
        target_allocation: Target allocation from signal
    
    Returns:
        Tuple of (rebalance_required: bool, instructions: str)
    """
    spy_change = target_allocation.spy_weight - current_allocation.spy_weight
    tqqq_change = target_allocation.tqqq_weight - current_allocation.tqqq_weight
    cash_change = target_allocation.cash_weight - current_allocation.cash_weight
    
    # Check if rebalance needed (threshold: 0.1%)
    threshold = 0.001
    if (abs(spy_change) < threshold and 
        abs(tqqq_change) < threshold and 
        abs(cash_change) < threshold):
        return False, "No rebalance required. Current allocation is optimal."
    
    # Build instructions
    instructions = []
    
    if abs(spy_change) >= threshold:
        action = "BUY" if spy_change > 0 else "SELL"
        instructions.append(f"{action} {abs(spy_change)*100:.1f}% SPY")
    
    if abs(tqqq_change) >= threshold:
        action = "BUY" if tqqq_change > 0 else "SELL"
        instructions.append(f"{action} {abs(tqqq_change)*100:.1f}% TQQQ")
    
    if abs(cash_change) >= threshold:
        if cash_change > 0:
            instructions.append(f"Move {abs(cash_change)*100:.1f}% to Cash")
        else:
            instructions.append(f"Deploy {abs(cash_change)*100:.1f}% from Cash")
    
    instruction_text = "Execute at next market open: " + " | ".join(instructions)
    
    return True, instruction_text


# ============================================================================
# MAIN SIGNAL GENERATOR
# ============================================================================

class TrendMonsterSignal:
    """
    Main signal generator class.
    
    Usage:
        generator = TrendMonsterSignal()
        
        # Set current allocation (from your portfolio tracking)
        generator.set_current_allocation(spy=0.75, tqqq=0.25, cash=0.0)
        
        # Generate signal with latest market data
        signal = generator.generate(
            spy_weekly_close=450.00,
            spy_50week_sma=420.00,
            vix_close=15.50,
            vix3m_close=18.20
        )
        
        # Access signal data
        print(signal.trend)
        print(signal.allocation)
        print(signal.rebalance_instructions)
    """
    
    def __init__(self):
        """Initialize signal generator."""
        self._current_allocation: Optional[Allocation] = None
    
    def set_current_allocation(
        self,
        spy: float,
        tqqq: float,
        cash: float
    ) -> None:
        """
        Set current portfolio allocation for rebalance calculations.
        
        Args:
            spy: Current SPY weight (0.0 to 1.0)
            tqqq: Current TQQQ weight (0.0 to 1.0)
            cash: Current cash weight (0.0 to 1.0)
        """
        self._current_allocation = Allocation(
            spy_weight=spy,
            tqqq_weight=tqqq,
            cash_weight=cash
        )
    
    def generate(
        self,
        spy_weekly_close: float,
        spy_50week_sma: float,
        vix_close: float,
        vix3m_close: float,
        weekly_as_of: Optional[datetime] = None,
        daily_as_of: Optional[datetime] = None
    ) -> Signal:
        """
        Generate trading signal from market data.
        
        Args:
            spy_weekly_close: SPY price at last weekly close (Friday 4 PM ET)
            spy_50week_sma: 50-week SMA of SPY (calculated from weekly closes)
            vix_close: VIX index at last daily close (4:15 PM ET)
            vix3m_close: VIX3M index at last daily close (4:15 PM ET)
            weekly_as_of: Date of weekly close (optional, for logging)
            daily_as_of: Date of daily close (optional, for logging)
        
        Returns:
            Signal object containing all strategy outputs
        """
        # Calculate VIX ratio
        vix_ratio = vix_close / vix3m_close
        
        # Determine trend (from weekly data)
        trend = determine_trend(spy_weekly_close, spy_50week_sma)
        
        # Classify VIX level
        vix_level = classify_vix_level(vix_ratio)
        
        # Determine posture
        posture = determine_posture(trend, vix_ratio)
        
        # Calculate target allocation
        target_allocation = calculate_allocation(trend, vix_ratio)
        
        # Generate rebalance instructions
        if self._current_allocation is not None:
            rebalance_required, instructions = generate_rebalance_instructions(
                self._current_allocation,
                target_allocation
            )
        else:
            rebalance_required = True
            instructions = "Set current allocation to enable rebalance instructions."
        
        # Build signal
        signal = Signal(
            trend=trend,
            posture=posture,
            vix_level=vix_level,
            allocation=target_allocation,
            vix_ratio=vix_ratio,
            spy_close=spy_weekly_close,
            spy_sma=spy_50week_sma,
            rebalance_required=rebalance_required,
            rebalance_instructions=instructions,
            signal_generated_at=datetime.now(),
            weekly_data_as_of=weekly_as_of,
            daily_data_as_of=daily_as_of
        )
        
        return signal
    
    def generate_from_data(self, data: MarketData) -> Signal:
        """
        Generate signal from MarketData object.
        
        Args:
            data: MarketData object with all required inputs
        
        Returns:
            Signal object
        """
        return self.generate(
            spy_weekly_close=data.spy_weekly_close,
            spy_50week_sma=data.spy_50week_sma,
            vix_close=data.vix_close,
            vix3m_close=data.vix3m_close,
            weekly_as_of=data.weekly_as_of,
            daily_as_of=data.daily_as_of
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_signal(
    spy_weekly_close: float,
    spy_50week_sma: float,
    vix_close: float,
    vix3m_close: float
) -> dict:
    """
    Simple function to get signal as dictionary.
    
    This is a convenience wrapper for quick integration.
    
    Args:
        spy_weekly_close: SPY Friday close
        spy_50week_sma: 50-week SMA
        vix_close: Previous VIX close
        vix3m_close: Previous VIX3M close
    
    Returns:
        Dictionary with signal data
    
    Example:
        signal = get_signal(
            spy_weekly_close=450.00,
            spy_50week_sma=420.00,
            vix_close=15.50,
            vix3m_close=18.20
        )
        print(signal['allocation'])  # {'spy': 75.0, 'tqqq': 25.0, 'cash': 0.0}
    """
    generator = TrendMonsterSignal()
    signal = generator.generate(
        spy_weekly_close=spy_weekly_close,
        spy_50week_sma=spy_50week_sma,
        vix_close=vix_close,
        vix3m_close=vix3m_close
    )
    return signal.to_dict()


def get_allocation_only(
    spy_weekly_close: float,
    spy_50week_sma: float,
    vix_close: float,
    vix3m_close: float
) -> Tuple[float, float, float]:
    """
    Get just the allocation percentages.
    
    Args:
        spy_weekly_close: SPY Friday close
        spy_50week_sma: 50-week SMA
        vix_close: Previous VIX close
        vix3m_close: Previous VIX3M close
    
    Returns:
        Tuple of (spy_pct, tqqq_pct, cash_pct) as percentages 0-100
    
    Example:
        spy, tqqq, cash = get_allocation_only(450.0, 420.0, 15.5, 18.2)
        print(f"SPY: {spy}%, TQQQ: {tqqq}%, Cash: {cash}%")
    """
    vix_ratio = vix_close / vix3m_close
    trend = determine_trend(spy_weekly_close, spy_50week_sma)
    allocation = calculate_allocation(trend, vix_ratio)
    return allocation.as_percentages()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the signal generator.
    """
    print("=" * 60)
    print("TrendMonster Signal Generator - Example")
    print("=" * 60)
    
    # Example market data
    spy_weekly_close = 595.00   # SPY Friday close
    spy_50week_sma = 540.00     # 50-week SMA
    vix_close = 14.50           # Yesterday's VIX close
    vix3m_close = 17.80         # Yesterday's VIX3M close
    
    print(f"\nInput Data:")
    print(f"  SPY Weekly Close: ${spy_weekly_close:.2f}")
    print(f"  SPY 50-Week SMA:  ${spy_50week_sma:.2f}")
    print(f"  VIX Close:        {vix_close:.2f}")
    print(f"  VIX3M Close:      {vix3m_close:.2f}")
    print(f"  VIX Ratio:        {vix_close/vix3m_close:.4f}")
    
    # Method 1: Simple function
    print(f"\n--- Method 1: Simple Function ---")
    spy_pct, tqqq_pct, cash_pct = get_allocation_only(
        spy_weekly_close, spy_50week_sma, vix_close, vix3m_close
    )
    print(f"  Allocation: SPY {spy_pct:.0f}% | TQQQ {tqqq_pct:.0f}% | Cash {cash_pct:.0f}%")
    
    # Method 2: Full signal object
    print(f"\n--- Method 2: Full Signal Object ---")
    generator = TrendMonsterSignal()
    generator.set_current_allocation(spy=0.60, tqqq=0.40, cash=0.0)
    
    signal = generator.generate(
        spy_weekly_close=spy_weekly_close,
        spy_50week_sma=spy_50week_sma,
        vix_close=vix_close,
        vix3m_close=vix3m_close
    )
    
    print(f"  Trend:      {signal.trend.value}")
    print(f"  Posture:    {signal.posture.value}")
    print(f"  VIX Level:  {signal.vix_level.value}")
    print(f"  Allocation: {signal.allocation}")
    print(f"  Rebalance:  {signal.rebalance_required}")
    print(f"  Action:     {signal.rebalance_instructions}")
    
    # Method 3: JSON output for API
    print(f"\n--- Method 3: JSON Output ---")
    import json
    print(json.dumps(signal.to_dict(), indent=2))
