import logging
import traceback
import requests
from google.cloud import storage, firestore
import os
import sys

# There is a bug in the latest VertexAI Vision library that makes this monkeypatch necessary
def custom_excepthook(exc_type, exc_value, exc_traceback):
    # Do not print exception when user cancels the program
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("An uncaught exception occurred:")
    logging.error("Type: %s", exc_type)
    logging.error("Value: %s", exc_value)

    if exc_traceback:
        format_exception = traceback.format_tb(exc_traceback)
        for line in format_exception:
            logging.error(repr(line))

sys.excepthook = custom_excepthook

# Create a firestore client
db = firestore.Client()

def process_image(data, context):
    logging.info("Function started.")
    logging.info("Received data: " + str(data))
    
    try:
        attributes = data.get('attributes', {})
        event_type = attributes.get('eventType')
        bucket_id = attributes['bucketId']
        object_id = attributes['objectId']
        
        if event_type != "OBJECT_FINALIZE":
            logging.info("Event type is not OBJECT_FINALIZE. Exiting function.")
            return "No action taken"

        # Initialize a client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_id)
        blob = bucket.blob(object_id)

        # Download the blob to a local file
        blob.download_to_filename(f'/tmp/{object_id}')
        logging.info(f'{object_id} downloaded to /tmp/{object_id}.')

        caption = get_captions(f'/tmp/{object_id}')

        # Store filename and combined information in Firestore
        doc_ref = db.collection('captions').document(object_id)
        doc_ref.set({
            'filename': object_id,
            'info': caption
        })

        logging.info(f"Stored {object_id} and its info in Firestore.")
    except Exception as e:
        stack_trace = traceback.format_exc()
        logging.error(f"Error during processing: {e}\n{stack_trace}")
    return "Processed image data"

def get_captions(filename):
    api_url = "<our cloud run API URL>"

    with open(filename, 'rb') as img_file:
        response = requests.post(api_url, files={'image': img_file})

    if response.status_code == 200:
        data = response.json()
        return data.get('captions', "")
    else:
        logging.error(f"Error getting captions: {response.text}")
        return ""

print(process_image({
    "attributes": {
        "bucketId": "my-bucket-name",
        "eventType": "OBJECT_FINALIZE",
        "objectId": "image01.png"
    }
}, {}))
