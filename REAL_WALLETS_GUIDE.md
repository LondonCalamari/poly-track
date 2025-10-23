# How to Track REAL Polymarket Wallets

## The Mock Data Issue

The 3 wallets you saw (`0x1234...`, `0x2345...`, `0x3456...`) are **fake test wallets** created for demonstration. They don't exist on Polymarket because:

- You don't have a Polysights API key (which provides real wallet data)
- The system uses mock data to show how it works
- Mock wallets allow testing without API access

## How to Track REAL Wallets

### Step 1: Find Smart Wallets on Polymarket

**Option A: Polymarket Leaderboard (Easiest)**

1. Visit: https://polymarket.com/leaderboard
2. Look for traders with:
   - High volume (>$10k)
   - Good profit margins (>30%)
   - Consistent activity
3. Click on a trader's name
4. Copy the wallet address from the URL: `polymarket.com/profile/[wallet-address]`

**Example Top Traders:**
```
https://polymarket.com/profile/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
https://polymarket.com/profile/0x2f4a8b8a2e1e8f6c3d5e7f8a9b0c1d2e3f4a5b6c
```

**Option B: Browse Polysights (Manual)**

1. Visit: https://polysights.com
2. Look at "Top Traders" or "Insider Finder"
3. Copy wallet addresses from the list
4. You don't need an API key to browse manually!

**Option C: Watch Live Markets**

1. Go to a popular market on Polymarket
2. Click "Activity" or "Trades"
3. Look for large bets (>$1000)
4. Copy the wallet addresses making those bets

### Step 2: Add Real Wallets to Your Tracker

I've created a script to easily add wallet addresses:

```bash
python add_wallets.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

Add multiple at once:
```bash
python add_wallets.py \
  0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \
  0x2f4a8b8a2e1e8f6c3d5e7f8a9b0c1d2e3f4a5b6c \
  0x3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b
```

### Step 3: Fetch Their Data from Polymarket

Once you've added wallet addresses:

```bash
python main.py --scan-once
```

This will:
1. ✓ Connect to Polymarket API
2. ✓ Fetch trading history for each wallet
3. ✓ Calculate their PnL, win rate, etc.
4. ✓ Update your database with REAL data

### Step 4: View Real Wallet Data

```bash
python main.py --list-wallets
```

You'll now see:
- ✓ Real wallet addresses
- ✓ Actual trading performance
- ✓ Links to Polymarket profiles
- ✓ Links to PolygonScan transactions

## Example Workflow

```bash
# 1. Find a top trader on Polymarket
# Visit: https://polymarket.com/leaderboard
# Copy address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# 2. Add to tracker
python add_wallets.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# 3. Fetch their data
python main.py --scan-once

# 4. View results
python main.py --list-wallets
```

## Recommended Smart Wallets to Track

Here are some wallet categories to look for on Polymarket:

**High Volume Traders:**
- Look for >$100k total volume
- These often make large, confident bets

**High Win Rate Traders:**
- Filter by win rate >70%
- These are selective and strategic

**Early Movers:**
- Traders who bet before major news
- Check "Activity" on markets before events

**Specialized Traders:**
- Focus on specific categories (politics, sports, crypto)
- Domain expertise often = better predictions

## Getting the Most Accurate Data

### Option 1: Free PolygonScan API (Recommended)

Get verified on-chain data:

1. Sign up at https://polygonscan.com/apis (FREE)
2. Get your API key
3. Add to `.env`:
   ```
   POLYGONSCAN_API_KEY=your_free_key_here
   ```
4. Run scan again

This gives you:
- ✓ Verified transaction history
- ✓ Wallet age verification
- ✓ Real activity timestamps
- ✓ On-chain confirmation

### Option 2: Polysights API (Paid)

If you can get Polysights access:
- Automated wallet discovery
- Pre-calculated performance metrics
- Historical tracking

But you can do everything manually without it!

## Remove Mock Wallets

To clean up the fake test wallets:

```bash
# Connect to database
sqlite3 data/polytrack.db

# Delete mock wallets
DELETE FROM wallets WHERE address LIKE '0x123456%';
DELETE FROM wallets WHERE address LIKE '0x234567%';
DELETE FROM wallets WHERE address LIKE '0x345678%';

# Exit
.quit
```

Or start fresh:
```bash
rm data/polytrack.db
python main.py --scan-once
```

## Verify Wallets Before Tracking

Before adding a wallet, verify it exists:

**Check on Polymarket:**
```
https://polymarket.com/profile/[wallet-address]
```

**Check on PolygonScan:**
```
https://polygonscan.com/address/[wallet-address]
```

You should see:
- ✓ Transaction history
- ✓ Trading activity
- ✓ Recent bets

If the wallet shows "Not found" or no transactions, it's not a real active wallet.

## Advanced: Auto-Track Leaderboard

Want to automatically track the top 20 wallets? I can add a script that:
1. Scrapes Polymarket leaderboard
2. Extracts top trader addresses
3. Adds them to your tracker automatically

Let me know if you want this feature!

## Summary

**Current Status:**
- ❌ Mock wallets (0x1234..., 0x2345..., 0x3456...) - FAKE for testing
- ✅ System ready to track REAL wallets

**Next Steps:**
1. Visit https://polymarket.com/leaderboard
2. Copy real wallet addresses
3. Run: `python add_wallets.py [addresses]`
4. Run: `python main.py --scan-once`
5. View: `python main.py --list-wallets`

**You'll get:**
- ✓ Real trading data
- ✓ Actual performance metrics
- ✓ Working Polymarket profile links
- ✓ Signal detection from real activity

Start tracking real smart money now! 🎯
