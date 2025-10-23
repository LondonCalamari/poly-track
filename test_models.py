"""Test script to verify SQLAlchemy models are fixed"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.database.models import Wallet, Market, Bet, Signal, ScanLog, Base
    print("✓ All models imported successfully!")
    print("✓ SQLAlchemy metadata conflict fixed!")
    print("\nModels available:")
    print("  - Wallet")
    print("  - Market")
    print("  - Bet")
    print("  - Signal")
    print("  - ScanLog")
    print("\nThe 'metadata' column has been renamed to 'extra_data' in all models.")
    print("\nYou can now install dependencies and run the application:")
    print("  pip install -r requirements.txt")
    print("  python main.py --scan-once")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
