"""Console alerts for EdgeCopy v1"""

from typing import Dict, Any
from datetime import datetime

from ..utils.logger import Logger


class ConsoleAlert:
    """
    Console-based alert system with formatted output
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize console alert

        Args:
            config: Configuration dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.enabled = config.get('enabled', True)

    def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send signal alert to console

        Args:
            signal_data: Signal data dict

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            # Format alert message
            message = self._format_signal_alert(signal_data)

            # Print to console
            print("\n" + "=" * 80)
            print(message)
            print("=" * 80 + "\n")

            self.logger.info(f"Console alert sent for signal {signal_data.get('signal_id')}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending console alert: {e}")
            return False

    def send_test_alert(self) -> bool:
        """
        Send test alert

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = """
🎯 EdgeCopy v1 - Test Alert

This is a test alert from the EdgeCopy tracking system.
Console alerts are working correctly!

Time: {time}
Status: ✓ Operational
        """.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        print("\n" + "=" * 80)
        print(message)
        print("=" * 80 + "\n")

        return True

    def _format_signal_alert(self, signal_data: Dict[str, Any]) -> str:
        """Format signal data for console output"""
        perfect_score = signal_data.get('perfect_bet_score', '0/6')
        confidence = signal_data.get('confidence', 0)
        wallet_count = signal_data.get('wallet_count', 0)
        market_title = signal_data.get('market_title', 'Unknown Market')
        liquidity = signal_data.get('liquidity', '$0')
        avg_pnl = signal_data.get('avg_wallet_pnl', '0%')
        current_odds = signal_data.get('current_odds', 'N/A')
        hours_before = signal_data.get('hours_before_event', 'N/A')
        has_red_flags = signal_data.get('has_red_flags', False)

        flag_emoji = "🚩" if has_red_flags else "✓"
        quality_emoji = "⭐" * min(int(float(perfect_score.split('/')[0])), 6)

        message = f"""
🎯 EDGECOPY v1 - TRADING SIGNAL DETECTED

Market: {market_title}
Signal ID: {signal_data.get('signal_id', 'N/A')}

📊 QUALITY SCORE
  Perfect Bet Score: {perfect_score} {quality_emoji}
  Confidence: {confidence}
  Status: {flag_emoji} {'RED FLAGS DETECTED' if has_red_flags else 'Clean Signal'}

👥 SMART WALLET ACTIVITY
  Wallet Count: {wallet_count}
  Average PnL: {avg_pnl}

💰 MARKET CONDITIONS
  Liquidity: {liquidity}
  Current Odds: {current_odds}
  Time to Event: {hours_before}

⚠️  USER ACTION REQUIRED
  Review signal and confirm entry manually
  Check Perfect Bet Checklist (need 5/6)
  Validate risk management parameters

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        return message

    def send_error_alert(self, error_message: str) -> bool:
        """
        Send error alert to console

        Args:
            error_message: Error message

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = f"""
❌ EdgeCopy v1 - Error Alert

{error_message}

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        print("\n" + "=" * 80)
        print(message)
        print("=" * 80 + "\n")

        return True

    def send_scan_summary(self, scan_results: Dict[str, Any]) -> bool:
        """
        Send scan summary to console

        Args:
            scan_results: Scan results dict

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = f"""
📊 EdgeCopy v1 - Scan Summary

Overlaps Found: {scan_results.get('overlaps_found', 0)}
Signals Created: {scan_results.get('signals_created', 0)}
Signals Rejected: {scan_results.get('signals_rejected', 0)}
Duration: {scan_results.get('duration_seconds', 0):.2f}s

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        print("\n" + "-" * 80)
        print(message)
        print("-" * 80 + "\n")

        return True
