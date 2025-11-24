import sys
import os
import json
import logging

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_full_hourly_integration_test():
    print("--- Starting Full Integration Test (HOURLY Resolution) ---")
    
    try:
        client = KnmiClient()
        fs = client.get_filesystem()
        
        # 1. Define Test Parameters
        station_id = "0-20000-0-06260" # De Bilt
        start_year = 2014
        end_year = 2024 
        
        print(f"Station: {station_id} (De Bilt)")
        print(f"Years:   {start_year} to {end_year}")
        
        total_records = 0
        
        for year in range(start_year, end_year + 1):
            # Define interval for the year
            t_start = f"{year}-01-01T00:00:00Z"
            t_end = f"{year}-12-31T23:59:59Z"
            
            print(f"\n--- Processing {year} ---")
            
            # 2. Fetch Data
            try:
                data = client.fetch_data(station_id, t_start, t_end)
                
                # Verify Structure
                if 'coverages' not in data:
                    print(f"❌ Error: No 'coverages' in response for {year}")
                    continue
                    
                cov = data['coverages'][0]
                ranges = cov.get('ranges', {})
                params = list(ranges.keys())
                
                if not params:
                    print(f"❌ Error: No parameters found for {year}")
                    continue
                    
                # Count records for first parameter
                first_param = params[0]
                count = len(ranges[first_param]['values'])
                total_records += count
                
                print(f"✅ Fetched {count} records (Hourly). Params: {len(params)}")
                
                # Simple validation
                expected_min = 8760 # 365 * 24
                if count < expected_min:
                    print(f"⚠️ Warning: Count {count} is less than expected {expected_min}")

            except Exception as e:
                print(f"❌ API Fetch Failed for {year}: {e}")
                continue

            # 3. Save Data (One file per year)
            file_path = f"{client.settings.DATA_ROOT}/landing/source=knmi/type=history_hourly/station={station_id}/year={year}/data.json"
            
            try:
                with fs.open(file_path, "w") as f:
                    json.dump(data, f)
                
                size = fs.info(file_path)['size'] / 1024 / 1024 # MB
                print(f"✅ Saved to: {file_path} ({size:.2f} MB)")
            except Exception as e:
                print(f"❌ Storage Write Failed for {year}: {e}")

        print(f"\n🎉 Full History Ingestion Complete.")
        print(f"Total Records Processed: {total_records}")
        print(f"Expected (~10 years): ~{10 * 365 * 24} ({87600})")

    except Exception as e:
        print(f"CRITICAL: Test Failed: {e}")

if __name__ == "__main__":
    run_full_hourly_integration_test()
