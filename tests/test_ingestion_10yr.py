import sys
import os
import json
import logging

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_full_integration_test():
    print("--- Starting Full Integration Test (Yearly Partitioning) ---")
    
    try:
        client = KnmiClient()
        fs = client.get_filesystem()
        
        # 1. Define Test Parameters
        station_id = "0-20000-0-06201"
        start_year = 2014
        end_year = 2024 
        
        print(f"Station: {station_id}")
        print(f"Years:   {start_year} to {end_year}")
        
        for year in range(start_year, end_year + 1):
            # Define interval for the year
            t_start = f"{year}-01-01T00:00:00Z"
            t_end = f"{year}-12-31T23:59:59Z"
            
            print(f"\n--- Processing {year} ---")
            
            # 2. Fetch Data
            try:
                data = client.fetch_data(station_id, t_start, t_end)
                print(f"✅ Fetched data for {year}")
            except Exception as e:
                print(f"❌ API Fetch Failed for {year}: {e}")
                continue

            # 3. Save Data (One file per year)
            # Hive Path: .../station={id}/year={year}/data.json
            file_path = f"{client.settings.DATA_ROOT}/landing/source=knmi/type=history/station={station_id}/year={year}/data.json"
            
            try:
                # fs.mkdirs handled implicitly by most s3fs operations or not needed for object stores
                with fs.open(file_path, "w") as f:
                    json.dump(data, f)
                
                size = fs.info(file_path)['size'] / 1024
                print(f"✅ Saved to: {file_path} ({size:.2f} KB)")
            except Exception as e:
                print(f"❌ Storage Write Failed for {year}: {e}")

        print("\n🎉 Full History Ingestion Complete.")

    except Exception as e:
        print(f"CRITICAL: Test Failed: {e}")

if __name__ == "__main__":
    run_full_integration_test()
