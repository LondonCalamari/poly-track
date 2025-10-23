"""Market monitoring and liquidity validation for EdgeCopy v1"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..database.models import Market, Bet
from ..database.repository import MarketRepository, BetRepository
from ..utils.validators import Validators
from ..utils.logger import Logger


class MarketMonitor:
    """
    Monitors Polymarket markets for liquidity, timing, and activity

    Validates:
    - Market liquidity thresholds (>$300k minimum)
    - Pre-event timing windows (1-5 hours)
    - Market consolidation phases
    - Trading activity patterns
    """

    def __init__(self, config: dict, market_repo: MarketRepository,
                 bet_repo: BetRepository, logger: Logger):
        """
        Initialize market monitor

        Args:
            config: Configuration dict
            market_repo: Market repository instance
            bet_repo: Bet repository instance
            logger: Logger instance
        """
        self.config = config
        self.market_repo = market_repo
        self.bet_repo = bet_repo
        self.logger = logger
        self.validators = Validators()

        # Signal detection config
        signal_config = config.get('signal_detection', {})
        self.min_liquidity = signal_config.get('min_liquidity', 300000)
        self.pre_event_min_hours = signal_config.get('pre_event_window_hours_min', 1)
        self.pre_event_max_hours = signal_config.get('pre_event_window_hours_max', 5)
        self.sync_window_minutes = signal_config.get('sync_time_window_minutes', 30)

        # Perfect bet config
        perfect_config = config.get('perfect_bet', {})
        self.perfect_min_liquidity = perfect_config.get('min_liquidity', 500000)

    def add_or_update_market(self, market_id: str, market_data: Dict[str, Any]) -> Market:
        """
        Add new market or update existing one

        Args:
            market_id: Polymarket market ID
            market_data: Market data dict

        Returns:
            Market instance
        """
        market = self.market_repo.get_or_create(market_id)

        # Update data
        update_data = {
            'title': market_data.get('title', ''),
            'description': market_data.get('description', ''),
            'category': market_data.get('category', ''),
            'end_date': market_data.get('end_date'),
            'liquidity': market_data.get('liquidity', 0),
            'volume': market_data.get('volume', 0),
            'active_traders': market_data.get('active_traders', 0),
            'current_probability': market_data.get('current_probability'),
            'is_active': market_data.get('is_active', True),
            'is_resolved': market_data.get('is_resolved', False),
            'resolution': market_data.get('resolution'),
            'last_updated': datetime.now()
        }

        # Set opening probability if first time
        if not market.opening_probability and update_data['current_probability']:
            update_data['opening_probability'] = update_data['current_probability']

        for key, value in update_data.items():
            setattr(market, key, value)

        self.market_repo.session.commit()

        return market

    def validate_liquidity(self, market: Market, perfect_bet: bool = False) -> bool:
        """
        Validate market liquidity meets requirements

        Args:
            market: Market instance
            perfect_bet: Whether to use perfect bet criteria

        Returns:
            True if liquidity sufficient, False otherwise
        """
        min_liq = self.perfect_min_liquidity if perfect_bet else self.min_liquidity
        return self.validators.validate_liquidity(market.liquidity, min_liq)

    def validate_timing(self, market: Market, bet_timestamp: datetime = None) -> Dict[str, Any]:
        """
        Validate timing window for pre-event betting

        Args:
            market: Market instance
            bet_timestamp: Timestamp of bet (default: now)

        Returns:
            Dict with timing validation results
        """
        if not market.end_date:
            return {
                'is_valid': False,
                'reason': 'No end date set for market',
                'hours_before_event': None
            }

        bet_time = bet_timestamp or datetime.now()

        # Check if market already ended
        if bet_time >= market.end_date:
            return {
                'is_valid': False,
                'reason': 'Market already ended',
                'hours_before_event': None
            }

        # Calculate hours before event
        time_diff = market.end_date - bet_time
        hours_before = time_diff.total_seconds() / 3600

        # Validate within window
        is_valid = self.validators.validate_timing_window(
            bet_time,
            market.end_date,
            self.pre_event_min_hours,
            self.pre_event_max_hours
        )

        return {
            'is_valid': is_valid,
            'hours_before_event': round(hours_before, 2),
            'in_perfect_window': 1 <= hours_before <= 3,
            'too_early': hours_before > self.pre_event_max_hours,
            'too_late': hours_before < self.pre_event_min_hours
        }

    def is_consolidation_phase(self, market: Market, lookback_hours: int = 6) -> bool:
        """
        Detect if market is in consolidation phase (not hype)

        Args:
            market: Market instance
            lookback_hours: Hours to look back for analysis

        Returns:
            True if in consolidation, False if in hype phase
        """
        if not market.current_probability or not market.opening_probability:
            return False

        # Check recent volume patterns
        recent_bets = self.bet_repo.get_market_bets(
            market.market_id,
            hours=lookback_hours
        )

        if not recent_bets:
            return True  # No recent activity = consolidation

        # Calculate volatility
        prob_change = abs(market.current_probability - market.opening_probability)

        # Low volatility = consolidation
        # High volatility with many bets = hype phase
        is_low_volatility = prob_change < 0.10  # Less than 10% change
        is_moderate_activity = len(recent_bets) < 20  # Not too many bets

        return is_low_volatility and is_moderate_activity

    def get_market_activity(self, market_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get market activity summary

        Args:
            market_id: Market ID
            hours: Hours to look back

        Returns:
            Dict with activity metrics
        """
        market = self.market_repo.get_by_market_id(market_id)
        if not market:
            return {}

        recent_bets = self.bet_repo.get_market_bets(market_id, hours=hours)

        # Calculate metrics
        total_bets = len(recent_bets)
        total_volume = sum(bet.bet_amount for bet in recent_bets)
        avg_bet_size = total_volume / total_bets if total_bets > 0 else 0

        # Unique wallets
        unique_wallets = len(set(bet.wallet_id for bet in recent_bets))

        # Pre-news bets
        pre_news_bets = [bet for bet in recent_bets if bet.is_pre_news]

        return {
            'market_id': market_id,
            'title': market.title,
            'total_bets': total_bets,
            'total_volume': round(total_volume, 2),
            'avg_bet_size': round(avg_bet_size, 2),
            'unique_wallets': unique_wallets,
            'pre_news_bets': len(pre_news_bets),
            'liquidity': market.liquidity,
            'current_probability': market.current_probability,
            'is_consolidation': self.is_consolidation_phase(market)
        }

    def check_bet_synchronization(self, bet_timestamps: List[datetime]) -> Dict[str, Any]:
        """
        Check if bets are synchronized within time window

        Args:
            bet_timestamps: List of bet timestamps

        Returns:
            Dict with synchronization analysis
        """
        if not bet_timestamps or len(bet_timestamps) < 2:
            return {
                'is_synchronized': False,
                'reason': 'Insufficient bets for sync check',
                'time_spread_minutes': None
            }

        sorted_times = sorted(bet_timestamps)
        time_spread = sorted_times[-1] - sorted_times[0]
        spread_minutes = time_spread.total_seconds() / 60

        is_synced = self.validators.validate_sync_window(
            bet_timestamps,
            self.sync_window_minutes
        )

        return {
            'is_synchronized': is_synced,
            'time_spread_minutes': round(spread_minutes, 2),
            'first_bet': sorted_times[0],
            'last_bet': sorted_times[-1],
            'total_bets': len(bet_timestamps)
        }

    def get_high_liquidity_markets(self) -> List[Market]:
        """
        Get all markets with sufficient liquidity

        Returns:
            List of high liquidity markets
        """
        return self.market_repo.get_high_liquidity_markets(
            min_liquidity=self.min_liquidity
        )

    def get_upcoming_markets(self, hours_ahead: int = 24) -> List[Market]:
        """
        Get markets ending within specified hours

        Args:
            hours_ahead: Hours to look ahead

        Returns:
            List of upcoming markets
        """
        cutoff = datetime.now() + timedelta(hours=hours_ahead)
        markets = self.market_repo.get_active_markets()

        return [
            m for m in markets
            if m.end_date and datetime.now() < m.end_date <= cutoff
        ]

    def scan_markets(self, market_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk scan and update market data

        Args:
            market_data_list: List of market data dicts

        Returns:
            Scan results summary
        """
        self.logger.info(f"Scanning {len(market_data_list)} markets...")

        added = 0
        updated = 0
        high_liquidity = 0
        upcoming = 0

        for market_data in market_data_list:
            market_id = market_data.get('market_id')
            if not market_id:
                continue

            existing = self.market_repo.get_by_market_id(market_id)
            is_new = existing is None

            market = self.add_or_update_market(market_id, market_data)

            if is_new:
                added += 1
            else:
                updated += 1

            if market.liquidity >= self.min_liquidity:
                high_liquidity += 1

            # Check if upcoming (next 24 hours)
            if market.end_date:
                hours_until = (market.end_date - datetime.now()).total_seconds() / 3600
                if 0 < hours_until <= 24:
                    upcoming += 1

        results = {
            'total_scanned': len(market_data_list),
            'added': added,
            'updated': updated,
            'high_liquidity': high_liquidity,
            'upcoming_24h': upcoming
        }

        self.logger.info(
            f"Market scan complete: {added} added, {updated} updated, "
            f"{high_liquidity} high liquidity, {upcoming} upcoming"
        )

        return results
