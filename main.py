#!/usr/bin/env python3
"""
EdgeCopy v1 - Polymarket Smart Wallet Tracker
Main entry point and orchestrator
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import Config
from src.utils.logger import get_logger
from src.database.models import init_database
from src.database.repository import (
    WalletRepository,
    MarketRepository,
    BetRepository,
    SignalRepository,
    ScanLogRepository
)
from src.core.wallet_tracker import WalletTracker
from src.core.market_monitor import MarketMonitor
from src.core.signal_detector import SignalDetector
from src.core.risk_manager import RiskManager
from src.integrations.polymarket import PolymarketAPI
from src.integrations.polysights import PolysightsAPI
from src.integrations.nevua import NevuaMarketsAPI
from src.integrations.hashdive import HashDiveAPI
from src.alerts.alert_manager import AlertManager


class EdgeCopyTracker:
    """
    EdgeCopy v1 main tracker orchestrator
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize EdgeCopy tracker

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)

        # Initialize logger
        self.logger = get_logger("EdgeCopy", self.config.logging_config)

        # Initialize database
        db_path = self.config.get('storage.db_path', './data/polytrack.db')
        self.db = init_database(db_path)
        self.session = self.db.get_session()

        # Initialize repositories
        self.wallet_repo = WalletRepository(self.session)
        self.market_repo = MarketRepository(self.session)
        self.bet_repo = BetRepository(self.session)
        self.signal_repo = SignalRepository(self.session)
        self.scan_log_repo = ScanLogRepository(self.session)

        # Initialize core modules
        self.wallet_tracker = WalletTracker(
            self.config.wallet_criteria,
            self.wallet_repo,
            self.logger
        )

        self.market_monitor = MarketMonitor(
            self.config.config,
            self.market_repo,
            self.bet_repo,
            self.logger
        )

        self.signal_detector = SignalDetector(
            self.config.config,
            self.wallet_tracker,
            self.market_monitor,
            self.signal_repo,
            self.wallet_repo,
            self.market_repo,
            self.bet_repo,
            self.logger
        )

        self.risk_manager = RiskManager(
            self.config.config,
            self.logger
        )

        # Initialize integrations
        self.polymarket_api = PolymarketAPI(
            self.config.get('apis.polymarket', {}),
            self.logger
        )

        self.polysights_api = PolysightsAPI(
            self.config.get('apis.polysights', {}),
            self.logger
        )

        self.nevua_api = NevuaMarketsAPI(
            self.config.get('apis.nevua_markets', {}),
            self.logger
        )

        self.hashdive_api = HashDiveAPI(
            self.config.get('apis.hash_dive', {}),
            self.logger
        )

        # Initialize alerts
        self.alert_manager = AlertManager(
            self.config.alerts_config,
            self.logger
        )

        self.logger.info("EdgeCopy v1 initialized successfully")

    def scan_wallets(self) -> dict:
        """
        Scan and update smart wallet data

        Returns:
            Scan results
        """
        self.logger.info("Starting wallet scan...")
        start_time = datetime.now()

        # Fetch wallet data from Polysights
        wallet_data = self.polysights_api.get_smart_wallets(
            min_pnl=self.config.get('wallet_criteria.min_pnl_percent', 30),
            min_win_rate=self.config.get('wallet_criteria.min_win_rate', 60),
            min_avg_bet=self.config.get('wallet_criteria.min_avg_bet_size', 10000)
        )

        # Update wallet tracker
        results = self.wallet_tracker.scan_wallets(wallet_data)

        # Log scan
        duration = (datetime.now() - start_time).total_seconds()
        self.scan_log_repo.create(
            scan_type='WALLET_SCAN',
            items_scanned=results['total_scanned'],
            items_added=results['added'],
            items_updated=results['updated'],
            duration_seconds=duration
        )

        return results

    def scan_markets(self) -> dict:
        """
        Scan and update market data

        Returns:
            Scan results
        """
        self.logger.info("Starting market scan...")
        start_time = datetime.now()

        # Fetch market data from Polymarket
        market_data = self.polymarket_api.get_markets(limit=100, active_only=True)

        # Update market monitor
        results = self.market_monitor.scan_markets(market_data)

        # Log scan
        duration = (datetime.now() - start_time).total_seconds()
        self.scan_log_repo.create(
            scan_type='MARKET_SCAN',
            items_scanned=results['total_scanned'],
            items_added=results['added'],
            items_updated=results['updated'],
            duration_seconds=duration
        )

        return results

    def detect_signals(self, lookback_hours: int = 24) -> dict:
        """
        Run signal detection scan

        Args:
            lookback_hours: Hours to look back

        Returns:
            Signal detection results
        """
        self.logger.info("Starting signal detection...")
        start_time = datetime.now()

        # Run signal detection
        results = self.signal_detector.scan_for_signals(lookback_hours)

        # Send alerts for new signals
        if results['signals_created'] > 0:
            signals = self.signal_detector.get_active_signals()

            for signal in signals[-results['signals_created']:]:  # Only new signals
                signal_summary = self.signal_detector.get_signal_summary(signal)
                self.alert_manager.send_signal_alert(signal_summary)

        # Send scan summary
        self.alert_manager.send_scan_summary(results)

        # Log scan
        duration = (datetime.now() - start_time).total_seconds()
        self.scan_log_repo.create(
            scan_type='SIGNAL_DETECTION',
            items_scanned=results['overlaps_found'],
            signals_generated=results['signals_created'],
            duration_seconds=duration
        )

        return results

    def run_full_scan(self) -> dict:
        """
        Run complete scan cycle (wallets + markets + signals)

        Returns:
            Combined scan results
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting EdgeCopy v1 full scan cycle")
        self.logger.info("=" * 60)

        results = {
            'wallets': self.scan_wallets(),
            'markets': self.scan_markets(),
            'signals': self.detect_signals()
        }

        self.logger.info("=" * 60)
        self.logger.info("Full scan cycle complete")
        self.logger.info(f"Smart wallets found: {results['wallets']['smart_wallets_found']}")
        self.logger.info(f"Markets scanned: {results['markets']['total_scanned']}")
        self.logger.info(f"Signals created: {results['signals']['signals_created']}")
        self.logger.info("=" * 60)

        return results

    def run_continuous(self, interval_minutes: int = None):
        """
        Run continuous monitoring loop

        Args:
            interval_minutes: Scan interval (default from config)
        """
        interval = interval_minutes or self.config.get('monitoring.scan_interval_minutes', 10)

        self.logger.info(f"Starting continuous monitoring (interval: {interval} minutes)")
        self.logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.run_full_scan()

                self.logger.info(f"Next scan in {interval} minutes...")
                time.sleep(interval * 60)

        except KeyboardInterrupt:
            self.logger.info("\nStopping EdgeCopy tracker...")
            self.session.close()

    def list_smart_wallets(self):
        """List all tracked smart wallets"""
        wallets = self.wallet_tracker.get_smart_wallets()

        print("\n" + "=" * 80)
        print(f"SMART WALLETS ({len(wallets)} found)")
        print("=" * 80)

        for wallet in wallets:
            print(f"\nAddress: {wallet.address}")
            print(f"  PnL: {wallet.pnl_percent:.1f}% | Win Rate: {wallet.win_rate:.1f}% | "
                  f"Avg Bet: ${wallet.avg_bet_size:,.0f}")
            print(f"  Total Bets: {wallet.total_bets} ({wallet.winning_bets}W/{wallet.losing_bets}L)")
            print(f"  Reputation: {wallet.reputation_score:.1f}/100")
            if wallet.is_insider_pattern:
                print(f"  ⚠️  INSIDER PATTERN DETECTED")

        print("\n" + "=" * 80 + "\n")

    def list_signals(self, hours: int = 24):
        """
        List recent signals

        Args:
            hours: Hours to look back
        """
        signals = self.signal_repo.get_recent_signals(hours=hours, min_score=0)

        print("\n" + "=" * 80)
        print(f"RECENT SIGNALS (last {hours} hours)")
        print("=" * 80)

        for signal in signals:
            summary = self.signal_detector.get_signal_summary(signal)

            print(f"\nSignal #{summary['signal_id']}")
            print(f"  Market: {summary['market_title'][:60]}...")
            print(f"  Score: {summary['perfect_bet_score']} | Confidence: {summary['confidence']}")
            print(f"  Wallets: {summary['wallet_count']} | Avg PnL: {summary['avg_wallet_pnl']}")
            print(f"  Liquidity: {summary['liquidity']} | Odds: {summary['current_odds']}")
            print(f"  Time to Event: {summary['hours_before_event']}")
            print(f"  Status: {'🚩 HAS RED FLAGS' if summary['has_red_flags'] else '✓ Clean'}")
            print(f"  Created: {summary['created_at']}")

        print("\n" + "=" * 80 + "\n")

    def test_alerts(self):
        """Test all alert channels"""
        print("\nTesting alert channels...")
        results = self.alert_manager.send_test_alert()

        print("\nAlert Test Results:")
        for channel, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"  {channel}: {status}")

        print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="EdgeCopy v1 - Polymarket Smart Wallet Tracker"
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--scan-once',
        action='store_true',
        help='Run single scan and exit'
    )

    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )

    parser.add_argument(
        '--interval',
        type=int,
        help='Scan interval in minutes (for continuous mode)'
    )

    parser.add_argument(
        '--list-wallets',
        action='store_true',
        help='List tracked smart wallets'
    )

    parser.add_argument(
        '--show-signals',
        action='store_true',
        help='Show recent signals'
    )

    parser.add_argument(
        '--test-alerts',
        action='store_true',
        help='Test alert channels'
    )

    args = parser.parse_args()

    # Initialize tracker
    try:
        tracker = EdgeCopyTracker(config_path=args.config)
    except Exception as e:
        print(f"Error initializing tracker: {e}")
        sys.exit(1)

    # Execute command
    try:
        if args.list_wallets:
            tracker.list_smart_wallets()

        elif args.show_signals:
            tracker.list_signals()

        elif args.test_alerts:
            tracker.test_alerts()

        elif args.scan_once:
            tracker.run_full_scan()

        elif args.continuous:
            tracker.run_continuous(interval_minutes=args.interval)

        else:
            # Default: run single scan
            tracker.run_full_scan()

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

    except Exception as e:
        print(f"\nError: {e}")
        tracker.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
