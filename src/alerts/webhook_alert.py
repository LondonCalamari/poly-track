"""Webhook alerts for EdgeCopy v1"""

from typing import Dict, Any
from datetime import datetime
import requests
import json

from ..utils.logger import Logger


class WebhookAlert:
    """
    Webhook-based alert system for custom integrations
    """

    def __init__(self, config: dict, logger: Logger):
        """
        Initialize webhook alert

        Args:
            config: Configuration dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('url', '')

        if self.enabled and not self.webhook_url:
            self.logger.warning("Webhook alerts enabled but URL not configured")
            self.enabled = False

    def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send signal alert via webhook

        Args:
            signal_data: Signal data dict

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            payload = {
                'event_type': 'SIGNAL_DETECTED',
                'timestamp': datetime.now().isoformat(),
                'data': signal_data
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Webhook alert sent for signal {signal_data.get('signal_id')}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
            return False

    def send_test_alert(self) -> bool:
        """
        Send test alert

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        payload = {
            'event_type': 'TEST',
            'timestamp': datetime.now().isoformat(),
            'message': 'EdgeCopy v1 webhook test',
            'status': 'operational'
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            self.logger.info("Webhook test alert sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error sending webhook test: {e}")
            return False

    def send_error_alert(self, error_message: str) -> bool:
        """
        Send error alert via webhook

        Args:
            error_message: Error message

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        payload = {
            'event_type': 'ERROR',
            'timestamp': datetime.now().isoformat(),
            'error': error_message
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            return True

        except Exception as e:
            self.logger.error(f"Error sending webhook error alert: {e}")
            return False

    def send_scan_summary(self, scan_results: Dict[str, Any]) -> bool:
        """
        Send scan summary via webhook

        Args:
            scan_results: Scan results dict

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        payload = {
            'event_type': 'SCAN_COMPLETE',
            'timestamp': datetime.now().isoformat(),
            'results': scan_results
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            return True

        except Exception as e:
            self.logger.error(f"Error sending webhook scan summary: {e}")
            return False
