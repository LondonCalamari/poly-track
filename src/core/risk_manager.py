"""Risk management module for EdgeCopy v1"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logger import Logger


class RiskManager:
    """
    Risk management and position tracking

    Implements:
    - Position sizing (max 15% risk)
    - Profit taking (10-15% increments)
    - Stop loss management
    - Never average down rule
    - Pre-news position closing
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize risk manager

        Args:
            config: Configuration dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        risk_config = config.get('risk_management', {})
        self.max_position_risk = risk_config.get('max_position_risk_percent', 15)
        self.profit_increments = risk_config.get('profit_take_increments', [0.1, 0.15])
        self.never_average_down = risk_config.get('never_average_down', True)
        self.close_before_news = risk_config.get('close_before_major_news', True)

    def calculate_position_size(
        self,
        total_capital: float,
        entry_price: float,
        risk_percent: float = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size

        Args:
            total_capital: Total available capital
            entry_price: Entry price/odds
            risk_percent: Custom risk percent (default: from config)

        Returns:
            Position sizing recommendation
        """
        risk_percent = risk_percent or self.max_position_risk

        # Calculate position size
        max_risk_amount = total_capital * (risk_percent / 100)
        position_size = max_risk_amount / (1 - entry_price)  # Adjusted for odds

        # Calculate return metrics
        potential_profit = position_size * entry_price
        potential_loss = max_risk_amount

        return {
            'position_size': round(position_size, 2),
            'risk_amount': round(max_risk_amount, 2),
            'risk_percent': risk_percent,
            'potential_profit': round(potential_profit, 2),
            'potential_loss': round(potential_loss, 2),
            'risk_reward_ratio': round(potential_profit / potential_loss, 2) if potential_loss > 0 else 0,
            'entry_price': entry_price
        }

    def calculate_profit_targets(
        self,
        entry_price: float,
        position_size: float
    ) -> List[Dict[str, Any]]:
        """
        Calculate profit taking targets

        Args:
            entry_price: Entry price/odds
            position_size: Position size

        Returns:
            List of profit targets
        """
        targets = []

        for increment in self.profit_increments:
            target_price = entry_price * (1 + increment)
            target_price = min(target_price, 0.99)  # Cap at 99%

            profit_amount = position_size * (target_price - entry_price)
            profit_percent = (target_price - entry_price) / entry_price * 100

            targets.append({
                'target_price': round(target_price, 3),
                'profit_amount': round(profit_amount, 2),
                'profit_percent': round(profit_percent, 2),
                'exit_percent': int(increment * 100)  # % of position to exit
            })

        return targets

    def calculate_stop_loss(
        self,
        entry_price: float,
        max_loss_percent: float = 50
    ) -> Dict[str, Any]:
        """
        Calculate stop loss level

        Args:
            entry_price: Entry price/odds
            max_loss_percent: Maximum acceptable loss percentage

        Returns:
            Stop loss recommendation
        """
        stop_price = entry_price * (1 - max_loss_percent / 100)
        stop_price = max(stop_price, 0.01)  # Floor at 1%

        return {
            'stop_price': round(stop_price, 3),
            'max_loss_percent': max_loss_percent,
            'trigger_price': round(stop_price * 1.01, 3)  # Alert slightly before
        }

    def validate_entry(
        self,
        total_capital: float,
        current_positions: List[Dict[str, Any]],
        new_position_size: float
    ) -> Dict[str, Any]:
        """
        Validate if new entry is safe

        Args:
            total_capital: Total capital
            current_positions: List of current positions
            new_position_size: Proposed new position size

        Returns:
            Validation result
        """
        # Calculate total exposure
        current_exposure = sum(p.get('size', 0) for p in current_positions)
        new_total_exposure = current_exposure + new_position_size
        exposure_percent = (new_total_exposure / total_capital) * 100

        is_valid = exposure_percent <= 100  # Don't over-leverage

        return {
            'is_valid': is_valid,
            'current_exposure': round(current_exposure, 2),
            'new_total_exposure': round(new_total_exposure, 2),
            'exposure_percent': round(exposure_percent, 2),
            'max_allowed': 100,
            'warnings': [] if is_valid else ['Total exposure exceeds 100% of capital']
        }

    def should_close_position(
        self,
        entry_price: float,
        current_price: float,
        hours_held: float,
        is_major_news_coming: bool = False
    ) -> Dict[str, Any]:
        """
        Determine if position should be closed

        Args:
            entry_price: Entry price
            current_price: Current price
            hours_held: Hours position has been held
            is_major_news_coming: Whether major news event is coming

        Returns:
            Close recommendation
        """
        # Calculate current P&L
        pnl_percent = ((current_price - entry_price) / entry_price) * 100

        should_close = False
        reasons = []

        # 1. Major news event coming
        if is_major_news_coming and self.close_before_news:
            should_close = True
            reasons.append("Major news event approaching - close to avoid uncertainty")

        # 2. Large profit hit
        if pnl_percent >= (self.profit_increments[0] * 100):
            should_close = True
            reasons.append(f"Profit target reached: {pnl_percent:.1f}%")

        # 3. Position held too long (>48 hours)
        if hours_held > 48:
            should_close = True
            reasons.append(f"Position held too long: {hours_held:.1f} hours")

        # 4. Large loss
        if pnl_percent <= -30:
            should_close = True
            reasons.append(f"Stop loss triggered: {pnl_percent:.1f}%")

        return {
            'should_close': should_close,
            'reasons': reasons,
            'current_pnl_percent': round(pnl_percent, 2),
            'hours_held': round(hours_held, 2),
            'action': 'CLOSE' if should_close else 'HOLD'
        }

    def check_averaging_down(
        self,
        existing_position: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Check if attempting to average down (not allowed)

        Args:
            existing_position: Existing position data
            current_price: Current market price

        Returns:
            Averaging down check result
        """
        entry_price = existing_position.get('entry_price', 0)
        is_losing = current_price < entry_price

        is_averaging_down = is_losing and self.never_average_down

        return {
            'is_averaging_down': is_averaging_down,
            'is_allowed': not is_averaging_down,
            'warning': (
                "Adding to losing position (averaging down) is not allowed per risk rules"
                if is_averaging_down else None
            ),
            'current_pnl_percent': round(((current_price - entry_price) / entry_price) * 100, 2)
        }

    def generate_trade_plan(
        self,
        signal: Dict[str, Any],
        total_capital: float,
        current_positions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete trade plan for signal

        Args:
            signal: Signal data
            total_capital: Total available capital
            current_positions: Current positions list

        Returns:
            Complete trade plan
        """
        current_positions = current_positions or []

        entry_price = signal.get('current_odds', 0.5)

        # Position sizing
        position = self.calculate_position_size(total_capital, entry_price)

        # Validate entry
        validation = self.validate_entry(
            total_capital,
            current_positions,
            position['position_size']
        )

        # Profit targets
        profit_targets = self.calculate_profit_targets(
            entry_price,
            position['position_size']
        )

        # Stop loss
        stop_loss = self.calculate_stop_loss(entry_price)

        return {
            'signal_id': signal.get('signal_id'),
            'market_title': signal.get('market_title'),
            'entry_price': entry_price,
            'position_sizing': position,
            'profit_targets': profit_targets,
            'stop_loss': stop_loss,
            'entry_validation': validation,
            'risk_warnings': validation.get('warnings', []),
            'recommended_action': 'ENTER' if validation['is_valid'] else 'PASS',
            'notes': [
                f"Risk: {position['risk_percent']}% of capital",
                f"R:R Ratio: {position['risk_reward_ratio']}:1",
                "Take profits at targets incrementally",
                "Never average down if position moves against you",
                "Close before major uncertain news events"
            ]
        }

    def track_position_performance(
        self,
        entry_price: float,
        current_price: float,
        position_size: float,
        entry_time: datetime
    ) -> Dict[str, Any]:
        """
        Track position performance metrics

        Args:
            entry_price: Entry price
            current_price: Current price
            position_size: Position size
            entry_time: Entry timestamp

        Returns:
            Performance metrics
        """
        # Calculate P&L
        pnl_amount = position_size * (current_price - entry_price)
        pnl_percent = ((current_price - entry_price) / entry_price) * 100

        # Time held
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600

        # Determine status
        if pnl_percent > 10:
            status = "WINNING"
        elif pnl_percent < -10:
            status = "LOSING"
        else:
            status = "NEUTRAL"

        return {
            'entry_price': entry_price,
            'current_price': current_price,
            'position_size': position_size,
            'pnl_amount': round(pnl_amount, 2),
            'pnl_percent': round(pnl_percent, 2),
            'hours_held': round(hours_held, 2),
            'status': status,
            'entry_time': entry_time,
            'current_time': datetime.now()
        }
