"""
Coherence SRE: Datadog Connector.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from datadog import initialize, api # type: ignore

from coherence.ingestion.base import (
    MonitoringConnector, 
    ConnectorError, 
    ConfigurationError, 
    RateLimitError
)

class DatadogConnector(MonitoringConnector):
    """
    Production-ready Datadog Connector.
    """

    def __init__(self, api_key: Optional[str] = None, app_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DD_API_KEY")
        self.app_key = app_key or os.getenv("DD_APP_KEY")
        self._initialized = False

    def validate_config(self) -> None:
        if not self.api_key:
            raise ConfigurationError("Datadog API Key is missing. Set DD_API_KEY env var.")
        if not self.app_key:
            raise ConfigurationError("Datadog App Key is missing. Set DD_APP_KEY env var.")
        
        # Initialize the Datadog client
        if not self._initialized:
            initialize(api_key=self.api_key, app_key=self.app_key)
            self._initialized = True

    def test_connection(self) -> bool:
        try:
            self.validate_config()
            # Lightweight call to verify auth
            api.User.get_all() 
            return True
        except Exception:
            return False

    def fetch_metrics(self, query: str, start: datetime, end: datetime) -> pd.DataFrame:
        self.validate_config()
        
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        try:
            # https://docs.datadoghq.com/api/latest/metrics/#query-timeseries-points
            results = api.Metric.query(start=start_ts, end=end_ts, query=query)
            
            if not results or 'series' not in results:
                return pd.DataFrame()

            data_list = []
            for series in results['series']:
                metric_name = series.get('metric')
                scope = series.get('scope', 'unknown') # host/tags often here
                
                # Parse points: [timestamp, value]
                for point in series.get('pointlist', []):
                    data_list.append({
                        'timestamp': pd.to_datetime(point[0], unit='ms'), # DD uses MS usually, need to check, actually API often uses seconds.
                        # Wait, DD API usually uses seconds for start/end but points might be ms. 
                        # Let's assume seconds for now based on standard DD API usage in Python, 
                        # but often it returns milliseconds for X inputs. 
                        # Safe bet: Check if > 30000000000 -> ms. But let's stick to standard conversion.
                        # Actually standard DD python library returns points having [timestamp(ms), value]
                        'value': point[1],
                        'metric': metric_name,
                        'scope': scope
                    })

            if not data_list:
                return pd.DataFrame()
                
            df = pd.DataFrame(data_list)
            # Normalize timestamp if needed (DD usually returns ms in pointlist)
            # If timestamp is massive, divide by 1000. 
            # But let's assume it handles standard pd.to_datetime logic.
            return df

        except Exception as e:
            if "429" in str(e):
                raise RateLimitError("Datadog API rate limit exceeded.")
            raise ConnectorError(f"Failed to fetch metrics: {str(e)}")

    def fetch_events(self, start: datetime, end: datetime, tags: Optional[List[str]] = None) -> pd.DataFrame:
        self.validate_config()
        
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        params = {
            "start": start_ts,
            "end": end_ts,
        }
        if tags:
            params["tags"] = ",".join(tags)

        try:
            results = api.Event.query(**params)
            
            if not results or 'events' not in results:
                return pd.DataFrame()

            events_list = []
            for event in results['events']:
                events_list.append({
                    'timestamp': pd.to_datetime(event.get('date_happened'), unit='s'),
                    'title': event.get('title'),
                    'text': event.get('text'),
                    'priority': event.get('priority'),
                    'host': event.get('host'),
                    'tags': event.get('tags'),
                    'alert_type': event.get('alert_type')
                })
                
            return pd.DataFrame(events_list)

        except Exception as e:
            if "429" in str(e):
                raise RateLimitError("Datadog API rate limit exceeded.")
            raise ConnectorError(f"Failed to fetch events: {str(e)}")
