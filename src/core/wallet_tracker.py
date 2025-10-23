"""Smart wallet identification and tracking for EdgeCopy v1"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..database.models import Wallet
from ..database.repository import WalletRepository
from ..utils.validators import Validators
from ..utils.logger import Logger


class WalletTracker:
    """
    Tracks and identifies smart wallets based on performance criteria

    Criteria:
    - 30%+ ROI over 30 days
    - 60%+ win rate
    - $10k+ average bet size
    - Pre-news entry patterns
    - Consistent profitability
    """

    def __init__(self, config: dict, wallet_repo: WalletRepository, logger: Logger):
        """
        Initialize wallet tracker

        Args:
            config: Configuration dict
            wallet_repo: Wallet repository instance
            logger: Logger instance
        """
        self.config = config
        self.wallet_repo = wallet_repo
        self.logger = logger
        self.validators = Validators()

        # Criteria from config
        self.min_pnl = config.get('min_pnl_percent', 30)
        self.min_win_rate = config.get('min_win_rate', 60)
        self.min_avg_bet = config.get('min_avg_bet_size', 10000)
        self.max_wallet_age = config.get('max_wallet_age_days', 30)

        # Insider detection settings
        insider_config = config.get('insider_detection', {})
        self.detect_insiders = insider_config.get('enable', True)
        self.new_wallet_age = insider_config.get('new_wallet_age_days', 1)
        self.max_markets_new = insider_config.get('max_markets_for_new', 3)

    def add_or_update_wallet(self, address: str, metrics: Dict[str, Any]) -> Wallet:
        """
        Add new wallet or update existing one

        Args:
            address: Wallet address
            metrics: Wallet performance metrics

        Returns:
            Wallet instance
        """
        if not self.validators.validate_wallet_address(address):
            self.logger.error(f"Invalid wallet address: {address}")
            return None

        wallet = self.wallet_repo.get_or_create(address)

        # Update metrics
        update_data = {
            'pnl_percent': metrics.get('pnl_percent', 0),
            'win_rate': metrics.get('win_rate', 0),
            'avg_bet_size': metrics.get('avg_bet_size', 0),
            'total_volume': metrics.get('total_volume', 0),
            'profit_usd': metrics.get('profit_usd', 0),
            'total_bets': metrics.get('total_bets', 0),
            'winning_bets': metrics.get('winning_bets', 0),
            'losing_bets': metrics.get('losing_bets', 0),
            'markets_count': metrics.get('markets_count', 0),
            'last_active': metrics.get('last_active', datetime.now()),
            'last_scanned': datetime.now()
        }

        # Classify wallet
        update_data['is_smart_wallet'] = self._is_smart_wallet(update_data)
        update_data['is_insider_pattern'] = self._is_insider_pattern(update_data, wallet)
        update_data['reputation_score'] = self._calculate_reputation(update_data)

        # Update
        for key, value in update_data.items():
            setattr(wallet, key, value)

        self.wallet_repo.session.commit()

        if update_data['is_smart_wallet']:
            self.logger.info(
                f"Smart wallet tracked: {address[:10]}... "
                f"PnL:{update_data['pnl_percent']:.1f}% WR:{update_data['win_rate']:.1f}%"
            )

        return wallet

    def _is_smart_wallet(self, metrics: Dict[str, Any]) -> bool:
        """
        Determine if wallet meets smart wallet criteria

        Args:
            metrics: Wallet metrics

        Returns:
            True if smart wallet, False otherwise
        """
        return (
            self.validators.validate_pnl(metrics.get('pnl_percent', 0), self.min_pnl) and
            self.validators.validate_win_rate(metrics.get('win_rate', 0), self.min_win_rate) and
            self.validators.validate_bet_size(metrics.get('avg_bet_size', 0), self.min_avg_bet) and
            metrics.get('total_bets', 0) >= 5  # Minimum bet history
        )

    def _is_insider_pattern(self, metrics: Dict[str, Any], wallet: Wallet) -> bool:
        """
        Detect event-based insider pattern

        Args:
            metrics: Wallet metrics
            wallet: Wallet instance

        Returns:
            True if matches insider pattern, False otherwise
        """
        if not self.detect_insiders:
            return False

        # New wallet with focused betting
        wallet_age = datetime.now() - (wallet.first_seen or datetime.now())
        is_new = wallet_age.days <= self.new_wallet_age
        is_focused = metrics.get('markets_count', 0) <= self.max_markets_new

        # High confidence bets
        has_large_bets = metrics.get('avg_bet_size', 0) > self.min_avg_bet
        has_high_win_rate = metrics.get('win_rate', 0) > 70

        return is_new and is_focused and has_large_bets and has_high_win_rate

    def _calculate_reputation(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate wallet reputation score (0-100)

        Args:
            metrics: Wallet metrics

        Returns:
            Reputation score
        """
        score = 0.0

        # PnL contribution (0-30 points)
        pnl = metrics.get('pnl_percent', 0)
        if pnl >= 30:
            score += min(30, pnl * 0.5)

        # Win rate contribution (0-30 points)
        win_rate = metrics.get('win_rate', 0)
        if win_rate >= 60:
            score += (win_rate - 60) * 0.75

        # Volume contribution (0-20 points)
        volume = metrics.get('total_volume', 0)
        if volume > 10000:
            score += min(20, (volume / 10000) * 2)

        # Consistency contribution (0-20 points)
        total_bets = metrics.get('total_bets', 0)
        if total_bets >= 10:
            score += min(20, (total_bets / 10) * 2)

        return min(100, round(score, 2))

    def get_smart_wallets(self) -> List[Wallet]:
        """
        Get all tracked smart wallets

        Returns:
            List of smart wallet instances
        """
        return self.wallet_repo.get_smart_wallets(
            min_pnl=self.min_pnl,
            min_win_rate=self.min_win_rate
        )

    def get_insider_patterns(self) -> List[Wallet]:
        """
        Get wallets matching insider patterns

        Returns:
            List of potential insider wallets
        """
        return self.wallet_repo.get_insider_patterns()

    def get_active_smart_wallets(self, days: int = None) -> List[Wallet]:
        """
        Get smart wallets active in recent period

        Args:
            days: Number of days to look back (default from config)

        Returns:
            List of active smart wallets
        """
        days = days or self.max_wallet_age
        cutoff = datetime.now() - timedelta(days=days)

        wallets = self.get_smart_wallets()
        return [w for w in wallets if w.last_active >= cutoff]

    def get_wallet_stats(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed stats for a wallet

        Args:
            address: Wallet address

        Returns:
            Dict of wallet statistics
        """
        wallet = self.wallet_repo.get_by_address(address)
        if not wallet:
            return None

        return {
            'address': wallet.address,
            'pnl_percent': wallet.pnl_percent,
            'win_rate': wallet.win_rate,
            'avg_bet_size': wallet.avg_bet_size,
            'total_volume': wallet.total_volume,
            'profit_usd': wallet.profit_usd,
            'total_bets': wallet.total_bets,
            'winning_bets': wallet.winning_bets,
            'losing_bets': wallet.losing_bets,
            'markets_count': wallet.markets_count,
            'first_seen': wallet.first_seen,
            'last_active': wallet.last_active,
            'is_smart_wallet': wallet.is_smart_wallet,
            'is_insider_pattern': wallet.is_insider_pattern,
            'reputation_score': wallet.reputation_score
        }

    def get_top_performers(self, limit: int = 20) -> List[Wallet]:
        """
        Get top performing smart wallets

        Args:
            limit: Maximum number of wallets to return

        Returns:
            List of top performing wallets
        """
        return self.wallet_repo.get_top_performers(limit=limit)

    def scan_wallets(self, wallet_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk scan and update wallet data

        Args:
            wallet_data_list: List of wallet data dicts

        Returns:
            Scan results summary
        """
        self.logger.info(f"Scanning {len(wallet_data_list)} wallets...")

        added = 0
        updated = 0
        smart_found = 0
        insiders_found = 0

        for wallet_data in wallet_data_list:
            address = wallet_data.get('address')
            if not address:
                continue

            existing = self.wallet_repo.get_by_address(address)
            is_new = existing is None

            wallet = self.add_or_update_wallet(address, wallet_data)

            if wallet:
                if is_new:
                    added += 1
                else:
                    updated += 1

                if wallet.is_smart_wallet:
                    smart_found += 1
                if wallet.is_insider_pattern:
                    insiders_found += 1

        results = {
            'total_scanned': len(wallet_data_list),
            'added': added,
            'updated': updated,
            'smart_wallets_found': smart_found,
            'insider_patterns_found': insiders_found
        }

        self.logger.info(
            f"Wallet scan complete: {added} added, {updated} updated, "
            f"{smart_found} smart wallets, {insiders_found} insider patterns"
        )

        return results
