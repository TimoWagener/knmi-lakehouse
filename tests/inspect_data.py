import sys
import os
import json
import logging

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)

def inspect_file():
    client = KnmiClient()
    fs = client.get_filesystem()
    
    # The logical path we wrote to (Year 2014)
    file_path = f"{client.settings.DATA_ROOT}/landing/source=knmi/type=history/station=0-20000-0-06201/year=2014/data.json"
    
    print(f"Reading: {file_path}")
    
    try:
        with fs.open(file_path, "r") as f:
            data = json.load(f)
            
        print("Keys:", data.keys())
        
        if "parameters" in data:
            params = data["parameters"].keys()
            print(f"\nParameters found ({len(params)}): {list(params)}")
            
        if "ranges" in data:
            print("\nRanges (Data Arrays):")
            for k, v in data["ranges"].items():
                print(f" - '{k}': {len(v['values'])} values")
        else:
            print("\n⚠️ 'ranges' key MISSING in response!")
            # Check 'coverages' if it exists (EDR sometimes nests it)
            if "coverages" in data:
                print(f"Coverages found: {len(data['coverages'])}")
                cov = data['coverages'][0]
                if "ranges" in cov:
                     ranges = cov['ranges']
                     print(f"Found {len(ranges)} parameters in coverage[0].")
                     # Check the first parameter count
                     first_param = list(ranges.keys())[0]
                     count = len(ranges[first_param]['values'])
                     print(f"DATA POINTS count for '{first_param}': {count}")
                     if count < 3650:
                         print("⚠️ WARNING: Data count is less than expected (3650 days for 10 years). API might be paginating.")

                
        if "domain" in data:
             print("Domain found (Time/Space coordinates).")
             
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    inspect_file()
