"""EdgeCopy v1 Signal Detection Engine"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..database.models import Signal, Bet
from ..database.repository import SignalRepository, WalletRepository, MarketRepository, BetRepository
from ..core.wallet_tracker import WalletTracker
from ..core.market_monitor import MarketMonitor
from ..utils.validators import Validators
from ..utils.logger import Logger


class SignalDetector:
    """
    EdgeCopy v1 Signal Detection Algorithm

    Detects trading signals by:
    1. Scanning for wallet overlaps (≥2 smart wallets in same market)
    2. Validating liquidity (>$300k)
    3. Checking timing (<5h before event)
    4. Calculating Perfect Bet score (need 5/6)
    5. Filtering red flags
    """

    def __init__(
        self,
        config: dict,
        wallet_tracker: WalletTracker,
        market_monitor: MarketMonitor,
        signal_repo: SignalRepository,
        wallet_repo: WalletRepository,
        market_repo: MarketRepository,
        bet_repo: BetRepository,
        logger: Logger
    ):
        """
        Initialize signal detector

        Args:
            config: Configuration dict
            wallet_tracker: WalletTracker instance
            market_monitor: MarketMonitor instance
            signal_repo: Signal repository
            wallet_repo: Wallet repository
            market_repo: Market repository
            bet_repo: Bet repository
            logger: Logger instance
        """
        self.config = config
        self.wallet_tracker = wallet_tracker
        self.market_monitor = market_monitor
        self.signal_repo = signal_repo
        self.wallet_repo = wallet_repo
        self.market_repo = market_repo
        self.bet_repo = bet_repo
        self.logger = logger
        self.validators = Validators()

        # Signal detection config
        signal_config = config.get('signal_detection', {})
        self.min_wallet_overlap = signal_config.get('min_wallet_overlap', 2)
        self.min_liquidity = signal_config.get('min_liquidity', 300000)
        self.pre_event_min = signal_config.get('pre_event_window_hours_min', 1)
        self.pre_event_max = signal_config.get('pre_event_window_hours_max', 5)
        self.sync_window = signal_config.get('sync_time_window_minutes', 30)

        # Perfect bet config
        perfect_config = config.get('perfect_bet', {})
        self.enable_perfect_checklist = perfect_config.get('enable_checklist', True)
        self.min_perfect_score = perfect_config.get('min_score', 5)

        # Red flags config
        red_flags_config = config.get('red_flags', {})
        self.detect_red_flags = red_flags_config.get('detect_fake_clusters', True)
        self.cross_verify_count = red_flags_config.get('cross_verify_sources', 2)

    def detect_wallet_overlaps(self, lookback_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect markets where multiple smart wallets have entered

        Args:
            lookback_hours: Hours to look back for recent bets

        Returns:
            List of market overlaps with wallet details
        """
        self.logger.info(f"Detecting wallet overlaps in last {lookback_hours} hours...")

        # Get smart wallets
        smart_wallets = self.wallet_tracker.get_active_smart_wallets()

        if not smart_wallets:
            self.logger.warning("No active smart wallets found")
            return []

        # Track market -> wallets mapping
        market_wallets = defaultdict(list)

        # Scan recent bets from smart wallets
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        for wallet in smart_wallets:
            recent_bets = self.bet_repo.get_wallet_bets(wallet.address)
            recent_bets = [b for b in recent_bets if b.bet_timestamp >= cutoff_time]

            for bet in recent_bets:
                market_wallets[bet.market.market_id].append({
                    'wallet': wallet,
                    'bet': bet
                })

        # Filter for overlaps
        overlaps = []

        for market_id, wallet_bet_list in market_wallets.items():
            unique_wallets = len(set(wb['wallet'].id for wb in wallet_bet_list))

            if unique_wallets >= self.min_wallet_overlap:
                market = self.market_repo.get_by_market_id(market_id)

                if not market:
                    continue

                overlaps.append({
                    'market_id': market_id,
                    'market': market,
                    'wallet_count': unique_wallets,
                    'wallet_bets': wallet_bet_list
                })

        self.logger.info(f"Found {len(overlaps)} markets with wallet overlaps")

        return overlaps

    def validate_signal(self, overlap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate signal against all criteria

        Args:
            overlap: Market overlap data

        Returns:
            Validation results dict
        """
        market = overlap['market']
        wallet_bets = overlap['wallet_bets']

        validation = {
            'is_valid': True,
            'reasons': [],
            'checks': {}
        }

        # 1. Liquidity check
        liquidity_ok = self.market_monitor.validate_liquidity(market)
        validation['checks']['liquidity'] = liquidity_ok

        if not liquidity_ok:
            validation['is_valid'] = False
            validation['reasons'].append(
                f"Insufficient liquidity: ${market.liquidity:,.0f} < ${self.min_liquidity:,.0f}"
            )

        # 2. Timing check (for most recent bets)
        bet_timestamps = [wb['bet'].bet_timestamp for wb in wallet_bets]
        most_recent_bet = max(bet_timestamps)

        timing = self.market_monitor.validate_timing(market, most_recent_bet)
        validation['checks']['timing'] = timing['is_valid']
        validation['hours_before_event'] = timing['hours_before_event']

        if not timing['is_valid']:
            validation['is_valid'] = False
            validation['reasons'].append(
                f"Outside timing window: {timing.get('reason', 'Invalid timing')}"
            )

        # 3. Synchronization check
        sync_result = self.market_monitor.check_bet_synchronization(bet_timestamps)
        validation['checks']['synchronized'] = sync_result['is_synchronized']
        validation['time_spread_minutes'] = sync_result['time_spread_minutes']

        if not sync_result['is_synchronized']:
            validation['is_valid'] = False
            validation['reasons'].append(
                f"Bets not synchronized: {sync_result['time_spread_minutes']:.1f} min spread"
            )

        # 4. Market activity status
        is_consolidation = self.market_monitor.is_consolidation_phase(market)
        validation['checks']['consolidation'] = is_consolidation

        return validation

    def calculate_perfect_bet_score(
        self,
        market,
        wallet_count: int,
        is_consolidation: bool,
        is_pre_news: bool
    ) -> Dict[str, Any]:
        """
        Calculate Perfect Bet Checklist score

        Args:
            market: Market instance
            wallet_count: Number of smart wallets
            is_consolidation: Whether in consolidation phase
            is_pre_news: Whether in pre-news window

        Returns:
            Perfect bet scoring dict
        """
        # Get wallets data
        wallets = self.wallet_tracker.get_smart_wallets()
        avg_pnl = sum(w.pnl_percent for w in wallets) / len(wallets) if wallets else 0
        wallet_confirmed = avg_pnl >= 30

        return self.validators.calculate_perfect_bet_score(
            liquidity=market.liquidity,
            smart_wallet_count=wallet_count,
            is_consolidation=is_consolidation,
            wallet_confirmed=wallet_confirmed,
            is_pre_news=is_pre_news,
            risk_percent=10  # Default, should be calculated based on position size
        )

    def detect_red_flags(
        self,
        overlap: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect red flags in signal

        Args:
            overlap: Market overlap data

        Returns:
            Red flags detection results
        """
        wallet_bets = overlap['wallet_bets']
        market = overlap['market']

        # Count new wallets (< 1 day old)
        new_wallet_count = sum(
            1 for wb in wallet_bets
            if (datetime.now() - wb['wallet'].first_seen).days < 1
        )

        # Check bet synchronization
        bet_timestamps = [wb['bet'].bet_timestamp for wb in wallet_bets]
        time_spread = (max(bet_timestamps) - min(bet_timestamps)).total_seconds() / 60

        # Check bet sizes (small identical bets are suspicious)
        bet_sizes = [wb['bet'].bet_amount for wb in wallet_bets]
        avg_bet_size = sum(bet_sizes) / len(bet_sizes) if bet_sizes else 0
        small_bets = sum(1 for size in bet_sizes if size < 1000)

        red_flags = self.validators.detect_red_flags(
            new_wallet_count=new_wallet_count,
            liquidity=market.liquidity,
            bet_time_spread_minutes=time_spread,
            is_obvious_outcome=False  # Would need additional logic to determine
        )

        # Additional checks
        red_flags['many_small_bets'] = small_bets > len(bet_sizes) * 0.5
        red_flags['suspicious_cluster'] = new_wallet_count > 3 and avg_bet_size < 5000

        has_flags = any(red_flags.values())

        return {
            'has_red_flags': has_flags,
            'flags': red_flags,
            'new_wallet_count': new_wallet_count,
            'avg_bet_size': avg_bet_size
        }

    def create_signal(self, overlap: Dict[str, Any], validation: Dict[str, Any]) -> Optional[Signal]:
        """
        Create signal record in database

        Args:
            overlap: Market overlap data
            validation: Validation results

        Returns:
            Signal instance if created, None otherwise
        """
        if not validation['is_valid']:
            self.logger.debug(
                f"Skipping invalid signal for market {overlap['market_id']}: "
                f"{', '.join(validation['reasons'])}"
            )
            return None

        market = overlap['market']
        wallet_bets = overlap['wallet_bets']
        wallet_count = overlap['wallet_count']

        # Calculate scores
        is_pre_news = validation['checks'].get('timing', False)
        is_consolidation = validation['checks'].get('consolidation', False)

        perfect_score = self.calculate_perfect_bet_score(
            market,
            wallet_count,
            is_consolidation,
            is_pre_news
        )

        # Red flags
        red_flag_results = self.detect_red_flags(overlap)

        # Only create if meets minimum score
        if self.enable_perfect_checklist and perfect_score['score'] < self.min_perfect_score:
            self.logger.debug(
                f"Signal score too low: {perfect_score['score']}/{perfect_score['max_score']} "
                f"for market {market.market_id}"
            )
            return None

        # Calculate average wallet PnL
        wallets = [wb['wallet'] for wb in wallet_bets]
        avg_pnl = sum(w.pnl_percent for w in wallets) / len(wallets) if wallets else 0

        # Get wallet addresses
        wallet_addresses = list(set(w.address for w in wallets))

        # Create signal
        signal_data = {
            'market_id': market.id,
            'signal_type': 'MULTI_WALLET_OVERLAP',
            'confidence_score': perfect_score['score'] / perfect_score['max_score'] * 100,
            'perfect_bet_score': perfect_score['score'],
            'wallet_count': wallet_count,
            'wallet_addresses': wallet_addresses,
            'avg_wallet_pnl': round(avg_pnl, 2),
            'market_liquidity': market.liquidity,
            'current_odds': market.current_probability,
            'is_consolidation': is_consolidation,
            'event_timestamp': market.end_date,
            'hours_before_event': validation.get('hours_before_event'),
            'is_validated': True,
            'has_red_flags': red_flag_results['has_red_flags'],
            'red_flags': red_flag_results['flags'],
            'extra_data': {
                'perfect_bet_checks': perfect_score['checks'],
                'validation': validation,
                'red_flag_details': red_flag_results
            }
        }

        signal = self.signal_repo.create(**signal_data)

        self.logger.info(
            f"🎯 SIGNAL CREATED: {market.title[:50]}... "
            f"Score:{perfect_score['score']}/{perfect_score['max_score']} "
            f"Wallets:{wallet_count} "
            f"Liquidity:${market.liquidity:,.0f}"
        )

        return signal

    def scan_for_signals(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """
        Main signal detection scan

        Args:
            lookback_hours: Hours to look back

        Returns:
            Scan results summary
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting EdgeCopy v1 signal detection scan")
        self.logger.info("=" * 60)

        start_time = datetime.now()

        # Step 1: Detect wallet overlaps
        overlaps = self.detect_wallet_overlaps(lookback_hours)

        if not overlaps:
            self.logger.info("No wallet overlaps found")
            return {
                'overlaps_found': 0,
                'signals_created': 0,
                'signals_rejected': 0,
                'duration_seconds': 0
            }

        # Step 2: Validate and create signals
        signals_created = 0
        signals_rejected = 0

        for overlap in overlaps:
            validation = self.validate_signal(overlap)

            if validation['is_valid']:
                signal = self.create_signal(overlap, validation)
                if signal:
                    signals_created += 1
                else:
                    signals_rejected += 1
            else:
                signals_rejected += 1
                self.logger.debug(
                    f"Signal rejected for {overlap['market_id']}: "
                    f"{', '.join(validation['reasons'])}"
                )

        duration = (datetime.now() - start_time).total_seconds()

        results = {
            'overlaps_found': len(overlaps),
            'signals_created': signals_created,
            'signals_rejected': signals_rejected,
            'duration_seconds': round(duration, 2)
        }

        self.logger.info("=" * 60)
        self.logger.info(f"Scan complete: {signals_created} signals created, {signals_rejected} rejected")
        self.logger.info(f"Duration: {duration:.2f}s")
        self.logger.info("=" * 60)

        return results

    def get_active_signals(self, min_score: int = None) -> List[Signal]:
        """
        Get active signals awaiting user action

        Args:
            min_score: Minimum perfect bet score (default: configured minimum)

        Returns:
            List of active signals
        """
        min_score = min_score or self.min_perfect_score
        return self.signal_repo.get_recent_signals(hours=24, min_score=min_score)

    def get_signal_summary(self, signal: Signal) -> Dict[str, Any]:
        """
        Get formatted signal summary

        Args:
            signal: Signal instance

        Returns:
            Formatted signal summary dict
        """
        market = signal.market

        return {
            'signal_id': signal.id,
            'market_title': market.title,
            'market_id': market.market_id,
            'perfect_bet_score': f"{signal.perfect_bet_score}/6",
            'confidence': f"{signal.confidence_score:.1f}%",
            'wallet_count': signal.wallet_count,
            'avg_wallet_pnl': f"{signal.avg_wallet_pnl:.1f}%",
            'liquidity': f"${signal.market_liquidity:,.0f}",
            'current_odds': f"{signal.current_odds:.3f}" if signal.current_odds else "N/A",
            'hours_before_event': f"{signal.hours_before_event:.1f}h" if signal.hours_before_event else "N/A",
            'is_consolidation': signal.is_consolidation,
            'has_red_flags': signal.has_red_flags,
            'created_at': signal.created_at,
            'wallet_addresses': signal.wallet_addresses
        }
