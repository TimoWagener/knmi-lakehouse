import sys
import os
from dagster import Definitions, AssetSelection

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def verify_defs():
    print("--- Verifying Dagster Definitions ---")
    
    try:
        from src.definitions import defs
        print("✅ Successfully imported 'src.definitions.defs'")
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return
    except Exception as e:
        print(f"❌ General Error during import: {e}")
        return

    # 1. Check Assets
    assets = list(defs.get_asset_graph().assets)
    print(f"✅ Found {len(assets)} assets.")
    
    asset_names = [key.to_user_string() for key in assets]
    print(f"   Assets: {asset_names}")
    
    if "raw_stations_list" not in asset_names:
        print(f"❌ Missing 'raw_stations_list'")
    
    if "ingestion/knmi_hourly_observations" not in asset_names:
        print(f"❌ Missing 'ingestion/knmi_hourly_observations'")
        
    # 2. Check Sensors
    sensors = list(defs.sensors)
    print(f"✅ Found {len(sensors)} sensors.")
    if len(sensors) > 0:
        print(f"   Sensor: {sensors[0].name}")
        
    # 3. Check Partitions (Tricky without full context, but we can check the AssetNode)
    # Find the ingestion asset node
    ingestion_node = next(a for a in assets if a.key.to_user_string() == "ingestion/knmi_hourly_observations")
    if ingestion_node.partitions_def:
        print(f"✅ Ingestion asset has partitions: {ingestion_node.partitions_def}")
    else:
        print(f"❌ Ingestion asset is MISSING partitions!")

    print("\n🎉 Dagster Graph Verification Complete.")

if __name__ == "__main__":
    verify_defs()
