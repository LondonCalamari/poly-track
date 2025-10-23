"""Internal wallet reputation system - Replaces HashDive"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..database.repository import WalletRepository, BetRepository
from ..utils.logger import Logger


class InternalReputationSystem:
    """
    Internal wallet reputation and verification system

    Calculates reputation based on:
    - Historical performance (PnL, win rate)
    - Consistency over time
    - Volume and bet sizing
    - Market diversity
    - Early entry patterns
    - Profit stability

    This replaces HashDive - no API key required!
    """

    def __init__(
        self,
        wallet_repo: WalletRepository,
        bet_repo: BetRepository,
        logger: Logger
    ):
        """
        Initialize reputation system

        Args:
            wallet_repo: Wallet repository
            bet_repo: Bet repository
            logger: Logger instance
        """
        self.wallet_repo = wallet_repo
        self.bet_repo = bet_repo
        self.logger = logger

    def calculate_reputation_score(
        self,
        wallet_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive reputation score for wallet

        Args:
            wallet_address: Wallet address

        Returns:
            Reputation data dict or None
        """
        try:
            wallet = self.wallet_repo.get_by_address(wallet_address)

            if not wallet:
                self.logger.warning(f"Wallet {wallet_address} not found")
                return None

            # Component scores (each 0-100)
            performance_score = self._calculate_performance_score(wallet)
            consistency_score = self._calculate_consistency_score(wallet)
            volume_score = self._calculate_volume_score(wallet)
            diversity_score = self._calculate_diversity_score(wallet)
            timing_score = self._calculate_timing_score(wallet)
            stability_score = self._calculate_stability_score(wallet)

            # Weighted average
            weights = {
                'performance': 0.30,  # 30% - Most important
                'consistency': 0.20,  # 20% - Very important
                'volume': 0.15,       # 15%
                'diversity': 0.10,    # 10%
                'timing': 0.15,       # 15% - Early entry bonus
                'stability': 0.10     # 10%
            }

            total_score = (
                performance_score * weights['performance'] +
                consistency_score * weights['consistency'] +
                volume_score * weights['volume'] +
                diversity_score * weights['diversity'] +
                timing_score * weights['timing'] +
                stability_score * weights['stability']
            )

            # Determine trust level
            trust_level = self._determine_trust_level(total_score)

            # Check for red flags
            red_flags = self._check_red_flags(wallet)

            return {
                'address': wallet_address,
                'reputation_score': round(total_score, 2),
                'trust_level': trust_level,
                'verified': total_score >= 70 and len(red_flags) == 0,
                'component_scores': {
                    'performance': round(performance_score, 2),
                    'consistency': round(consistency_score, 2),
                    'volume': round(volume_score, 2),
                    'diversity': round(diversity_score, 2),
                    'timing': round(timing_score, 2),
                    'stability': round(stability_score, 2)
                },
                'red_flags': red_flags,
                'calculated_at': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error calculating reputation for {wallet_address}: {e}")
            return None

    def _calculate_performance_score(self, wallet) -> float:
        """Calculate performance score based on PnL and win rate"""
        # PnL component (0-50 points)
        pnl = wallet.pnl_percent or 0
        pnl_score = min(50, (pnl / 50) * 50)  # Cap at 50 for 50%+ PnL

        # Win rate component (0-50 points)
        win_rate = wallet.win_rate or 0
        win_rate_score = min(50, ((win_rate - 50) / 30) * 50)  # 50% = 0, 80%+ = 50

        return max(0, pnl_score + win_rate_score)

    def _calculate_consistency_score(self, wallet) -> float:
        """Calculate consistency based on bet history variance"""
        total_bets = wallet.total_bets or 0

        if total_bets < 5:
            return 0  # Need minimum history

        # More bets = more proven consistency
        bet_count_score = min(50, (total_bets / 20) * 50)  # 20+ bets = max

        # Win rate should be consistent (not too low, not suspiciously high)
        win_rate = wallet.win_rate or 0
        if 55 <= win_rate <= 85:  # Reasonable range
            win_consistency = 50
        elif 50 <= win_rate < 55 or 85 < win_rate <= 90:
            win_consistency = 30
        else:
            win_consistency = 10

        return (bet_count_score + win_consistency) / 2

    def _calculate_volume_score(self, wallet) -> float:
        """Calculate score based on trading volume"""
        total_volume = wallet.total_volume or 0
        avg_bet_size = wallet.avg_bet_size or 0

        # Volume score (0-50 points)
        # $100k+ volume = max score
        volume_score = min(50, (total_volume / 100000) * 50)

        # Bet size score (0-50 points)
        # $10k+ avg = max score
        bet_size_score = min(50, (avg_bet_size / 10000) * 50)

        return (volume_score + bet_size_score) / 2

    def _calculate_diversity_score(self, wallet) -> float:
        """Calculate score based on market diversity"""
        markets_count = wallet.markets_count or 0
        total_bets = wallet.total_bets or 0

        if total_bets == 0:
            return 0

        # Diversity ratio (spreading bets across markets is good)
        diversity_ratio = markets_count / total_bets if total_bets > 0 else 0

        # Sweet spot: 0.3-0.6 (not too focused, not too scattered)
        if 0.3 <= diversity_ratio <= 0.6:
            diversity_score = 100
        elif 0.2 <= diversity_ratio < 0.3 or 0.6 < diversity_ratio <= 0.7:
            diversity_score = 70
        elif 0.1 <= diversity_ratio < 0.2 or 0.7 < diversity_ratio <= 0.8:
            diversity_score = 40
        else:
            diversity_score = 20

        return diversity_score

    def _calculate_timing_score(self, wallet) -> float:
        """Calculate score based on early entry patterns"""
        # Get wallet's bets
        bets = self.bet_repo.get_wallet_bets(wallet.address)

        if not bets:
            return 50  # Neutral if no bet data

        # Count pre-news bets
        pre_news_count = sum(1 for bet in bets if bet.is_pre_news)
        early_entry_count = sum(1 for bet in bets if bet.is_early_entry)

        total_bets = len(bets)

        # Pre-news ratio
        pre_news_ratio = pre_news_count / total_bets if total_bets > 0 else 0
        early_ratio = early_entry_count / total_bets if total_bets > 0 else 0

        # High pre-news ratio = smart timing
        timing_score = (pre_news_ratio * 60) + (early_ratio * 40)

        return min(100, timing_score)

    def _calculate_stability_score(self, wallet) -> float:
        """Calculate profit stability (avoiding boom/bust patterns)"""
        winning_bets = wallet.winning_bets or 0
        losing_bets = wallet.losing_bets or 0
        total_bets = wallet.total_bets or 0

        if total_bets < 5:
            return 50  # Neutral for new wallets

        # Check for extreme patterns
        if total_bets > 0:
            win_ratio = winning_bets / total_bets

            # Stable wallets have consistent wins, not all-or-nothing
            if 0.55 <= win_ratio <= 0.75:
                stability = 100
            elif 0.50 <= win_ratio < 0.55 or 0.75 < win_ratio <= 0.85:
                stability = 70
            else:
                stability = 30
        else:
            stability = 50

        return stability

    def _determine_trust_level(self, score: float) -> str:
        """Determine trust level from score"""
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "HIGH"
        elif score >= 55:
            return "MEDIUM"
        elif score >= 40:
            return "LOW"
        else:
            return "VERY_LOW"

    def _check_red_flags(self, wallet) -> List[str]:
        """Check for red flags that reduce trust"""
        flags = []

        # Too new with high claims
        wallet_age = (datetime.now() - wallet.first_seen).days if wallet.first_seen else 0
        if wallet_age < 7 and wallet.pnl_percent > 100:
            flags.append("NEW_WALLET_HIGH_CLAIMS")

        # Too few bets for claimed performance
        if wallet.total_bets < 10 and wallet.pnl_percent > 50:
            flags.append("INSUFFICIENT_HISTORY")

        # Suspiciously high win rate
        if wallet.win_rate > 90:
            flags.append("UNREALISTIC_WIN_RATE")

        # No recent activity
        if wallet.last_active:
            days_inactive = (datetime.now() - wallet.last_active).days
            if days_inactive > 30:
                flags.append("INACTIVE")

        # Very focused betting (potential manipulation)
        if wallet.markets_count < 3 and wallet.total_bets > 10:
            flags.append("OVERLY_FOCUSED")

        return flags

    def verify_wallet_claims(
        self,
        wallet_address: str,
        claimed_pnl: float,
        claimed_win_rate: float
    ) -> Dict[str, Any]:
        """
        Verify claimed performance metrics

        Args:
            wallet_address: Wallet address
            claimed_pnl: Claimed PnL percentage
            claimed_win_rate: Claimed win rate

        Returns:
            Verification results
        """
        wallet = self.wallet_repo.get_by_address(wallet_address)

        if not wallet:
            return {
                'verified': False,
                'reason': 'Wallet not found in database'
            }

        # Check if claims match our data (within tolerance)
        pnl_diff = abs(wallet.pnl_percent - claimed_pnl)
        win_rate_diff = abs(wallet.win_rate - claimed_win_rate)

        pnl_verified = pnl_diff <= 5  # Within 5% tolerance
        win_rate_verified = win_rate_diff <= 5  # Within 5% tolerance

        return {
            'verified': pnl_verified and win_rate_verified,
            'actual_pnl': wallet.pnl_percent,
            'claimed_pnl': claimed_pnl,
            'pnl_difference': pnl_diff,
            'pnl_verified': pnl_verified,
            'actual_win_rate': wallet.win_rate,
            'claimed_win_rate': claimed_win_rate,
            'win_rate_difference': win_rate_diff,
            'win_rate_verified': win_rate_verified
        }

    def get_top_reputation_wallets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top wallets by reputation score

        Args:
            limit: Maximum wallets to return

        Returns:
            List of wallet reputation data
        """
        wallets = self.wallet_repo.get_top_performers(limit=limit * 2)  # Get more, then filter

        wallet_reps = []
        for wallet in wallets:
            rep = self.calculate_reputation_score(wallet.address)
            if rep:
                wallet_reps.append(rep)

        # Sort by reputation score
        wallet_reps.sort(key=lambda x: x['reputation_score'], reverse=True)

        return wallet_reps[:limit]
