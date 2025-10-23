"""Alert manager for coordinating all alert channels"""

from typing import Dict, Any, List

from .console_alert import ConsoleAlert
from .telegram_alert import TelegramAlert
from .webhook_alert import WebhookAlert
from ..utils.logger import Logger


class AlertManager:
    """
    Manages all alert channels and coordinates notifications
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize alert manager

        Args:
            config: Alerts configuration dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Initialize alert channels
        self.console = ConsoleAlert(config.get('console', {}), logger)
        self.telegram = TelegramAlert(config.get('telegram', {}), logger)
        self.webhook = WebhookAlert(config.get('webhook', {}), logger)

        self.enabled_channels = self._get_enabled_channels()

        self.logger.info(f"Alert manager initialized with channels: {', '.join(self.enabled_channels)}")

    def _get_enabled_channels(self) -> List[str]:
        """Get list of enabled alert channels"""
        channels = []

        if self.console.enabled:
            channels.append('console')
        if self.telegram.enabled:
            channels.append('telegram')
        if self.webhook.enabled:
            channels.append('webhook')

        return channels

    def send_signal_alert(self, signal_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Send signal alert to all enabled channels

        Args:
            signal_data: Signal data dict

        Returns:
            Dict of channel -> success status
        """
        results = {}

        if self.console.enabled:
            results['console'] = self.console.send_signal_alert(signal_data)

        if self.telegram.enabled:
            results['telegram'] = self.telegram.send_signal_alert(signal_data)

        if self.webhook.enabled:
            results['webhook'] = self.webhook.send_signal_alert(signal_data)

        successful = sum(results.values())
        total = len(results)

        self.logger.info(f"Signal alert sent: {successful}/{total} channels successful")

        return results

    def send_test_alert(self) -> Dict[str, bool]:
        """
        Send test alert to all enabled channels

        Returns:
            Dict of channel -> success status
        """
        results = {}

        if self.console.enabled:
            results['console'] = self.console.send_test_alert()

        if self.telegram.enabled:
            results['telegram'] = self.telegram.send_test_alert()

        if self.webhook.enabled:
            results['webhook'] = self.webhook.send_test_alert()

        return results

    def send_error_alert(self, error_message: str) -> Dict[str, bool]:
        """
        Send error alert to all enabled channels

        Args:
            error_message: Error message

        Returns:
            Dict of channel -> success status
        """
        results = {}

        if self.console.enabled:
            results['console'] = self.console.send_error_alert(error_message)

        if self.telegram.enabled:
            results['telegram'] = self.telegram.send_error_alert(error_message)

        if self.webhook.enabled:
            results['webhook'] = self.webhook.send_error_alert(error_message)

        return results

    def send_scan_summary(self, scan_results: Dict[str, Any]) -> Dict[str, bool]:
        """
        Send scan summary to enabled channels

        Args:
            scan_results: Scan results dict

        Returns:
            Dict of channel -> success status
        """
        results = {}

        if self.console.enabled:
            results['console'] = self.console.send_scan_summary(scan_results)

        if self.webhook.enabled:
            results['webhook'] = self.webhook.send_scan_summary(scan_results)

        return results
