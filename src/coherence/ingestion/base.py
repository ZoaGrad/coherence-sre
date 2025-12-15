"""
Coherence SRE: Monitoring Connector Interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

class ConnectorError(Exception):
    """Base class for all connector exceptions."""
    pass

class ConfigurationError(ConnectorError):
    """Raised when connector configuration is invalid."""
    pass

class RateLimitError(ConnectorError):
    """Raised when API rate limits are exceeded."""
    pass

class ReadOnlyViolationError(ConnectorError):
    """Raised when a connector attempts a write operation (Strict Read-Only Enforcement)."""
    pass


class MonitoringConnector(ABC):
    """
    Abstract Base Class for specific monitoring system connectors (Datadog, Prometheus, etc.).
    Enforces the 'Read-Only' contract.
    """

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validates the configuration (API keys, URLs, etc.) without making network calls.
        Raises ConfigurationError.
        """
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Verifies connectivity to the external service.
        Returns True if successful, False otherwise.
        """
        ...

    @abstractmethod
    def fetch_metrics(self, query: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Fetches time-series metrics.
        Returns a pandas DataFrame with columns: [timestamp, value, host, tags].
        """
        ...

    @abstractmethod
    def fetch_events(self, start: datetime, end: datetime, tags: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetches system events (alerts, warnings).
        Returns a pandas DataFrame with columns: [timestamp, title, text, priority, host, tags].
        """
        ...
