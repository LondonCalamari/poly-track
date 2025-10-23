"""Blockchain wallet scanner - Direct on-chain monitoring without API keys"""

import time
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..utils.logger import Logger


class BlockchainWalletScanner:
    """
    Direct blockchain wallet scanner

    Monitors wallet activity by:
    - Polling wallet addresses for new transactions
    - Tracking bet activity through Polymarket contracts
    - Detecting synchronized wallet movements
    - Building activity profiles

    This replaces Nevua Markets - no API key required!
    """

    def __init__(
        self,
        polymarket_api,
        polygonscan_api,
        wallet_repo,
        bet_repo,
        logger: Logger
    ):
        """
        Initialize blockchain wallet scanner

        Args:
            polymarket_api: Polymarket API instance
            polygonscan_api: PolygonScan API instance
            wallet_repo: Wallet repository
            bet_repo: Bet repository
            logger: Logger instance
        """
        self.polymarket_api = polymarket_api
        self.polygonscan_api = polygonscan_api
        self.wallet_repo = wallet_repo
        self.bet_repo = bet_repo
        self.logger = logger

        # Track last scan times per wallet
        self.last_scan_times: Dict[str, datetime] = {}

        # Cache of recent transactions to avoid duplicates
        self.seen_transactions: Set[str] = set()

    def track_wallet(self, wallet_address: str) -> bool:
        """
        Add wallet to tracking list

        Args:
            wallet_address: Wallet address to track

        Returns:
            True if successfully added to tracking
        """
        try:
            # Check if wallet exists on blockchain
            exists = self.polygonscan_api.verify_wallet_exists(wallet_address)

            if not exists:
                self.logger.warning(f"Wallet {wallet_address} has no transaction history")
                return False

            # Add or update in database
            wallet = self.wallet_repo.get_or_create(wallet_address)

            # Initialize last scan time
            self.last_scan_times[wallet_address] = datetime.now()

            self.logger.info(f"Now tracking wallet: {wallet_address}")
            return True

        except Exception as e:
            self.logger.error(f"Error tracking wallet {wallet_address}: {e}")
            return False

    def untrack_wallet(self, wallet_address: str) -> bool:
        """
        Remove wallet from tracking

        Args:
            wallet_address: Wallet address to untrack

        Returns:
            True if successfully removed
        """
        try:
            if wallet_address in self.last_scan_times:
                del self.last_scan_times[wallet_address]

            self.logger.info(f"Stopped tracking wallet: {wallet_address}")
            return True

        except Exception as e:
            self.logger.error(f"Error untracking wallet {wallet_address}: {e}")
            return False

    def get_tracked_wallets(self) -> List[str]:
        """
        Get list of currently tracked wallets

        Returns:
            List of wallet addresses
        """
        return list(self.last_scan_times.keys())

    def scan_wallet_activity(self, wallet_address: str) -> Dict[str, Any]:
        """
        Scan a wallet for new activity

        Args:
            wallet_address: Wallet address to scan

        Returns:
            Activity summary dict
        """
        try:
            # Get recent transactions (last scan to now)
            last_scan = self.last_scan_times.get(wallet_address, datetime.now() - timedelta(hours=24))

            # Get wallet's Polymarket positions
            positions = self.polymarket_api.get_wallet_positions(wallet_address)

            # Get blockchain transactions
            blockchain_summary = self.polygonscan_api.get_wallet_activity_summary(wallet_address)

            # Detect new bets/positions
            new_positions = []
            for position in positions:
                # Check if this is a new position we haven't seen
                position_key = f"{wallet_address}_{position.get('market_id')}_{position.get('outcome')}"

                if position_key not in self.seen_transactions:
                    new_positions.append(position)
                    self.seen_transactions.add(position_key)

            # Update last scan time
            self.last_scan_times[wallet_address] = datetime.now()

            return {
                'wallet_address': wallet_address,
                'new_positions_count': len(new_positions),
                'new_positions': new_positions,
                'total_positions': len(positions),
                'blockchain_summary': blockchain_summary,
                'scan_time': datetime.now(),
                'time_since_last_scan': (datetime.now() - last_scan).total_seconds() / 60  # minutes
            }

        except Exception as e:
            self.logger.error(f"Error scanning wallet {wallet_address}: {e}")
            return {'wallet_address': wallet_address, 'error': str(e)}

    def scan_all_tracked_wallets(self) -> Dict[str, Any]:
        """
        Scan all tracked wallets for new activity

        Returns:
            Summary of scan results
        """
        self.logger.info(f"Scanning {len(self.last_scan_times)} tracked wallets...")

        results = {
            'wallets_scanned': 0,
            'new_positions_found': 0,
            'active_wallets': 0,
            'errors': 0,
            'market_overlaps': defaultdict(list)
        }

        for wallet_address in list(self.last_scan_times.keys()):
            activity = self.scan_wallet_activity(wallet_address)

            results['wallets_scanned'] += 1

            if 'error' in activity:
                results['errors'] += 1
                continue

            if activity['new_positions_count'] > 0:
                results['active_wallets'] += 1
                results['new_positions_found'] += activity['new_positions_count']

                # Track market overlaps
                for position in activity['new_positions']:
                    market_id = position.get('market_id')
                    if market_id:
                        results['market_overlaps'][market_id].append({
                            'wallet': wallet_address,
                            'position': position,
                            'timestamp': datetime.now()
                        })

        # Detect overlaps (2+ wallets in same market)
        overlaps_detected = sum(
            1 for market_id, wallets in results['market_overlaps'].items()
            if len(wallets) >= 2
        )

        results['overlaps_detected'] = overlaps_detected

        self.logger.info(
            f"Wallet scan complete: {results['wallets_scanned']} scanned, "
            f"{results['active_wallets']} active, "
            f"{results['new_positions_found']} new positions, "
            f"{overlaps_detected} market overlaps"
        )

        return results

    def auto_track_smart_wallets(self, min_pnl: float = 30, limit: int = 20) -> int:
        """
        Automatically start tracking smart wallets from database

        Args:
            min_pnl: Minimum PnL to consider for tracking
            limit: Maximum wallets to track

        Returns:
            Number of wallets added to tracking
        """
        try:
            smart_wallets = self.wallet_repo.get_smart_wallets(min_pnl=min_pnl)
            smart_wallets = smart_wallets[:limit]  # Limit to avoid overload

            added = 0
            for wallet in smart_wallets:
                if wallet.address not in self.last_scan_times:
                    if self.track_wallet(wallet.address):
                        added += 1

            self.logger.info(f"Auto-tracked {added} smart wallets")
            return added

        except Exception as e:
            self.logger.error(f"Error auto-tracking smart wallets: {e}")
            return 0

    def detect_real_time_signals(self) -> List[Dict[str, Any]]:
        """
        Detect real-time trading signals from tracked wallets

        Returns:
            List of potential signals
        """
        scan_results = self.scan_all_tracked_wallets()

        signals = []

        # Check for market overlaps (multiple smart wallets entering same market)
        for market_id, wallet_activities in scan_results['market_overlaps'].items():
            if len(wallet_activities) >= 2:  # 2+ wallets in same market

                # Check if activities are synchronized (within 30 minutes)
                timestamps = [wa['timestamp'] for wa in wallet_activities]
                time_spread = max(timestamps) - min(timestamps)

                if time_spread.total_seconds() / 60 <= 30:  # Within 30 minutes
                    signals.append({
                        'market_id': market_id,
                        'wallet_count': len(wallet_activities),
                        'wallet_addresses': [wa['wallet'] for wa in wallet_activities],
                        'activities': wallet_activities,
                        'time_spread_minutes': time_spread.total_seconds() / 60,
                        'detected_at': datetime.now()
                    })

        if signals:
            self.logger.info(f"🎯 Real-time signals detected: {len(signals)} market overlaps")

        return signals

    def get_scanning_stats(self) -> Dict[str, Any]:
        """
        Get statistics about scanning activity

        Returns:
            Stats dict
        """
        return {
            'tracked_wallets': len(self.last_scan_times),
            'cached_transactions': len(self.seen_transactions),
            'last_scan_times': {
                addr: scan_time.isoformat()
                for addr, scan_time in self.last_scan_times.items()
            }
        }
