"""
Rearc Data Quest Part - 2
Local-first Implementation of Population API Ingestion.
Fetches Population data from a public API and stores the responses as a JSON in a local directory that mirrors an S3 layout.
"""

import json
import requests
from pathlib import Path
from datetime import datetime


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

def save_json(data):
    """
    Save API responses as a JSON file locally.
    """

    ensure_local_directory()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    output_file = LOCAL_API_DIR / f"population_{timestamp}.json"

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