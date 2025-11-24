import time
import logging
import requests
import fsspec
from typing import Any, Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger(__name__)

class KnmiSettings(BaseSettings):
    """
    Configuration settings loaded from environment variables.
    """
    DATA_ROOT: str = Field(..., description="Root path for data storage (e.g., s3://weather-lake)")
    KNMI_API_TOKEN: str = Field(..., description="API Token for KNMI")
    KNMI_API_BASE_URL: str = Field("https://api.dataplatform.knmi.nl/edr/v1", description="Base URL for KNMI EDR API")
    
    # MinIO / S3 Specifics
    ENDPOINT_URL: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

class KnmiClient:
    """
    Smart Client for KNMI API interaction and FileSystem abstraction.
    """
    def __init__(self):
        self.settings = KnmiSettings()
        self.fs = self._init_filesystem()
        self.headers = {"Authorization": self.settings.KNMI_API_TOKEN}

    def _init_filesystem(self) -> fsspec.AbstractFileSystem:
        """
        Initialize the filesystem based on DATA_ROOT scheme.
        """
        protocol = self.settings.DATA_ROOT.split("://")[0]
        storage_options = {}
        
        if protocol == "s3":
            storage_options = {
                "key": self.settings.AWS_ACCESS_KEY_ID,
                "secret": self.settings.AWS_SECRET_ACCESS_KEY,
                "endpoint_url": self.settings.ENDPOINT_URL,
            }
        elif protocol == "gs":
            # GCS specific options if needed
            pass
            
        return fsspec.filesystem(protocol, **storage_options)

    def get_filesystem(self) -> fsspec.AbstractFileSystem:
        return self.fs

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def fetch_locations(self) -> Dict[str, Any]:
        """
        Fetch station metadata from KNMI EDR API.
        Hits /collections/hourly-in-situ-meteorological-observations-validated/locations
        """
        # We use the hourly validated collection for station discovery
        collection = "hourly-in-situ-meteorological-observations-validated"
        url = f"{self.settings.KNMI_API_BASE_URL}/collections/{collection}/locations"
        params = {"f": "json"}
        
        logger.info(f"Fetching locations from {url}")
        # Throttle as per requirements
        time.sleep(1.0)
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def fetch_data(self, station_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Fetch observation data for a specific station and time range.
        """
        # Switch to hourly validated data
        collection = "hourly-in-situ-meteorological-observations-validated"
        
        # EDR Pattern: /collections/{id}/locations/{locId}
        url = f"{self.settings.KNMI_API_BASE_URL}/collections/{collection}/locations/{station_id}"
        
        params = {
            "f": "CoverageJSON",
            "datetime": f"{start_date}/{end_date}",
        }

        logger.info(f"Fetching data for {station_id} from {start_date} to {end_date}")
        time.sleep(1.0)
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
