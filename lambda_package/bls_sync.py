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
import boto3
#from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv()

# ==============================================
# S3 CONFIGURATION
# ==============================================
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET', 'rearc-data-quest-milan-prod')
S3_PREFIX = 'raw/bls/'

# Initialize S3 client (only if USE_S3 is enabled)
s3_client = boto3.client('s3') if USE_S3 else None

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

def list_s3_files():
    '''
    List all files already present is S3 bucket under raw/bls/ prefix.

    Returns:
        set: Set of filenames (e.g.,{'pr.data.0.Current','pr.class',...})
    '''
    try:
        response = s3_client.list_objects_v2(
            Bucket = S3_BUCKET,
            Prefix = S3_PREFIX
            )
        #Handle empty bucket (no 'Contents' Key)
        if 'Contents' not in response:
            return set()
        
        files = set()
        for obj in response['Contents']:
            # Extract just file name from full S3 key
            # 'raw/bls/pr.data.0.Current' -> 'pr.data.0.Current'
            filename = obj['Key'].split('/')[-1]

            #Skkip empty keys (Directory markers)
            if filename:
                files.add(filename)
        return files
    
    except Exception as e:
        print(f'Error listing S3 files: {e}')
        return set()

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

def download_file_content(filename):
    '''
    Downloads a single BLS file and returns its content (without saving).

    Returns:
        bytes: File content in binary format
    '''

    url = BLS_BASE_URL + filename
    print(f'Downloading {filename}...')

    response = requests.get(url, headers=DOWNLOAD_HEADERS, timeout=60)
    response.raise_for_status()

    return response.content

def upload_to_s3(filename, content):
    '''
    Uploads file content to S3. bucket.


    Args:
        filename(str): Just the filename (e.g. 'pr.data.0.Current')
        contents(bytes): Binary content from HTTP response
    '''

    s3_key = S3_PREFIX + filename #'raw/bls/'+'pr.data.0.Current'

    try:
        s3_client.put_object(
            Bucket = S3_BUCKET,
            Key = s3_key,
            Body = content,
            ContentType = 'text/plain'
        )

        print(f'Uploaded to S3: s3://{S3_BUCKET}/{s3_key}')

    except Exception as e:
        print(f'Error uploading {filename} to S3: {e}')

def sync_bls_files():
    """
    Incrementally sync BLS files from the remote source to local storage.

    - Downloads only new files
    - Does not re-download existing files
    - Safe to re-run (Idempotent)
    """

    # Ensure local directory exists
    if not USE_S3:
        ensure_local_directory()

    # Get Remote and local file lists
    remote_files = list_remote_files()
    existing_files = list_s3_files() if USE_S3 else list_local_files()
    #local_files = list_local_files()

    # Determine which files are new
    new_files = remote_files - existing_files

    print(f"Remote files found: {len(remote_files)}")
    print(f"Existing files files found: {len(existing_files)}")
    print(f"New files to download: {len(new_files)}")

    # Download only new files
    for filename in sorted(new_files):
        try:
            if USE_S3:
                #S3 mode: download content and upload to S3
                content = download_file_content(filename)
                upload_to_s3(filename,content)
            else:
                #Local mode: use local tesing function
                download_file(filename)
        except Exception as e:
            print(f'Failed to process {filename}: {e}')
            #Continue with other files instead of stopping

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