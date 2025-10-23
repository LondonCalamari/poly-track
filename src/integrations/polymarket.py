"""Polymarket API integration"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.logger import Logger


class PolymarketAPI:
    """
    Polymarket API client for fetching market and trading data

    Endpoints:
    - Markets data
    - Trading activity
    - Wallet positions
    - Event outcomes
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize Polymarket API client

        Args:
            config: API configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.base_url = "https://gamma-api.polymarket.com"
        self.rpc_url = config.get('rpc_url', 'https://polygon-rpc.com')
        self.rate_limit = config.get('rate_limit_per_minute', 120)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdgeCopy-v1',
            'Content-Type': 'application/json'
        })

    def get_markets(self, limit: int = 100, offset: int = 0, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch active markets

        Args:
            limit: Number of markets to fetch
            offset: Pagination offset
            active_only: Only fetch active markets

        Returns:
            List of market data dicts
        """
        try:
            params = {
                'limit': limit,
                'offset': offset
            }

            if active_only:
                params['closed'] = 'false'

            response = self.session.get(
                f"{self.base_url}/markets",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            markets = response.json()

            # Transform to standard format
            return [self._transform_market_data(m) for m in markets]

        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}", exc_info=True)
            return []

    def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific market data

        Args:
            market_id: Market ID

        Returns:
            Market data dict or None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/markets/{market_id}",
                timeout=30
            )
            response.raise_for_status()

            market = response.json()
            return self._transform_market_data(market)

        except Exception as e:
            self.logger.error(f"Error fetching market {market_id}: {e}")
            return None

    def get_market_trades(self, market_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a market

        Args:
            market_id: Market ID
            limit: Number of trades to fetch

        Returns:
            List of trade data dicts
        """
        try:
            response = self.session.get(
                f"{self.base_url}/markets/{market_id}/trades",
                params={'limit': limit},
                timeout=30
            )
            response.raise_for_status()

            trades = response.json()
            return [self._transform_trade_data(t) for t in trades]

        except Exception as e:
            self.logger.error(f"Error fetching trades for {market_id}: {e}")
            return []

    def get_wallet_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Fetch positions for a wallet

        Args:
            wallet_address: Wallet address

        Returns:
            List of position data dicts
        """
        try:
            response = self.session.get(
                f"{self.base_url}/positions",
                params={'user': wallet_address},
                timeout=30
            )
            response.raise_for_status()

            positions = response.json()
            return positions

        except Exception as e:
            self.logger.error(f"Error fetching positions for {wallet_address}: {e}")
            return []

    def _transform_market_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw market data to standard format"""
        return {
            'market_id': raw_data.get('id') or raw_data.get('condition_id'),
            'title': raw_data.get('question') or raw_data.get('title', ''),
            'description': raw_data.get('description', ''),
            'category': raw_data.get('category', ''),
            'end_date': self._parse_timestamp(raw_data.get('end_date') or raw_data.get('endDate')),
            'liquidity': float(raw_data.get('liquidity', 0)),
            'volume': float(raw_data.get('volume', 0)),
            'active_traders': int(raw_data.get('numTraders', 0)),
            'current_probability': self._parse_probability(raw_data.get('outcomePrices', [])),
            'is_active': raw_data.get('active', True),
            'is_resolved': raw_data.get('closed', False),
            'resolution': raw_data.get('outcome'),
            'metadata': raw_data
        }

    def _transform_trade_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw trade data to standard format"""
        return {
            'transaction_hash': raw_data.get('transactionHash'),
            'wallet_address': raw_data.get('user') or raw_data.get('maker'),
            'bet_amount': float(raw_data.get('size', 0)),
            'bet_side': raw_data.get('side', 'YES'),
            'odds_at_bet': float(raw_data.get('price', 0)),
            'bet_timestamp': self._parse_timestamp(raw_data.get('timestamp')),
            'metadata': raw_data
        }

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if not timestamp:
            return None

        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return None
        except Exception:
            return None

    def _parse_probability(self, outcome_prices: List) -> Optional[float]:
        """Parse probability from outcome prices"""
        if not outcome_prices or len(outcome_prices) == 0:
            return None

        try:
            # Typically first outcome is YES
            return float(outcome_prices[0]) if outcome_prices else None
        except Exception:
            return None
