"""Add real wallet addresses to track

Run this script to manually add wallet addresses you want to track.
This bypasses the Polysights API and lets you add wallets directly.

Usage:
    python add_wallets.py 0x1234... 0x5678... 0xabcd...
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.models import init_database
from src.database.repository import WalletRepository
from src.utils.logger import get_logger


def add_wallet(wallet_address: str, db, logger):
    """Add a wallet address to tracking"""
    session = db.get_session()
    wallet_repo = WalletRepository(session)

    # Check if already exists
    existing = wallet_repo.get_by_address(wallet_address)
    if existing:
        logger.info(f"✓ Wallet already tracked: {wallet_address}")
        logger.info(f"  PnL: {existing.pnl_percent}% | Win Rate: {existing.win_rate}%")
        return existing

    # Create new wallet
    wallet = wallet_repo.create(wallet_address)
    logger.info(f"✓ Added wallet: {wallet_address}")
    logger.info(f"  Polymarket: https://polymarket.com/profile/{wallet_address}")
    logger.info(f"  PolygonScan: https://polygonscan.com/address/{wallet_address}")

    return wallet


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_wallets.py <wallet_address> [wallet_address...]")
        print("\nExamples:")
        print("  python add_wallets.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        print("  python add_wallets.py 0x123... 0x456... 0x789...")
        print("\nTo find wallet addresses:")
        print("  1. Visit https://polymarket.com/leaderboard")
        print("  2. Click on a top trader")
        print("  3. Copy the address from the URL")
        sys.exit(1)

    logger = get_logger()
    db = init_database()

    wallet_addresses = sys.argv[1:]

    print(f"\nAdding {len(wallet_addresses)} wallet(s) to tracking...\n")

    for address in wallet_addresses:
        # Basic validation
        if not address.startswith('0x') or len(address) != 42:
            logger.error(f"✗ Invalid address format: {address}")
            logger.error(f"  Address must start with 0x and be 42 characters long")
            continue

        add_wallet(address, db, logger)

    print("\n✓ Done! Run 'python main.py --list-wallets' to see tracked wallets")
    print("✓ Run 'python main.py --scan-once' to fetch their data from Polymarket")


if __name__ == "__main__":
    main()
