import json
from dagster import asset, Output
from src.utils.smart_client import KnmiClient

@asset
def raw_stations_list() -> Output[list[str]]:
    """
    Fetches the list of KNMI weather stations and saves metadata to S3.
    Returns a list of station IDs to be used for dynamic partitions.
    """
    client = KnmiClient()
    
    # 1. Fetch locations
    geojson = client.fetch_locations()
    
    # 2. Save to S3/MinIO
    save_path = f"{client.settings.DATA_ROOT}/metadata/stations.json"
    
    # Use fsspec filesystem to write
    with client.get_filesystem().open(save_path, "w") as f:
        json.dump(geojson, f)
        
    # 3. Extract IDs
    # GeoJSON FeatureCollection: features -> id or properties
    station_ids = []
    if "features" in geojson:
        for feature in geojson["features"]:
            # We must use the official API 'id' (e.g., '0-20000-0-06201') for subsequent calls to work.
            s_id = feature.get("id")
            if not s_id:
                # Fallback to properties if 'id' is missing (unlikely for valid GeoJSON)
                props = feature.get("properties", {})
                s_id = props.get("stationId") or props.get("wmoId")
            
            if s_id:
                station_ids.append(str(s_id))
                
    return Output(value=station_ids)
