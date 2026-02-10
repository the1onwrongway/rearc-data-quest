"""
Rearc Data Quest Part - 1 
Local First Implementation of BLS Sync

This script syncs BLS source files into a local directory that mirrors an S3 bucket structure.
THe Logic is intenntionally backend-agnostic and can be mapped to 1:1 to S3 without code changes.
"""

import os
import requests
from pathlib import Path
from urllib.parse import urljoin


LISTING_HEADERS = {
    "User-Agent": "rearc-data-quest/1.0 (contact: mcwan33@gmail.com)",
    "Accept": "text/html"
}

DOWNLOAD_HEADERS = {
    "User-Agent": "rearc-data-quest/1.0 (contact: mcwan33@gmail.com)"
    #"Accept": "text/plain"
}

BLS_BASE_URL = "https://download.bls.gov/pub/time.series/pr/"  # Base URL for BLS data files
LOCAL_BLS_DIR = Path("data/raw/bls")  # Local directory to store BLS data

def ensure_local_directory():
    """Ensure the local directory for BLS data exists."""
    LOCAL_BLS_DIR.mkdir(parents=True, exist_ok=True)

def list_local_files():
    """
    Lists the files already present in local BLS directory
    This mirrors listing objects in an S3 bucket.
    """
    # Ensure the local directory for BLS data exists.
    if not LOCAL_BLS_DIR.exists():
        return set()

    return {
        f.name
        for f in LOCAL_BLS_DIR.iterdir()
        if f.is_file()
    }

def list_remote_files():
    """
    Fetches the BLS directory index page and extracts file names.

    The BLS server returns HTML with file entries separated by <br> tags.
    Format: <A HREF="/path/file">filename</A>

    Assumptions:
    - BLS exposes a simple HTML directory listing.
    - File links are present inside href attributes.
    - We are interested in productivity-related files following the 'pr.*' naming convention
    """
    # Send an HTTP GET request to the BLS base URL to retrieve the directory listing
    response = requests.get(BLS_BASE_URL,headers=LISTING_HEADERS, timeout=30)
    
    # Raise an exception if the request was unsuccessful (e.g., 404 or 500 status codes)
    response.raise_for_status()
    
    # Initialize an empty set to store unique file names
    files = set()

    # Split by <br> tags instead of newlines since it's all one line
    for line in response.text.split('<br>'):
        
        # Look for href attributes
        if 'HREF="' not in line:
            continue
        
        try:
            # Extract the filename from href
            # Example line: <A HREF="pub/time.series/pr/pr.class">pr.class</a>
            href = line.split('HREF="')[1].split('"')[0]

            #Get just the filename (last part after /)
            filename = href.split('/')[-1]

        except IndexError:
            # If the line format is unexpected, skip safely
            continue

        # Only include text data files relevant for igestion
        if filename.startswith("pr."):
            files.add(filename)
            
    # Return the set of remote file names
    return files

def download_file(filename):
    """
    Downloads a single BLS file and stores it locally.
    """

    url = BLS_BASE_URL + filename
    local_path = LOCAL_BLS_DIR / filename
    
    print(f"Downloading {filename}...")

    response = requests.get(url,headers= DOWNLOAD_HEADERS, timeout = 60)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        f.write(response.content)

def sync_bls_files():
    """
    Incrementally sync BLS files from the remote source to local storage.

    - Downloads only new files
    - Does not re-download existing files
    - Safe to re-run (Idempotent)
    """

    # Ensure local directory exists
    ensure_local_directory()

    # Get Remote and local file lists
    remote_files = list_remote_files()
    local_files = list_local_files()

    # Determine which files are new
    new_files = remote_files - local_files

    print(f"Remote files found: {len(remote_files)}")
    print(f"Local files found: {len(local_files)}")
    print(f"New files to download: {len(new_files)}")

    # Download only new files
    for filename in sorted(new_files):
        download_file(filename)

    print("BLS Sync Complete")



if __name__ == "__main__":
    sync_bls_files()
"""
if __name__ == "__main__":
    files = list_remote_files()
    print(f"Number of remote files found: {len(files)}")
    print("Sample files:")
    for f in list(files)[:10]:
        print(f)
"""