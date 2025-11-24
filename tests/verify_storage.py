import sys
import os
import json
import logging

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.smart_client import KnmiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_storage_verification():
    print("--- Starting MinIO Storage Verification ---")
    
    try:
        client = KnmiClient()
        fs = client.get_filesystem()
        settings = client.settings
        
        print(f"Target Root: {settings.DATA_ROOT}")
        print(f"Endpoint:    {settings.ENDPOINT_URL}")
        
        # Parse bucket name from DATA_ROOT (e.g. s3://weather-lake -> weather-lake)
        if "://" in settings.DATA_ROOT:
            bucket_name = settings.DATA_ROOT.split("://")[1].split("/")[0]
        else:
            bucket_name = settings.DATA_ROOT.split("/")[0]
            
        print(f"Target Bucket: {bucket_name}")

        # 1. Check if bucket exists / Create bucket
        try:
            print(f"\n[1/3] Checking Bucket '{bucket_name}'...")
            if not fs.exists(bucket_name):
                print(f"Bucket '{bucket_name}' does not exist. Attempting to create...")
                fs.mkdir(bucket_name)
                print(f"✅ Created bucket: {bucket_name}")
            else:
                print(f"✅ Bucket '{bucket_name}' already exists.")
        except Exception as e:
            print(f"❌ Error checking/creating bucket. Possible Auth Issue.\nError: {e}")
            print("\nTIP: Check if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env match docker-compose.yaml")
            return

        # 2. Write Test File
        test_file = f"{settings.DATA_ROOT}/verification.txt"
        print(f"\n[2/3] Writing test file to: {test_file}")
        try:
            with fs.open(test_file, "w") as f:
                f.write("Hello from KNMI Lakehouse Verification!")
            print("✅ Write Successful.")
        except Exception as e:
            print(f"❌ Write Failed: {e}")
            return

        # 3. Read Test File
        print(f"\n[3/3] Reading back test file...")
        try:
            with fs.open(test_file, "r") as f:
                content = f.read()
            print(f"✅ Read Successful. Content: '{content}'")
        except Exception as e:
            print(f"❌ Read Failed: {e}")
            return
            
        print("\n🎉 Storage Verification Complete. MinIO is ready.")

    except Exception as e:
        print(f"CRITICAL: Client Initialization Failed: {e}")

if __name__ == "__main__":
    run_storage_verification()
