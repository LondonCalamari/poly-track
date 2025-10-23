"""Database models for EdgeCopy v1"""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Wallet(Base):
    """Smart wallet model"""

    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True)
    address = Column(String(42), unique=True, nullable=False, index=True)

    # Performance metrics
    pnl_percent = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    avg_bet_size = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    profit_usd = Column(Float, default=0.0)

    # Activity metrics
    total_bets = Column(Integer, default=0)
    winning_bets = Column(Integer, default=0)
    losing_bets = Column(Integer, default=0)
    markets_count = Column(Integer, default=0)

    # Timing metrics
    first_seen = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    last_scanned = Column(DateTime, default=datetime.now)

    # Classification
    is_smart_wallet = Column(Boolean, default=False)
    is_insider_pattern = Column(Boolean, default=False)
    reputation_score = Column(Float, default=0.0)

    # Metadata
    notes = Column(Text)
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    bets = relationship("Bet", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Wallet {self.address[:10]}... PnL:{self.pnl_percent}% WR:{self.win_rate}%>"


class Market(Base):
    """Polymarket market model"""

    __tablename__ = 'markets'

    id = Column(Integer, primary_key=True)
    market_id = Column(String(100), unique=True, nullable=False, index=True)

    # Market info
    title = Column(String(500))
    description = Column(Text)
    category = Column(String(100))
    end_date = Column(DateTime)

    # Market metrics
    liquidity = Column(Float, default=0.0)
    volume = Column(Float, default=0.0)
    active_traders = Column(Integer, default=0)

    # Odds/Probability
    current_probability = Column(Float)
    opening_probability = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    resolution = Column(String(50))

    # Tracking
    first_detected = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    bets = relationship("Bet", back_populates="market", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="market", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Market {self.market_id} {self.title[:30]}...>"


class Bet(Base):
    """Individual bet/trade model"""

    __tablename__ = 'bets'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    wallet_id = Column(Integer, ForeignKey('wallets.id'), nullable=False)
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False)

    # Bet details
    bet_amount = Column(Float, nullable=False)
    bet_side = Column(String(10))  # YES or NO
    odds_at_bet = Column(Float)
    transaction_hash = Column(String(66), unique=True)

    # Timing
    bet_timestamp = Column(DateTime, nullable=False, index=True)
    hours_before_event = Column(Float)

    # Outcome
    is_winning = Column(Boolean)
    profit_loss = Column(Float)
    closed_at = Column(DateTime)

    # Classification
    is_pre_news = Column(Boolean, default=False)
    is_early_entry = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    wallet = relationship("Wallet", back_populates="bets")
    market = relationship("Market", back_populates="bets")

    def __repr__(self):
        return f"<Bet ${self.bet_amount} on {self.bet_side}>"


class Signal(Base):
    """Trading signal model"""

    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False)

    # Signal info
    signal_type = Column(String(50))  # e.g., "MULTI_WALLET_OVERLAP"
    confidence_score = Column(Float, default=0.0)
    perfect_bet_score = Column(Integer, default=0)

    # Wallet overlap
    wallet_count = Column(Integer, default=0)
    wallet_addresses = Column(JSON)  # List of addresses
    avg_wallet_pnl = Column(Float)

    # Market conditions
    market_liquidity = Column(Float)
    current_odds = Column(Float)
    is_consolidation = Column(Boolean, default=False)

    # Timing
    signal_timestamp = Column(DateTime, default=datetime.now, index=True)
    event_timestamp = Column(DateTime)
    hours_before_event = Column(Float)

    # Validation
    is_validated = Column(Boolean, default=False)
    has_red_flags = Column(Boolean, default=False)
    red_flags = Column(JSON)

    # User action
    user_action = Column(String(20))  # IGNORED, ENTERED, PASSED
    user_notes = Column(Text)

    # Outcome tracking
    entry_price = Column(Float)
    exit_price = Column(Float)
    profit_loss = Column(Float)
    closed_at = Column(DateTime)

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    market = relationship("Market", back_populates="signals")

    def __repr__(self):
        return f"<Signal {self.signal_type} score:{self.perfect_bet_score}/6 wallets:{self.wallet_count}>"


class ScanLog(Base):
    """Scan history log"""

    __tablename__ = 'scan_logs'

    id = Column(Integer, primary_key=True)

    scan_timestamp = Column(DateTime, default=datetime.now, index=True)
    scan_type = Column(String(50))  # WALLET_SCAN, MARKET_SCAN, SIGNAL_DETECTION

    # Results
    items_scanned = Column(Integer, default=0)
    items_added = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    signals_generated = Column(Integer, default=0)

    # Performance
    duration_seconds = Column(Float)
    errors_count = Column(Integer, default=0)

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ScanLog {self.scan_type} at {self.scan_timestamp}>"


class Database:
    """Database manager"""

    def __init__(self, db_path: str = "sqlite:///./data/polytrack.db"):
        """
        Initialize database

        Args:
            db_path: Database connection string
        """
        self.db_path = db_path
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drop all tables (use with caution)"""
        Base.metadata.drop_all(self.engine)

    def get_session(self):
        """Get database session"""
        return self.Session()


def init_database(db_path: str = "sqlite:///./data/polytrack.db") -> Database:
    """
    Initialize database and create tables

    Args:
        db_path: Database connection string

    Returns:
        Database instance
    """
    db = Database(db_path)
    db.create_tables()
    return db
