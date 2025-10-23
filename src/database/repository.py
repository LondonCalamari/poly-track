"""Data access layer for EdgeCopy v1"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from .models import Wallet, Market, Bet, Signal, ScanLog


class WalletRepository:
    """Repository for wallet data access"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, address: str, **kwargs) -> Wallet:
        """Create new wallet"""
        wallet = Wallet(address=address, **kwargs)
        self.session.add(wallet)
        self.session.commit()
        return wallet

    def get_by_address(self, address: str) -> Optional[Wallet]:
        """Get wallet by address"""
        return self.session.query(Wallet).filter_by(address=address).first()

    def get_or_create(self, address: str, **kwargs) -> Wallet:
        """Get existing wallet or create new one"""
        wallet = self.get_by_address(address)
        if not wallet:
            wallet = self.create(address, **kwargs)
        return wallet

    def get_smart_wallets(self, min_pnl: float = 30, min_win_rate: float = 60) -> List[Wallet]:
        """Get all smart wallets meeting criteria"""
        return self.session.query(Wallet).filter(
            and_(
                Wallet.is_smart_wallet == True,
                Wallet.pnl_percent >= min_pnl,
                Wallet.win_rate >= min_win_rate
            )
        ).all()

    def get_active_wallets(self, days: int = 30) -> List[Wallet]:
        """Get wallets active in last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        return self.session.query(Wallet).filter(
            Wallet.last_active >= cutoff
        ).all()

    def get_insider_patterns(self) -> List[Wallet]:
        """Get wallets matching insider pattern"""
        return self.session.query(Wallet).filter(
            Wallet.is_insider_pattern == True
        ).all()

    def update_metrics(self, wallet_id: int, metrics: Dict[str, Any]) -> Wallet:
        """Update wallet metrics"""
        wallet = self.session.query(Wallet).get(wallet_id)
        if wallet:
            for key, value in metrics.items():
                setattr(wallet, key, value)
            wallet.updated_at = datetime.now()
            self.session.commit()
        return wallet

    def get_top_performers(self, limit: int = 20, order_by: str = 'pnl_percent') -> List[Wallet]:
        """Get top performing wallets"""
        order_column = getattr(Wallet, order_by, Wallet.pnl_percent)
        return self.session.query(Wallet).filter(
            Wallet.is_smart_wallet == True
        ).order_by(desc(order_column)).limit(limit).all()


class MarketRepository:
    """Repository for market data access"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, market_id: str, **kwargs) -> Market:
        """Create new market"""
        market = Market(market_id=market_id, **kwargs)
        self.session.add(market)
        self.session.commit()
        return market

    def get_by_market_id(self, market_id: str) -> Optional[Market]:
        """Get market by market_id"""
        return self.session.query(Market).filter_by(market_id=market_id).first()

    def get_or_create(self, market_id: str, **kwargs) -> Market:
        """Get existing market or create new one"""
        market = self.get_by_market_id(market_id)
        if not market:
            market = self.create(market_id, **kwargs)
        return market

    def get_active_markets(self) -> List[Market]:
        """Get all active markets"""
        return self.session.query(Market).filter(
            Market.is_active == True
        ).all()

    def get_high_liquidity_markets(self, min_liquidity: float = 300000) -> List[Market]:
        """Get markets with high liquidity"""
        return self.session.query(Market).filter(
            and_(
                Market.is_active == True,
                Market.liquidity >= min_liquidity
            )
        ).all()

    def update(self, market_id: str, updates: Dict[str, Any]) -> Market:
        """Update market data"""
        market = self.get_by_market_id(market_id)
        if market:
            for key, value in updates.items():
                setattr(market, key, value)
            market.updated_at = datetime.now()
            self.session.commit()
        return market


class BetRepository:
    """Repository for bet data access"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, wallet_id: int, market_id: int, **kwargs) -> Bet:
        """Create new bet"""
        bet = Bet(wallet_id=wallet_id, market_id=market_id, **kwargs)
        self.session.add(bet)
        self.session.commit()
        return bet

    def get_by_transaction(self, tx_hash: str) -> Optional[Bet]:
        """Get bet by transaction hash"""
        return self.session.query(Bet).filter_by(transaction_hash=tx_hash).first()

    def get_wallet_bets(self, wallet_address: str) -> List[Bet]:
        """Get all bets for a wallet"""
        return self.session.query(Bet).join(Wallet).filter(
            Wallet.address == wallet_address
        ).all()

    def get_market_bets(self, market_id: str, hours: int = 24) -> List[Bet]:
        """Get recent bets for a market"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return self.session.query(Bet).join(Market).filter(
            and_(
                Market.market_id == market_id,
                Bet.bet_timestamp >= cutoff
            )
        ).all()

    def get_pre_news_bets(self, market_id: str) -> List[Bet]:
        """Get pre-news bets for a market"""
        return self.session.query(Bet).join(Market).filter(
            and_(
                Market.market_id == market_id,
                Bet.is_pre_news == True
            )
        ).all()


class SignalRepository:
    """Repository for signal data access"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, market_id: int, **kwargs) -> Signal:
        """Create new signal"""
        signal = Signal(market_id=market_id, **kwargs)
        self.session.add(signal)
        self.session.commit()
        return signal

    def get_recent_signals(self, hours: int = 24, min_score: int = 0) -> List[Signal]:
        """Get recent signals"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return self.session.query(Signal).filter(
            and_(
                Signal.signal_timestamp >= cutoff,
                Signal.perfect_bet_score >= min_score
            )
        ).order_by(desc(Signal.signal_timestamp)).all()

    def get_validated_signals(self) -> List[Signal]:
        """Get validated signals without red flags"""
        return self.session.query(Signal).filter(
            and_(
                Signal.is_validated == True,
                Signal.has_red_flags == False
            )
        ).all()

    def get_pending_signals(self) -> List[Signal]:
        """Get signals awaiting user action"""
        return self.session.query(Signal).filter(
            Signal.user_action == None
        ).all()

    def update_user_action(self, signal_id: int, action: str, notes: str = None):
        """Update signal with user action"""
        signal = self.session.query(Signal).get(signal_id)
        if signal:
            signal.user_action = action
            if notes:
                signal.user_notes = notes
            signal.updated_at = datetime.now()
            self.session.commit()
        return signal

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get signal performance statistics"""
        total_signals = self.session.query(func.count(Signal.id)).scalar()
        validated = self.session.query(func.count(Signal.id)).filter(
            Signal.is_validated == True
        ).scalar()
        with_red_flags = self.session.query(func.count(Signal.id)).filter(
            Signal.has_red_flags == True
        ).scalar()

        acted_on = self.session.query(func.count(Signal.id)).filter(
            Signal.user_action == 'ENTERED'
        ).scalar()

        avg_score = self.session.query(func.avg(Signal.perfect_bet_score)).scalar()

        return {
            'total_signals': total_signals or 0,
            'validated': validated or 0,
            'with_red_flags': with_red_flags or 0,
            'acted_on': acted_on or 0,
            'avg_perfect_bet_score': round(avg_score or 0, 2)
        }


class ScanLogRepository:
    """Repository for scan log data access"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, scan_type: str, **kwargs) -> ScanLog:
        """Create new scan log"""
        log = ScanLog(scan_type=scan_type, **kwargs)
        self.session.add(log)
        self.session.commit()
        return log

    def get_recent_scans(self, limit: int = 50) -> List[ScanLog]:
        """Get recent scan logs"""
        return self.session.query(ScanLog).order_by(
            desc(ScanLog.scan_timestamp)
        ).limit(limit).all()

    def get_last_scan(self, scan_type: str = None) -> Optional[ScanLog]:
        """Get last scan log, optionally filtered by type"""
        query = self.session.query(ScanLog)
        if scan_type:
            query = query.filter_by(scan_type=scan_type)
        return query.order_by(desc(ScanLog.scan_timestamp)).first()
