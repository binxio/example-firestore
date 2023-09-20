from google.cloud import firestore

# Initialize the Firestore client
db = firestore.Client()

def get_all_captions_from_firestore():
    # Reference to the captions collection
    captions_ref = db.collection('captions')
    
    # Get all documents from the captions collection
    docs = captions_ref.stream()
    
    # Create a dictionary to store the results
    captions_data = {}
    
    # Loop through the documents and store the data in the dictionary
    for doc in docs:
        doc_data = doc.to_dict()
        filename = doc_data.get('filename')
        info = doc_data.get('info')
        captions_data[filename] = info
    
    return captions_data

print(get_all_captions_from_firestore())

