import logging
from dagster import (
    Definitions,
    DynamicPartitionsDefinition,
    SensorDefinition,
    SensorEvaluationContext,
    AssetSelection,
    define_asset_job,
    RunRequest,
    SkipReason,
    job,
    op
)
from dagster import load_assets_from_modules

from src.assets import metadata, ingestion
from src.partitions import knmi_stations_def

# Configure logging
logger = logging.getLogger(__name__)

# 1. Define Dynamic Partitions for Stations
# Moved to src/partitions.py to avoid circular imports
# knmi_stations_def = DynamicPartitionsDefinition(name="knmi_stations")

# 2. Load Assets
metadata_assets = load_assets_from_modules([metadata])
ingestion_assets = load_assets_from_modules([ingestion])

# 3. Define Sensor to update partitions
# This sensor watches for the completion of the 'raw_stations_list' asset
# and updates the 'knmi_stations' partition definition.

@job
def update_stations_partition_job():
    # This is a dummy job required if we were triggering a job, 
    # but for a standard sensor updating partitions, we often just do it in the sensor function.
    # However, Dagster sensors usually return RunRequests. 
    # For updating partitions *based on asset materialization*, we use an automation sensor.
    pass

def stations_sensor_fn(context: SensorEvaluationContext):
    """
    Listen for materializations of 'raw_stations_list'.
    When it updates, read the station IDs and update the dynamic partition.
    """
    # Get the last materialization of the asset
    asset_key = metadata.raw_stations_list.key
    cursor = context.cursor or None
    
    # Check for new materializations since the cursor
    events = context.instance.get_event_records(
        event_records_filter=None, # Filter logic handled by cursor usually, simplified here
        ascending=False,
        limit=1
    )
    
    # Correct way to query for asset materialization is using `context.instance.get_latest_materialization_event(asset_key)`
    # But standard sensor pattern for assets is simpler.
    
    # Let's stick to the plan: "Sensor listening to raw_stations_list"
    # We can check if the asset has been materialized recently.
    
    # Alternative: Simply load the file from S3 if we want to be decoupled?
    # No, better to use Dagster's event log.
    
    # Simplified approach for "Step 3":
    # We'll assume this sensor runs periodically. It checks if the partition set needs updating.
    # Since `raw_stations_list` returns the list of IDs, we can inspect its latest output value?
    # Accessing output values from a sensor is tricky/expensive (requires I/O manager).
    
    # Better Approach: 
    # The `raw_stations_list` asset writes to S3: `metadata/stations.json`.
    # The sensor can just read that file using our SmartClient!
    
    from src.utils.smart_client import KnmiClient
    import json
    
    try:
        client = KnmiClient()
        path = f"{client.settings.DATA_ROOT}/metadata/stations.json"
        fs = client.get_filesystem()
        
        if not fs.exists(path):
            return SkipReason(f"Stations metadata file not found at {path}")
            
        # Check modification time to see if we need to update?
        # Or just always try to add (idempotent).
        
        with fs.open(path, "r") as f:
            geojson = json.load(f)
            
        new_keys = []
        if "features" in geojson:
            for feature in geojson["features"]:
                s_id = feature.get("id")
                if not s_id:
                    props = feature.get("properties", {})
                    s_id = props.get("stationId") or props.get("wmoId")
                if s_id:
                    new_keys.append(str(s_id))
        
        if new_keys:
            context.instance.add_dynamic_partitions(knmi_stations_def.name, new_keys)
            return SkipReason(f"Updated {len(new_keys)} stations in partition '{knmi_stations_def.name}'")
            
        return SkipReason("No stations found in metadata file.")
        
    except Exception as e:
        logger.error(f"Sensor failed: {e}")
        return SkipReason(f"Sensor failed: {e}")

# Create the sensor definition
stations_sensor = SensorDefinition(
    name="stations_update_sensor",
    evaluation_fn=stations_sensor_fn,
    minimum_interval_seconds=60 * 60, # Check every hour
)

# 4. Final Definitions
defs = Definitions(
    assets=[*metadata_assets, *ingestion_assets],
    sensors=[stations_sensor],
)
