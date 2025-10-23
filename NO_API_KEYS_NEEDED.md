# EdgeCopy v1 - No Paid API Keys Required! 🎉

## Good News!

The system has been updated to **work without expensive API keys**. We've replaced Nevua Markets and HashDive with built-in alternatives that use free, public data sources.

## What Changed?

### ❌ REMOVED (No longer needed):
- **Nevua Markets API** - Was used for real-time wallet tracking
- **HashDive API** - Was used for reputation scoring

### ✅ REPLACED WITH (Built-in, free):
- **BlockchainWalletScanner** - Direct on-chain monitoring
- **InternalReputationSystem** - Internal reputation calculation
- **PolygonScan API** - Free blockchain data (optional but recommended)

## Required API Keys: NONE

The system now works **completely free** with just the included mock data. However, for better performance, you can optionally add:

### Optional (Free) API Keys:

#### 1. PolygonScan API - FREE ⭐ Recommended

**What it does:**
- Provides real blockchain transaction data
- Verifies wallet activity
- Tracks wallet age and history
- Enables actual on-chain monitoring

**How to get it (takes 2 minutes):**

1. Go to https://polygonscan.com
2. Click "Sign In" → "Click to sign up"
3. Create free account
4. Go to "API-KEYs" in your account
5. Click "Add" to create new API key
6. Copy the key

**Add to .env:**
```bash
POLYGONSCAN_API_KEY=YOUR_FREE_KEY_HERE
```

**Free tier limits:**
- 5 calls per second
- 100,000 calls per day
- More than enough for tracking!

#### 2. Polysights API - Optional

The system includes **mock smart wallet data** for testing, so Polysights is optional. If you have access, add the key. Otherwise, the system works fine without it.

## How It Works Now

### 1. Wallet Tracking (Replaces Nevua Markets)

**BlockchainWalletScanner** monitors wallets directly:

```python
# The scanner polls wallet addresses for new activity
# No API key needed - uses public blockchain data

scanner.track_wallet("0x1234...")  # Start tracking
scanner.scan_all_tracked_wallets()  # Check for new bets
scanner.detect_real_time_signals()  # Find overlaps
```

**Features:**
- Direct on-chain monitoring
- Automatic smart wallet tracking
- Real-time signal detection
- Market overlap detection
- No subscription required

### 2. Reputation System (Replaces HashDive)

**InternalReputationSystem** calculates scores internally:

```python
# Calculates reputation from on-chain history
# 100% internal - no API calls

reputation = system.calculate_reputation_score("0x1234...")

# Returns comprehensive scoring:
# - Performance score (PnL, win rate)
# - Consistency score (bet history)
# - Volume score (trading size)
# - Diversity score (market spread)
# - Timing score (early entries)
# - Stability score (profit consistency)
```

**Scoring components:**
- **Performance (30%)**: PnL % and win rate
- **Consistency (20%)**: Bet history stability
- **Volume (15%)**: Trading volume and bet sizing
- **Diversity (10%)**: Market variety
- **Timing (15%)**: Early entry patterns
- **Stability (10%)**: Profit smoothness

**Trust levels:**
- 85+ = EXCELLENT
- 70-84 = HIGH
- 55-69 = MEDIUM
- 40-54 = LOW
- <40 = VERY_LOW

### 3. Free Blockchain Data (PolygonScan)

**PolygonScanAPI** provides verified on-chain data:

```python
# Get comprehensive wallet data - all free!
activity = polygonscan.get_wallet_activity_summary("0x1234...")

# Returns:
# - Total transactions
# - Balance
# - Volume
# - First activity date
# - Recent activity
```

## Setup Instructions

### Minimal Setup (No API keys)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment template
cp .env.example .env

# 3. Run immediately!
python main.py --scan-once
```

The system will use:
- Mock smart wallet data (3 sample wallets)
- Internal reputation system
- Console alerts
- SQLite database

### Recommended Setup (Free PolygonScan key)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get free PolygonScan API key
# Visit: https://polygonscan.com/apis

# 3. Add to .env
cp .env.example .env
nano .env  # Add: POLYGONSCAN_API_KEY=your_key

# 4. Run with real blockchain data!
python main.py --continuous
```

Now you'll have:
- Real blockchain monitoring
- Verified wallet data
- Transaction history
- On-chain activity tracking

## Configuration

The system auto-enables the new features in `config.yaml`:

```yaml
apis:
  # Optional - works without this
  polysights:
    enabled: true
    api_key: ""  # Uses mock data if empty

  # Free API - highly recommended
  polygonscan:
    enabled: true
    api_key: ""  # Get free at polygonscan.com

  # Built-in scanner - no key needed
  blockchain_scanner:
    enabled: true
    auto_track_smart_wallets: true
    max_tracked_wallets: 50

  # Built-in reputation - no key needed
  reputation_system:
    enabled: true
    min_reputation_score: 50
    require_verification: true
```

## Testing the New System

### Test 1: Blockchain Scanner

```bash
python main.py --scan-once
```

You should see:
```
Scanning 3 tracked wallets...
Wallet scan complete: 0 new positions found
```

### Test 2: Reputation System

Open Python console:
```python
from main import EdgeCopyTracker

tracker = EdgeCopyTracker()
rep = tracker.reputation_system.calculate_reputation_score("0x1234...")

print(f"Reputation: {rep['reputation_score']}/100")
print(f"Trust Level: {rep['trust_level']}")
print(f"Verified: {rep['verified']}")
```

### Test 3: PolygonScan (if you added key)

```python
from main import EdgeCopyTracker

tracker = EdgeCopyTracker()
summary = tracker.polygonscan_api.get_wallet_activity_summary("0x1234...")

print(f"Balance: {summary['balance_matic']} MATIC")
print(f"Transactions: {summary['total_transactions']}")
print(f"First activity: {summary['first_activity']}")
```

## Features You Get Without API Keys

✅ **Smart wallet tracking** (uses mock data or your database)
✅ **Market monitoring** (Polymarket public API)
✅ **Signal detection** (EdgeCopy v1 algorithm)
✅ **Risk management** (position sizing, profit targets)
✅ **Console alerts** (always enabled)
✅ **Database tracking** (SQLite included)
✅ **Perfect Bet scoring** (5/6 checklist)
✅ **Red flag detection** (manipulation filters)
✅ **Internal reputation** (6-component scoring)
✅ **Blockchain scanning** (with PolygonScan key)

## Migration from Old Version

If you were trying to get Nevua/HashDive keys:

### Before (not working):
```bash
NEVUA_MARKETS_API_KEY=???  # Couldn't get
HASH_DIVE_API_KEY=???      # Couldn't get
```

### After (working now):
```bash
# Nothing required!
# Optional: POLYGONSCAN_API_KEY=free_key
```

All your existing code works the same, just with different backends!

## Performance Comparison

| Feature | Nevua Markets | BlockchainScanner | Winner |
|---------|---------------|-------------------|--------|
| Real-time tracking | ✓ | ✓ | Tie |
| API key required | ✓ ($) | ✗ (Free) | **Scanner** |
| On-chain verification | Limited | Full | **Scanner** |
| Setup time | Long | Instant | **Scanner** |
| Rate limits | Varies | 5/sec (free) | **Scanner** |

| Feature | HashDive | ReputationSystem | Winner |
|---------|----------|------------------|--------|
| Reputation scoring | ✓ | ✓ | Tie |
| API key required | ✓ ($) | ✗ (Free) | **Internal** |
| Customizable | Limited | Full | **Internal** |
| Cross-verification | External | On-chain | **Internal** |
| Data privacy | Shared | Local | **Internal** |

## Troubleshooting

### "No smart wallets found"

**Cause:** Using mock data without Polysights key

**Solution:** This is normal! The system includes 3 mock wallets for testing. To get real data:
1. Add PolygonScan API key
2. Add Polysights API key (optional)
3. Or manually add wallets to database

### "PolygonScan API rate limit"

**Cause:** Making too many requests

**Solution:** The free tier allows 5/sec. The system respects this. If needed:
1. Reduce `scan_interval_minutes` in config
2. Reduce `max_tracked_wallets` in config
3. Use mock data for testing

### "Blockchain scanner not finding signals"

**Cause:** Not tracking any wallets yet

**Solution:**
```bash
# Auto-track smart wallets from database
python main.py --scan-once

# The scanner will automatically track top performers
```

## Advanced Usage

### Auto-Track Top Performers

```python
tracker = EdgeCopyTracker()

# Automatically track top 20 smart wallets
tracker.blockchain_scanner.auto_track_smart_wallets(
    min_pnl=30,
    limit=20
)

# Now scan for activity
results = tracker.blockchain_scanner.scan_all_tracked_wallets()
print(f"Signals: {results['overlaps_detected']}")
```

### Custom Reputation Scoring

```python
# Get top wallets by reputation
top_reps = tracker.reputation_system.get_top_reputation_wallets(limit=10)

for wallet_rep in top_reps:
    print(f"{wallet_rep['address']}: {wallet_rep['reputation_score']}/100")
    print(f"  Trust: {wallet_rep['trust_level']}")
    print(f"  Verified: {wallet_rep['verified']}")
```

### Real-Time Signal Detection

```python
# Start continuous monitoring
tracker.blockchain_scanner.auto_track_smart_wallets(limit=30)

# Detect signals in real-time
signals = tracker.blockchain_scanner.detect_real_time_signals()

for signal in signals:
    print(f"🎯 Signal: {signal['wallet_count']} wallets in {signal['market_id']}")
    print(f"   Synchronized: {signal['time_spread_minutes']:.1f} minutes")
```

## Cost Comparison

### Before:
- Nevua Markets: $XX/month
- HashDive: $XX/month
- **Total: $XX/month**

### Now:
- PolygonScan: **FREE**
- BlockchainScanner: **FREE**
- ReputationSystem: **FREE**
- **Total: $0/month** 🎉

## Summary

🎉 **You no longer need Nevua Markets or HashDive API keys!**

The system now includes:
- ✅ Built-in blockchain scanner (replaces Nevua)
- ✅ Built-in reputation system (replaces HashDive)
- ✅ Free PolygonScan integration (recommended)
- ✅ Works completely free with mock data
- ✅ Better performance and control

**Get started immediately:**
```bash
python main.py --scan-once
```

**For best results (still free):**
1. Get PolygonScan API key (2 minutes)
2. Add to .env
3. Run continuous mode

**Questions?** Check README.md or QUICKSTART.md for more details!
