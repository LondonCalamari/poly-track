"""Automatic wallet discovery from Polymarket

Discovers smart wallets by:
1. Fetching active markets from Polymarket
2. Getting recent trades on those markets
3. Extracting wallet addresses
4. Calculating their performance (PnL, win rate, avg bet)
5. Auto-tracking wallets that meet smart wallet criteria
"""

from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict

from ..utils.logger import Logger


class WalletDiscovery:
    """
    Automatic smart wallet discovery from Polymarket

    Uses the EdgeCopy v1 criteria:
    - PnL > 30%
    - Win rate > 60%
    - Avg bet size > $10k
    - Active in last 30 days
    """

    def __init__(
        self,
        polymarket_api,
        wallet_tracker,
        config: dict,
        logger: Logger
    ):
        """
        Initialize wallet discovery

        Args:
            polymarket_api: Polymarket API instance
            wallet_tracker: WalletTracker instance
            config: Configuration dict
            logger: Logger instance
        """
        self.polymarket_api = polymarket_api
        self.wallet_tracker = wallet_tracker
        self.config = config
        self.logger = logger

        # Criteria from config
        self.min_pnl = config.get('min_pnl_percent', 30)
        self.min_win_rate = config.get('min_win_rate', 60)
        self.min_avg_bet = config.get('min_avg_bet_size', 10000)
        self.min_total_bets = 5  # Minimum bet history

    def discover_wallets_from_markets(
        self,
        limit_markets: int = 50,
        limit_trades_per_market: int = 100
    ) -> Dict[str, Any]:
        """
        Discover wallets by scanning active markets

        Args:
            limit_markets: Number of markets to scan
            limit_trades_per_market: Trades to fetch per market

        Returns:
            Discovery results dict
        """
        self.logger.info(f"🔍 Discovering smart wallets from {limit_markets} active markets...")

        # Get active markets
        markets = self.polymarket_api.get_markets(limit=limit_markets, active_only=True)

        if not markets:
            self.logger.warning("No markets fetched - check Polymarket API")
            return {'wallets_discovered': 0, 'wallets_added': 0}

        self.logger.info(f"Scanning {len(markets)} markets for wallet activity...")

        # Track wallet addresses we find
        wallet_addresses: Set[str] = set()

        # Scan each market for trades
        for market in markets:
            market_id = market.get('market_id')
            if not market_id:
                continue

            # Get recent trades
            trades = self.polymarket_api.get_market_trades(
                market_id,
                limit=limit_trades_per_market
            )

            # Extract wallet addresses
            for trade in trades:
                wallet_addr = trade.get('wallet_address')
                if wallet_addr:
                    wallet_addresses.add(wallet_addr)

        self.logger.info(f"Found {len(wallet_addresses)} unique wallet addresses")

        # Analyze each wallet
        return self.analyze_and_filter_wallets(list(wallet_addresses))

    def analyze_and_filter_wallets(self, wallet_addresses: List[str]) -> Dict[str, Any]:
        """
        Analyze wallets and filter for smart wallet criteria

        Args:
            wallet_addresses: List of wallet addresses to analyze

        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing {len(wallet_addresses)} wallets for smart wallet criteria...")

        smart_wallets_found = 0
        wallets_added = 0
        wallets_updated = 0

        for i, address in enumerate(wallet_addresses):
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{len(wallet_addresses)} wallets analyzed...")

            try:
                # Get wallet's positions and calculate metrics
                metrics = self.calculate_wallet_metrics(address)

                if not metrics:
                    continue

                # Check if meets smart wallet criteria
                if self.meets_smart_wallet_criteria(metrics):
                    smart_wallets_found += 1

                    # Add or update in tracker
                    wallet = self.wallet_tracker.add_or_update_wallet(address, metrics)

                    if wallet:
                        if wallet.created_at == wallet.updated_at:
                            wallets_added += 1
                            self.logger.info(
                                f"✓ New smart wallet: {address[:10]}... "
                                f"PnL:{metrics['pnl_percent']:.1f}% WR:{metrics['win_rate']:.1f}%"
                            )
                        else:
                            wallets_updated += 1

            except Exception as e:
                self.logger.error(f"Error analyzing wallet {address}: {e}")
                continue

        results = {
            'wallets_scanned': len(wallet_addresses),
            'smart_wallets_found': smart_wallets_found,
            'wallets_added': wallets_added,
            'wallets_updated': wallets_updated
        }

        self.logger.info(
            f"✓ Discovery complete: {smart_wallets_found} smart wallets found, "
            f"{wallets_added} added, {wallets_updated} updated"
        )

        return results

    def calculate_wallet_metrics(self, wallet_address: str) -> Dict[str, Any]:
        """
        Calculate performance metrics for a wallet

        Args:
            wallet_address: Wallet address

        Returns:
            Metrics dict or None if insufficient data
        """
        # Get wallet positions
        positions = self.polymarket_api.get_wallet_positions(wallet_address)

        if not positions or len(positions) < self.min_total_bets:
            return None

        # Calculate metrics
        total_bets = len(positions)
        total_invested = 0
        total_value = 0
        winning_bets = 0
        losing_bets = 0
        bet_sizes = []

        for position in positions:
            # Get bet details
            invested = float(position.get('size', 0) or 0)
            current_value = float(position.get('value', 0) or 0)

            total_invested += invested
            total_value += current_value
            bet_sizes.append(invested)

            # Determine if winning or losing
            if current_value > invested:
                winning_bets += 1
            elif current_value < invested:
                losing_bets += 1

        # Calculate PnL
        if total_invested > 0:
            pnl_percent = ((total_value - total_invested) / total_invested) * 100
        else:
            pnl_percent = 0

        # Calculate win rate
        if total_bets > 0:
            win_rate = (winning_bets / total_bets) * 100
        else:
            win_rate = 0

        # Calculate average bet size
        avg_bet_size = sum(bet_sizes) / len(bet_sizes) if bet_sizes else 0

        # Calculate profit in USD
        profit_usd = total_value - total_invested

        # Count unique markets
        markets = set(p.get('market_id') or p.get('asset_id') for p in positions if p.get('market_id') or p.get('asset_id'))
        markets_count = len(markets)

        return {
            'address': wallet_address,
            'pnl_percent': pnl_percent,
            'win_rate': win_rate,
            'avg_bet_size': avg_bet_size,
            'total_volume': total_invested + total_value,  # Total activity
            'profit_usd': profit_usd,
            'total_bets': total_bets,
            'winning_bets': winning_bets,
            'losing_bets': losing_bets,
            'markets_count': markets_count,
            'last_active': datetime.now()  # Could parse from position data
        }

    def meets_smart_wallet_criteria(self, metrics: Dict[str, Any]) -> bool:
        """
        Check if wallet meets smart wallet criteria

        Args:
            metrics: Wallet metrics dict

        Returns:
            True if meets criteria, False otherwise
        """
        return (
            metrics['pnl_percent'] >= self.min_pnl and
            metrics['win_rate'] >= self.min_win_rate and
            metrics['avg_bet_size'] >= self.min_avg_bet and
            metrics['total_bets'] >= self.min_total_bets
        )

    def discover_from_leaderboard(self, limit: int = 50) -> Dict[str, Any]:
        """
        Discover wallets from Polymarket leaderboard

        Note: This would require scraping or API endpoint access
        Currently returns placeholder

        Args:
            limit: Number of top wallets to fetch

        Returns:
            Discovery results
        """
        self.logger.info("Leaderboard discovery not yet implemented")
        self.logger.info("Use discover_wallets_from_markets() instead")

        return {
            'wallets_discovered': 0,
            'wallets_added': 0,
            'note': 'Leaderboard scraping requires additional implementation'
        }

    def get_discovery_stats(self) -> Dict[str, Any]:
        """
        Get statistics about discovered wallets

        Returns:
            Stats dict
        """
        smart_wallets = self.wallet_tracker.get_smart_wallets()

        return {
            'total_smart_wallets': len(smart_wallets),
            'avg_pnl': sum(w.pnl_percent for w in smart_wallets) / len(smart_wallets) if smart_wallets else 0,
            'avg_win_rate': sum(w.win_rate for w in smart_wallets) / len(smart_wallets) if smart_wallets else 0,
            'avg_reputation': sum(w.reputation_score for w in smart_wallets) / len(smart_wallets) if smart_wallets else 0,
            'insider_patterns': sum(1 for w in smart_wallets if w.is_insider_pattern)
        }
