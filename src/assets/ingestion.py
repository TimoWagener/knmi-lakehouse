import json
import logging
from dagster import (
    asset,
    Output,
    MultiPartitionsDefinition,
    MonthlyPartitionsDefinition,
    AssetExecutionContext
)
from src.utils.smart_client import KnmiClient
from src.partitions import knmi_stations_def

# Configure Logging
logger = logging.getLogger(__name__)

# Define Partitions
# We combine the Dynamic Stations with Monthly Time windows.
# Start date: 2014-01-01 (Matching our 10-year goal)
monthly_partitions = MonthlyPartitionsDefinition(start_date="2014-01-01")

knmi_partitions = MultiPartitionsDefinition({
    "station": knmi_stations_def,
    "date": monthly_partitions
})

@asset(
    partitions_def=knmi_partitions,
    group_name="ingestion",
    compute_kind="python"
)
def knmi_hourly_observations(context: AssetExecutionContext):
    """
    Fetches hourly weather observations for a specific station and month.
    Partitioned by Station and Month.
    """
    # 1. Parse Partition Key
    partition = context.partition_key
    # MultiPartition key format: MultiPartitionKey(keys_by_dimension={'station': '...', 'date': '...'})
    # context.partition_key.keys_by_dimension is the proper way access it
    
    keys = partition.keys_by_dimension
    station_id = keys["station"]
    date_str = keys["date"] # e.g., "2023-01-01"
    
    logger.info(f"Processing Partition: Station={station_id}, Month={date_str}")
    
    # 2. Calculate Time Range (Start/End of Month)
    # date_str is the start of the month
    start_date = f"{date_str}T00:00:00Z"
    
    # Calculate end of month
    # Quick trick: Parse to date, add month, subtract second?
    # Or relying on Dagster's window?
    time_window = context.partition_time_window
    start_dt = time_window.start
    end_dt = time_window.end
    
    # Format for API: ISO8601
    # KNMI EDR usually accepts exact ISO strings
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    t_start = start_dt.strftime(fmt)
    # end_dt is exclusive (start of next month), so we want strictly less than, 
    # or just pass start/end to API and hope it handles [start, end)?
    # EDR 'datetime' interval is usually inclusive/inclusive or inclusive/exclusive depending on impl.
    # Safest is to subtract 1 second for the API call if we want exact monthly boundaries?
    # Actually, EDR standard is ISO8601 intervals. 
    # Let's use the exact window start/end provided by Dagster.
    t_end = end_dt.strftime(fmt)
    
    logger.info(f"Time Window: {t_start} -> {t_end}")
    
    # 3. Fetch Data
    client = KnmiClient()
    try:
        data = client.fetch_data(station_id, t_start, t_end)
    except Exception as e:
        # If 404 or empty, what to do? 
        # For now, fail the asset so we know.
        raise e
        
    # 4. Save to S3 (Hive Style)
    # Structure: source=knmi/type=hourly/station={id}/year={yyyy}/month={mm}/data.json
    year = start_dt.year
    month = start_dt.month
    
    # Pad month with zero
    path = f"{client.settings.DATA_ROOT}/landing/source=knmi/type=hourly/station={station_id}/year={year}/month={month:02d}/data.json"
    
    fs = client.get_filesystem()
    with fs.open(path, "w") as f:
        json.dump(data, f)
        
    return Output(
        value=path,
        metadata={
            "path": path,
            "station": station_id,
            "year": year,
            "month": month,
            "size_mb": fs.info(path)['size'] / 1024 / 1024
        }
    )
