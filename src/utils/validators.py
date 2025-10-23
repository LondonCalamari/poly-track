"""Input validators and data validators for EdgeCopy v1"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import re


class Validators:
    """Collection of validation functions"""

    @staticmethod
    def validate_wallet_address(address: str) -> bool:
        """
        Validate Ethereum wallet address

        Args:
            address: Wallet address to validate

        Returns:
            True if valid, False otherwise
        """
        if not address:
            return False

        # Check if it starts with 0x and is 42 characters long
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return False

        return True

    @staticmethod
    def validate_pnl(pnl: float, min_pnl: float = 30.0) -> bool:
        """
        Validate PnL meets minimum threshold

        Args:
            pnl: PnL percentage
            min_pnl: Minimum required PnL

        Returns:
            True if valid, False otherwise
        """
        return pnl >= min_pnl

    @staticmethod
    def validate_win_rate(win_rate: float, min_win_rate: float = 60.0) -> bool:
        """
        Validate win rate meets minimum threshold

        Args:
            win_rate: Win rate percentage (0-100)
            min_win_rate: Minimum required win rate

        Returns:
            True if valid, False otherwise
        """
        return 0 <= win_rate <= 100 and win_rate >= min_win_rate

    @staticmethod
    def validate_bet_size(bet_size: float, min_bet_size: float = 10000.0) -> bool:
        """
        Validate bet size meets minimum threshold

        Args:
            bet_size: Bet size in USD
            min_bet_size: Minimum required bet size

        Returns:
            True if valid, False otherwise
        """
        return bet_size >= min_bet_size

    @staticmethod
    def validate_liquidity(liquidity: float, min_liquidity: float = 300000.0) -> bool:
        """
        Validate market liquidity meets minimum threshold

        Args:
            liquidity: Market liquidity in USD
            min_liquidity: Minimum required liquidity

        Returns:
            True if valid, False otherwise
        """
        return liquidity >= min_liquidity

    @staticmethod
    def validate_timing_window(
        bet_timestamp: datetime,
        event_timestamp: datetime,
        min_hours: int = 1,
        max_hours: int = 5
    ) -> bool:
        """
        Validate bet is within timing window before event

        Args:
            bet_timestamp: When bet was placed
            event_timestamp: When event occurs
            min_hours: Minimum hours before event
            max_hours: Maximum hours before event

        Returns:
            True if valid, False otherwise
        """
        time_diff = event_timestamp - bet_timestamp
        hours_before = time_diff.total_seconds() / 3600

        return min_hours <= hours_before <= max_hours

    @staticmethod
    def validate_sync_window(
        timestamps: List[datetime],
        max_minutes: int = 30
    ) -> bool:
        """
        Validate that bets are synchronized within time window

        Args:
            timestamps: List of bet timestamps
            max_minutes: Maximum minutes between first and last bet

        Returns:
            True if all bets within window, False otherwise
        """
        if not timestamps or len(timestamps) < 2:
            return True

        sorted_times = sorted(timestamps)
        time_diff = sorted_times[-1] - sorted_times[0]

        return time_diff.total_seconds() / 60 <= max_minutes

    @staticmethod
    def validate_wallet_age(
        wallet_created: datetime,
        max_age_days: int = 30
    ) -> bool:
        """
        Validate wallet age for activity tracking

        Args:
            wallet_created: When wallet was created/first active
            max_age_days: Maximum age to consider active

        Returns:
            True if within age limit, False otherwise
        """
        age = datetime.now() - wallet_created
        return age.days <= max_age_days

    @staticmethod
    def detect_new_wallet(
        wallet_created: datetime,
        markets_count: int,
        max_age_days: int = 1,
        max_markets: int = 3
    ) -> bool:
        """
        Detect potential event-based insider (new wallet pattern)

        Args:
            wallet_created: When wallet was created
            markets_count: Number of markets wallet has bet on
            max_age_days: Maximum age to flag as new
            max_markets: Maximum markets to flag as focused

        Returns:
            True if matches new wallet pattern, False otherwise
        """
        age = datetime.now() - wallet_created
        is_new = age.days <= max_age_days
        is_focused = markets_count <= max_markets

        return is_new and is_focused

    @staticmethod
    def calculate_perfect_bet_score(
        liquidity: float,
        smart_wallet_count: int,
        is_consolidation: bool,
        wallet_confirmed: bool,
        is_pre_news: bool,
        risk_percent: float
    ) -> Dict[str, Any]:
        """
        Calculate Perfect Bet Checklist score

        Args:
            liquidity: Market liquidity
            smart_wallet_count: Number of smart wallets
            is_consolidation: Whether in consolidation phase
            wallet_confirmed: Whether wallet history confirmed
            is_pre_news: Whether in pre-news window
            risk_percent: Position risk percentage

        Returns:
            Dict with score and details
        """
        checks = {
            'high_liquidity': liquidity > 500000,
            'consolidation_entry': is_consolidation,
            'confirmed_wallet': wallet_confirmed,
            'pre_news_timing': is_pre_news,
            'multi_wallet_sync': 2 <= smart_wallet_count <= 3,
            'low_risk': risk_percent < 15
        }

        score = sum(checks.values())

        return {
            'score': score,
            'max_score': 6,
            'is_perfect': score >= 5,
            'checks': checks
        }

    @staticmethod
    def detect_red_flags(
        new_wallet_count: int,
        liquidity: float,
        bet_time_spread_minutes: float,
        is_obvious_outcome: bool
    ) -> Dict[str, bool]:
        """
        Detect red flags in signal

        Args:
            new_wallet_count: Count of new wallets in signal
            liquidity: Market liquidity
            bet_time_spread_minutes: Time spread of bets
            is_obvious_outcome: Whether betting against obvious fact

        Returns:
            Dict of red flags
        """
        return {
            'fake_cluster': new_wallet_count > 3,
            'low_liquidity': liquidity < 300000,
            'poor_synchronization': bet_time_spread_minutes > 30,
            'obvious_anomaly': is_obvious_outcome
        }
