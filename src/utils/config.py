"""Configuration loader and validator for EdgeCopy v1"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for the tracking system"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration

        Args:
            config_path: Path to YAML configuration file
        """
        load_dotenv()

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._inject_env_vars()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _inject_env_vars(self):
        """Inject environment variables into config"""
        # API Keys
        if not self.config['apis']['polysights']['api_key']:
            self.config['apis']['polysights']['api_key'] = os.getenv('POLYSIGHTS_API_KEY', '')

        if not self.config['apis']['nevua_markets']['api_key']:
            self.config['apis']['nevua_markets']['api_key'] = os.getenv('NEVUA_MARKETS_API_KEY', '')

        if not self.config['apis']['hash_dive']['api_key']:
            self.config['apis']['hash_dive']['api_key'] = os.getenv('HASH_DIVE_API_KEY', '')

        if not self.config['apis']['polymarket']['rpc_url']:
            self.config['apis']['polymarket']['rpc_url'] = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')

        # Telegram
        if not self.config['alerts']['telegram']['bot_token']:
            self.config['alerts']['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', '')

        if not self.config['alerts']['telegram']['chat_id']:
            self.config['alerts']['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', '')

        # Webhook
        if not self.config['alerts']['webhook']['url']:
            self.config['alerts']['webhook']['url'] = os.getenv('WEBHOOK_URL', '')

        # Email
        email_config = self.config['alerts']['email']
        if not email_config['smtp_server']:
            email_config['smtp_server'] = os.getenv('SMTP_SERVER', '')
        if not email_config['from_email']:
            email_config['from_email'] = os.getenv('EMAIL_FROM', '')
        if not email_config['to_email']:
            email_config['to_email'] = os.getenv('EMAIL_TO', '')
        if not email_config['password']:
            email_config['password'] = os.getenv('EMAIL_PASSWORD', '')

        # Database
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            self.config['storage']['db_path'] = db_url

    def get(self, path: str, default=None):
        """
        Get configuration value by dot-notation path

        Args:
            path: Dot-notation path (e.g., 'wallet_criteria.min_pnl_percent')
            default: Default value if path not found

        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path: str, value: Any):
        """
        Set configuration value by dot-notation path

        Args:
            path: Dot-notation path
            value: Value to set
        """
        keys = path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, path: str = None):
        """
        Save configuration to file

        Args:
            path: Optional custom path to save to
        """
        save_path = Path(path) if path else self.config_path

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)

    @property
    def wallet_criteria(self):
        """Get wallet criteria config"""
        return self.config.get('wallet_criteria', {})

    @property
    def signal_detection(self):
        """Get signal detection config"""
        return self.config.get('signal_detection', {})

    @property
    def risk_management(self):
        """Get risk management config"""
        return self.config.get('risk_management', {})

    @property
    def monitoring(self):
        """Get monitoring config"""
        return self.config.get('monitoring', {})

    @property
    def alerts_config(self):
        """Get alerts config"""
        return self.config.get('alerts', {})

    @property
    def apis(self):
        """Get APIs config"""
        return self.config.get('apis', {})

    @property
    def storage(self):
        """Get storage config"""
        return self.config.get('storage', {})

    @property
    def logging_config(self):
        """Get logging config"""
        return self.config.get('logging', {})
