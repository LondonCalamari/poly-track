"""PolygonScan API integration - Free alternative for blockchain data"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.logger import Logger


class PolygonScanAPI:
    """
    PolygonScan API client for free blockchain data access

    Sign up for free API key at: https://polygonscan.com/apis
    Free tier: 5 calls/second, 100,000 calls/day
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize PolygonScan API client

        Args:
            config: API configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.base_url = "https://api.polygonscan.com/api"
        self.api_key = config.get('api_key', '')

        if not self.api_key:
            self.logger.warning(
                "PolygonScan API key not configured. "
                "Get free key at https://polygonscan.com/apis"
            )

        self.session = requests.Session()

    def get_wallet_transactions(
        self,
        wallet_address: str,
        start_block: int = 0,
        end_block: int = 99999999,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a wallet

        Args:
            wallet_address: Wallet address
            start_block: Starting block number
            end_block: Ending block number
            limit: Maximum transactions to return

        Returns:
            List of transaction dicts
        """
        try:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'startblock': start_block,
                'endblock': end_block,
                'page': 1,
                'offset': limit,
                'sort': 'desc',
                'apikey': self.api_key
            }

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1':
                return data.get('result', [])
            else:
                self.logger.warning(
                    f"PolygonScan API returned status 0: {data.get('message')}"
                )
                return []

        except Exception as e:
            self.logger.error(f"Error fetching transactions for {wallet_address}: {e}")
            return []

    def get_wallet_balance(self, wallet_address: str) -> Optional[float]:
        """
        Get MATIC balance for wallet

        Args:
            wallet_address: Wallet address

        Returns:
            Balance in MATIC or None
        """
        try:
            params = {
                'module': 'account',
                'action': 'balance',
                'address': wallet_address,
                'tag': 'latest',
                'apikey': self.api_key
            }

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1':
                # Convert from wei to MATIC
                wei_balance = int(data.get('result', 0))
                return wei_balance / 1e18
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error fetching balance for {wallet_address}: {e}")
            return None

    def get_token_transactions(
        self,
        wallet_address: str,
        contract_address: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get token (ERC20/ERC1155) transactions for wallet

        Args:
            wallet_address: Wallet address
            contract_address: Optional specific contract to filter
            limit: Maximum transactions to return

        Returns:
            List of token transaction dicts
        """
        try:
            params = {
                'module': 'account',
                'action': 'tokentx',
                'address': wallet_address,
                'page': 1,
                'offset': limit,
                'sort': 'desc',
                'apikey': self.api_key
            }

            if contract_address:
                params['contractaddress'] = contract_address

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1':
                return data.get('result', [])
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error fetching token transactions: {e}")
            return []

    def get_wallet_age(self, wallet_address: str) -> Optional[datetime]:
        """
        Get wallet creation date (first transaction)

        Args:
            wallet_address: Wallet address

        Returns:
            Datetime of first transaction or None
        """
        try:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 1,
                'sort': 'asc',  # Ascending to get first transaction
                'apikey': self.api_key
            }

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1':
                transactions = data.get('result', [])
                if transactions:
                    timestamp = int(transactions[0].get('timeStamp', 0))
                    return datetime.fromtimestamp(timestamp)

            return None

        except Exception as e:
            self.logger.error(f"Error fetching wallet age: {e}")
            return None

    def verify_wallet_exists(self, wallet_address: str) -> bool:
        """
        Check if wallet has any transaction history

        Args:
            wallet_address: Wallet address

        Returns:
            True if wallet exists (has transactions), False otherwise
        """
        try:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'page': 1,
                'offset': 1,
                'apikey': self.api_key
            }

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1':
                transactions = data.get('result', [])
                return len(transactions) > 0

            return False

        except Exception as e:
            self.logger.error(f"Error verifying wallet: {e}")
            return False

    def get_wallet_activity_summary(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get comprehensive wallet activity summary

        Args:
            wallet_address: Wallet address

        Returns:
            Activity summary dict
        """
        transactions = self.get_wallet_transactions(wallet_address, limit=1000)
        balance = self.get_wallet_balance(wallet_address)
        first_tx_date = self.get_wallet_age(wallet_address)

        # Calculate metrics
        total_txs = len(transactions)

        # Count incoming/outgoing
        incoming = sum(1 for tx in transactions if tx.get('to', '').lower() == wallet_address.lower())
        outgoing = sum(1 for tx in transactions if tx.get('from', '').lower() == wallet_address.lower())

        # Calculate total volume (in MATIC)
        total_volume = 0
        for tx in transactions:
            try:
                value = int(tx.get('value', 0))
                total_volume += value / 1e18  # Convert wei to MATIC
            except:
                pass

        # Get recent activity (last 30 days)
        recent_cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        recent_txs = sum(
            1 for tx in transactions
            if int(tx.get('timeStamp', 0)) >= recent_cutoff
        )

        return {
            'address': wallet_address,
            'balance_matic': balance,
            'total_transactions': total_txs,
            'incoming_transactions': incoming,
            'outgoing_transactions': outgoing,
            'total_volume_matic': round(total_volume, 4),
            'first_activity': first_tx_date,
            'recent_activity_30d': recent_txs,
            'is_active': recent_txs > 0
        }
