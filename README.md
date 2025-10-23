# EdgeCopy v1 - Polymarket Smart Wallet Tracker

A systematic framework for tracking and analyzing "smart money" on Polymarket using public blockchain data.

## Overview

EdgeCopy v1 implements the proven methodology for identifying and following high-performing traders on Polymarket. This system automates the detection of trading signals by monitoring wallet activity, market conditions, and timing patterns.

## How It Works

The system follows the EdgeCopy v1 algorithm:

1. **Scans** for smart wallets every 10 minutes (configurable)
2. **Detects** when ≥2 wallets with PnL>30% enter the same market
3. **Validates** liquidity requirements (>$300k)
4. **Checks** timing windows (<5h before event)
5. **Alerts** you for manual confirmation

## Key Features

### Smart Wallet Identification
- Track wallets with 30%+ ROI over 30 days
- 60%+ win rate filtering
- $10k+ average bet size
- Pre-news entry detection (1-5 hours)

### Signal Detection
- Multi-wallet overlap detection (2+ wallets)
- Synchronized timing verification (within 30 min)
- Liquidity validation (>$300k minimum)
- Pre-event window checking

### Risk Management
- Position sizing (max 15% risk)
- Profit-taking automation (10-15% increments)
- Red flag detection (fake clusters, manipulation)
- Cross-verification from multiple sources

### Perfect Bet Checklist
- Market liquidity check (>$500k)
- Consolidation phase detection
- Wallet history validation
- Pre-news timing window
- Multi-wallet synchronization
- Risk calculation

## Legal & Ethical Framework

This tool **only** uses publicly available blockchain data. It does **not**:
- Access private communications
- Use non-public event information
- Manipulate markets
- Violate any insider trading laws

All data is transparent and verifiable on-chain.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd poly-track

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

## Configuration

Edit `config.yaml` to customize:
- Smart wallet criteria
- Signal detection thresholds
- Risk management rules
- Alert preferences
- API settings

## Usage

```bash
# Start the tracker
python main.py

# Run with custom config
python main.py --config custom_config.yaml

# Scan once and exit
python main.py --scan-once

# List tracked wallets
python main.py --list-wallets

# View signals
python main.py --show-signals

# Test alerts
python main.py --test-alerts
```

## Project Structure

```
poly-track/
├── src/
│   ├── core/
│   │   ├── wallet_tracker.py      # Smart wallet identification
│   │   ├── market_monitor.py      # Market data & liquidity checks
│   │   ├── signal_detector.py     # EdgeCopy v1 algorithm
│   │   └── risk_manager.py        # Risk & position management
│   ├── integrations/
│   │   ├── polysights.py          # Polysights API
│   │   ├── polymarket.py          # Polymarket API
│   │   ├── nevua.py               # Nevua Markets integration
│   │   └── hashdive.py            # HashDive integration
│   ├── alerts/
│   │   ├── telegram_alert.py      # Telegram notifications
│   │   ├── webhook_alert.py       # Webhook alerts
│   │   └── console_alert.py       # Console output
│   ├── database/
│   │   ├── models.py              # Database models
│   │   └── repository.py          # Data access layer
│   └── utils/
│       ├── config.py              # Configuration loader
│       ├── logger.py              # Logging setup
│       └── validators.py          # Input validation
├── main.py                         # Entry point
├── config.yaml                     # Configuration
├── requirements.txt                # Dependencies
└── README.md                       # Documentation
```

## Smart Wallet Criteria

The system identifies smart wallets based on:

| Criterion | Threshold |
|-----------|-----------|
| ROI (30 days) | >30% |
| Win Rate | >60% |
| Avg Bet Size | >$10k |
| Pre-news Entry | 1-5 hours before |
| Profit Stability | Consistent |

## Signal Quality Scoring

Signals are scored against the Perfect Bet Checklist:

- ✓ Market liquidity > $500k
- ✓ Entry during consolidation (not hype)
- ✓ Wallet confirmed history (PnL>30%)
- ✓ Pre-news timing window (1-3h)
- ✓ 2-3 smart wallets in sync
- ✓ Risk <15% of capital

**Signals need ≥5/6 points to be considered high-quality.**

## Red Flags & Filters

The system automatically filters out:

- ❌ Multiple new wallets with identical small bets (fake clusters)
- ❌ Low liquidity markets (<$300k)
- ❌ Unsynchronized bets (>30 min spread)
- ❌ Bets against obvious facts
- ❌ Single-source signals

## Tools Integration

### Polysights
Primary source for insider finder and PnL tracking

### Nevua Markets
Real-time alerts via Telegram/webhook

### HashDive
Cross-verification and reputation scoring

### PolyAlertHub
Additional alert system

## Risk Management Rules

1. **Take profits gradually** (10-15% increments)
2. **Never average down** losing positions
3. **Copy patterns, not emotions**
4. **Close before major news** events
5. **Max 15% risk** per trade
6. **Mechanical decision-making** only

## Example Workflow

1. System scans every 10 minutes
2. Detects 3 smart wallets entering "Election Outcome" market
3. Validates: liquidity $750k ✓, timing 2h before event ✓
4. Calculates Perfect Bet score: 5/6 ✓
5. Sends alert via Telegram + console
6. You review and manually confirm entry
7. System tracks position and suggests profit-taking levels

## Monitoring & Alerts

Configure alerts in `config.yaml`:

```yaml
alerts:
  telegram:
    enabled: true
    bot_token: "your_token"
    chat_id: "your_chat_id"

  webhook:
    enabled: true
    url: "https://your-webhook.com"

  console:
    enabled: true
```

## Data & Privacy

- All data stored locally in SQLite database
- No data shared with third parties
- Optional PostgreSQL for advanced users
- 90-day retention policy (configurable)

## Troubleshooting

### API Rate Limits
- Adjust `scan_interval_minutes` in config
- Use multiple API keys (if supported)

### False Signals
- Increase `min_wallet_overlap` threshold
- Enable `cross_verify_sources`
- Raise `min_liquidity` requirement

### Missing Signals
- Lower `min_pnl_percent` threshold
- Increase `pre_event_window_hours_max`
- Check API key validity

## Contributing

This is a personal tracking tool. Feel free to fork and customize for your own use.

## Disclaimer

This tool is for educational and research purposes. Trading prediction markets involves risk. Always:

- Do your own research
- Never risk more than you can afford to lose
- Understand the markets you're trading
- Use proper risk management
- Verify all signals manually

The developers are not responsible for any trading losses.

## License

MIT License - See LICENSE file for details

## Resources

- [Polymarket](https://polymarket.com)
- [Polysights](https://polysights.com) - Insider Finder
- [Nevua Markets](https://nevua.xyz) - Alert System
- [HashDive](https://hashdive.com) - Reputation Scoring

## Support

For issues or questions, please open a GitHub issue.

---

**Remember:** Your edge isn't in hidden info - it's in speed, discipline, and pattern recognition.

*"Smart wallets aren't gods. They're just first to act on the imbalance between probability and attention."*
