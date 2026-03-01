import os
from bls_sync import sync_bls_files
from population import run as run_population

def lambda_handler(event,context):
    '''
    AWS Lambda entry point.

    Executes:
    - BLS incrementa sync
    - Population API ingestion
    '''

    print('Starting ingestion pipeline..')
    try:
        #Run BLS Ingestion
        sync_bls_files()

        #Run population Ingestion
        run_population()

        print("Ingestion Completed Successfully")

        return{
            'statusCode': 200,
            'body': 'Ingestion Completed'
        }
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise