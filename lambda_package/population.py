"""
Rearc Data Quest Part - 2
Local-first Implementation of Population API Ingestion.
Fetches Population data from a public API and stores the responses as a JSON in a local directory that mirrors an S3 layout.
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone
import boto3
#from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv()

# ==============================================
# S3 CONFIGURATION
# ==============================================
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET', 'rearc-data-quest-milan-prod')
S3_PREFIX = 'raw/api/'

# Initialize S3 client (only if USE_S3 is enabled)
s3_client = boto3.client('s3') if USE_S3 else None

#API endpoint for population data
POPULATION_API_URL = 'https://honolulu-api.datausa.io/tesseract/data.jsonrecords'

QUERY_PARAMS = {
    "cube":"acs_yg_total_population_1",
    "drilldowns" :"Year, Nation",
    "measures" : "Population",
    "locale":"en"
}

LOCAL_API_DIR = Path("data/raw/api")

def ensure_local_directory():
    """
    Ensure the local directory for API data exists.
    """
    LOCAL_API_DIR.mkdir(parents=True, exist_ok=True)

def fetch_population_data():
    """
    Fetch population data from DataUSA API.

    Returns
        Parsed JSON response.
    """

    response = requests.get(
        POPULATION_API_URL,
        params= QUERY_PARAMS,
        timeout= 30
    )

    response.raise_for_status()
    return response.json()

def s3_fil_exists(filename):
    '''
    Scan s3/raw/api to check if a file for today exists.
    '''
    s3_key = S3_PREFIX+ filename
    try:
        s3_client.head_object(
            Bucket = S3_BUCKET,
            Key = s3_key
            )
        return True
        
    except s3_client.exceptions.ClientError as e: 
        if e.response["Error"]["Code"] == '404':
            return False
        else:
            raise

def upload_json_to_s3(filename,data):
    '''
    Upload JSON data to S3.
    '''

    s3_key = S3_PREFIX + filename

    try:
        s3_client.put_object(
            Bucket = S3_BUCKET,
            Key = s3_key,
            Body = json.dumps(data),
            ContentType = 'application/json'
        )

        print(f"Uploaded to S3: s3://{S3_BUCKET}/{s3_key}")

    except Exception as e:
        print(f"Error uploading to S3: {e}")

def save_json(data):
    """
    Save API responses as a JSON file locally.
    """

    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"population_{today_str}.json"
    

    if USE_S3:
        if s3_fil_exists(filename):
            print('Population data already uploaded for today. Skipping')
            return
        upload_json_to_s3(filename,data)
    else:
        ensure_local_directory()
        output_file = LOCAL_API_DIR / filename
        
        with open(output_file, "w") as f:
            json.dump(data,f, indent = 2)
    
        print(f"Saved Population data to {output_file}")


def run():
    """
    Main Execution flow.
    """
    print("Fetching population data....")
    data = fetch_population_data()
    save_json(data)

if __name__ == "__main__":
    run()