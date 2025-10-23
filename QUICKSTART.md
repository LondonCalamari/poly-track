# EdgeCopy v1 - Quick Start Guide

Get started tracking smart wallets on Polymarket in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd poly-track

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
nano .env  # Edit with your API keys (optional for testing)
```

## Configuration

Edit `config.yaml` to customize your tracking criteria:

```yaml
# Smart Wallet Criteria
wallet_criteria:
  min_pnl_percent: 30     # Minimum 30% ROI
  min_win_rate: 60        # Minimum 60% win rate
  min_avg_bet_size: 10000 # Minimum $10k average bet

# Signal Detection
signal_detection:
  min_wallet_overlap: 2       # Minimum 2 wallets
  min_liquidity: 300000       # Minimum $300k liquidity
  sync_time_window_minutes: 30  # Within 30 minutes
```

## Basic Usage

### Run Single Scan

```bash
python main.py --scan-once
```

This will:
1. Scan for smart wallets
2. Check active markets
3. Detect trading signals
4. Display results in console

### Run Continuous Monitoring

```bash
python main.py --continuous
```

This starts the EdgeCopy v1 system in continuous mode, scanning every 10 minutes (configurable).

### List Smart Wallets

```bash
python main.py --list-wallets
```

Shows all tracked smart wallets with their performance metrics.

### Show Recent Signals

```bash
python main.py --show-signals
```

Displays recent trading signals detected by the system.

### Test Alerts

```bash
python main.py --test-alerts
```

Test your configured alert channels (Telegram, Webhook, Console).

## Understanding Signals

When EdgeCopy detects a signal, it shows:

```
🎯 EDGECOPY v1 - TRADING SIGNAL

Market: Will Bitcoin reach $100k by end of 2025?
Signal ID: 42

📊 QUALITY SCORE
  Perfect Bet Score: 5/6 ⭐⭐⭐⭐⭐
  Confidence: 83.3%
  Status: ✓ Clean Signal

👥 SMART WALLET ACTIVITY
  Wallet Count: 3
  Average PnL: 45.5%

💰 MARKET CONDITIONS
  Liquidity: $750,000
  Current Odds: 0.65
  Time to Event: 2.5h
```

### Perfect Bet Checklist

A signal scores 1 point for each criteria met:
1. ✓ Market liquidity > $500k
2. ✓ Entry during consolidation (not hype phase)
3. ✓ Wallet confirmed history (PnL>30%)
4. ✓ Pre-news timing window (1-3h)
5. ✓ 2-3 smart wallets in sync
6. ✓ Risk <15% of capital

**Signals need ≥5/6 points to be considered high-quality.**

## Next Steps

### 1. Set Up API Keys (Optional)

For production use, configure API keys in `.env`:

- **Polysights**: For advanced wallet analytics
- **Nevua Markets**: For real-time alerts
- **HashDive**: For wallet reputation cross-verification

### 2. Configure Alerts

Enable Telegram notifications:

```yaml
# In config.yaml
alerts:
  telegram:
    enabled: true
    bot_token: "your_bot_token"
    chat_id: "your_chat_id"
```

Get Telegram bot token:
1. Talk to [@BotFather](https://t.me/botfather)
2. Create new bot: `/newbot`
3. Copy token to config

### 3. Customize Risk Management

Edit risk parameters in `config.yaml`:

```yaml
risk_management:
  max_position_risk_percent: 15  # Max 15% per trade
  profit_take_increments: [0.1, 0.15]  # Take profit at 10%, 15%
  never_average_down: true
```

## Understanding the Output

### Wallet Scan Results
```
Wallet scan complete: 3 added, 15 updated, 8 smart wallets, 1 insider patterns
```

- **Added**: New wallets discovered
- **Updated**: Existing wallets updated
- **Smart wallets**: Wallets meeting criteria (PnL>30%, WR>60%)
- **Insider patterns**: New wallets with focused betting

### Market Scan Results
```
Market scan complete: 12 added, 88 updated, 35 high liquidity, 8 upcoming
```

- **High liquidity**: Markets with >$300k liquidity
- **Upcoming**: Markets ending in next 24 hours

### Signal Detection Results
```
Scan complete: 12 overlaps found, 3 signals created, 9 rejected
```

- **Overlaps found**: Markets with 2+ smart wallets
- **Signals created**: Signals passing all criteria
- **Rejected**: Signals failing validation

## Troubleshooting

### No Smart Wallets Found

If using mock data (no API keys), this is normal. The system includes 3 sample wallets for testing.

To get real data:
1. Sign up for Polysights API
2. Add API key to `.env`
3. Re-run scan

### No Signals Detected

Signals require:
- Active smart wallets
- Markets with sufficient liquidity
- Synchronized wallet activity

Try:
- Lowering `min_wallet_overlap` to 1 in config
- Reducing `min_liquidity` threshold
- Running during high market activity

### Alerts Not Working

Test each channel:
```bash
python main.py --test-alerts
```

Check:
- API keys in `.env`
- `enabled: true` in config
- Network connectivity

## Tips for Success

1. **Start with defaults**: Don't change criteria until you understand the signals
2. **Always manually confirm**: Never auto-trade based on signals alone
3. **Track performance**: Keep notes on which signals you acted on
4. **Adjust thresholds**: Fine-tune based on your results
5. **Use multiple sources**: Cross-verify signals with other data

## Advanced Usage

### Custom Scan Interval

```bash
python main.py --continuous --interval 5
```

Scans every 5 minutes instead of default 10.

### Custom Configuration

```bash
python main.py --config my_config.yaml --continuous
```

Use alternative configuration file.

### Database Location

Edit `config.yaml`:
```yaml
storage:
  db_path: "./data/polytrack.db"  # SQLite
  # Or PostgreSQL:
  # db_path: "postgresql://user:pass@localhost/polytrack"
```

## Getting Help

- Check `README.md` for detailed documentation
- Review `config.yaml` for all available options
- Check logs in `./logs/` directory
- Open GitHub issue for bugs/questions

## Safety Reminders

- This tool does **NOT** place trades automatically
- **Always** manually review signals before trading
- **Never** risk more than you can afford to lose
- **Use proper** risk management (max 15% per trade)
- **Verify** all signals independently

## Legal & Ethical

This tool only uses **public blockchain data**. It does not:
- Access private communications
- Use non-public event information
- Manipulate markets
- Violate insider trading laws

All data is transparent and verifiable on-chain.

---

**Ready to track smart money?**

```bash
python main.py --continuous
```

🎯 Your edge is in speed, discipline, and pattern recognition.
