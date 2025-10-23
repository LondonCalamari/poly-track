"""Telegram alerts for EdgeCopy v1"""

from typing import Dict, Any
from datetime import datetime
import requests

from ..utils.logger import Logger


class TelegramAlert:
    """
    Telegram bot alert system
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize Telegram alert

        Args:
            config: Configuration dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.enabled = config.get('enabled', False)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')

        if self.enabled and (not self.bot_token or not self.chat_id):
            self.logger.warning("Telegram alerts enabled but credentials missing")
            self.enabled = False

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send signal alert via Telegram

        Args:
            signal_data: Signal data dict

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            message = self._format_signal_alert(signal_data)
            return self._send_message(message, parse_mode='HTML')

        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
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
🎯 <b>EdgeCopy v1 - Test Alert</b>

This is a test alert from the EdgeCopy tracking system.
Telegram alerts are working correctly!

Time: {}
Status: ✓ Operational
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return self._send_message(message, parse_mode='HTML')

    def _format_signal_alert(self, signal_data: Dict[str, Any]) -> str:
        """Format signal data for Telegram"""
        perfect_score = signal_data.get('perfect_bet_score', '0/6')
        confidence = signal_data.get('confidence', 0)
        wallet_count = signal_data.get('wallet_count', 0)
        market_title = signal_data.get('market_title', 'Unknown Market')
        liquidity = signal_data.get('liquidity', '$0')
        avg_pnl = signal_data.get('avg_wallet_pnl', '0%')
        current_odds = signal_data.get('current_odds', 'N/A')
        hours_before = signal_data.get('hours_before_event', 'N/A')
        has_red_flags = signal_data.get('has_red_flags', False)

        flag_status = "🚩 RED FLAGS DETECTED" if has_red_flags else "✓ Clean Signal"
        stars = "⭐" * min(int(float(perfect_score.split('/')[0])), 6)

        message = f"""
🎯 <b>EDGECOPY v1 - TRADING SIGNAL</b>

<b>Market:</b> {market_title}
<b>Signal ID:</b> {signal_data.get('signal_id', 'N/A')}

📊 <b>QUALITY SCORE</b>
• Perfect Bet Score: {perfect_score} {stars}
• Confidence: {confidence}
• Status: {flag_status}

👥 <b>SMART WALLET ACTIVITY</b>
• Wallet Count: {wallet_count}
• Average PnL: {avg_pnl}

💰 <b>MARKET CONDITIONS</b>
• Liquidity: {liquidity}
• Current Odds: {current_odds}
• Time to Event: {hours_before}

⚠️ <b>ACTION REQUIRED</b>
Review and confirm entry manually

<i>Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>
        """

        return message

    def _send_message(self, message: str, parse_mode: str = None) -> bool:
        """
        Send message via Telegram Bot API

        Args:
            message: Message text
            parse_mode: Parsing mode (HTML, Markdown, etc.)

        Returns:
            True if sent successfully
        """
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message
            }

            if parse_mode:
                payload['parse_mode'] = parse_mode

            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info("Telegram alert sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_error_alert(self, error_message: str) -> bool:
        """
        Send error alert via Telegram

        Args:
            error_message: Error message

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = f"""
❌ <b>EdgeCopy v1 - Error Alert</b>

{error_message}

<i>Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>
        """

        return self._send_message(message, parse_mode='HTML')
