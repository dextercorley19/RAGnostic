# Import required libraries
import boto3
import os
import openai
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import boto3
import os
import uuid
from pinecone import Pinecone

load_dotenv()

# aws
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
s3 = boto3.client('s3')

# openai
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# --- Step 1: Get the document ---
# Output:
# Document containing "CHUNK_HERE" and document with that removed

def remove_chunk_marker(document: str, marker: str = "CHUNK_HERE") -> str:
    """
    Remove all occurrences of a specific marker from the document.

    Args:
    - document (str): The full text document.
    - marker (str): The marker to remove from the document. Default is "CHUNK_HERE".

    Returns:
    - str: The document with the marker removed.
    """
    cleaned_document = document.replace(marker, '')
    cleaned_document = cleaned_document.strip()
    return cleaned_document



document = open("example.txt").read()

markdown_content_to_chunk = document
markdown_content = remove_chunk_marker(document)

# --- Step 2: AWS S3 Setup ---

def upload_to_s3(document_name, content, user_id):
    """Upload a Markdown file to S3 using a combination of user_id, timestamp, and file name."""
    document_id = str(uuid.uuid4())
    timestamp = int(time.time())
    s3_key = f"{user_id}/{timestamp}_{document_id}_{document_name}"
    
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=content,
        ContentType='text/markdown'
    )
    
    s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    print(f"✅ Uploaded to S3: {s3_url}")
    
    return {
        'document_id': document_id,
        's3_url': s3_url,
        's3_key': s3_key,
        'document_name': document_name,
        'user_id': user_id
    }

# Test S3 Upload
user_id = str(uuid.uuid4()) # replace with real user id for production
file_name = "example.md" # change name to whatever you want
document_metadata = upload_to_s3(file_name, markdown_content, user_id) 


# ------------------------------------------
# --- Step 2: Embeddings with OpenAI API ---
# ------------------------------------------

def generate_embeddings(document_content, model="text-embedding-ada-002"):
    """Generate embeddings for a chunk of text."""
    text = document_content.replace("\n", " ")
    print(f"Embedding generated for content length: {len(text)}")
    return client.embeddings.create(input = [text], model=model).data[0].embedding


def chunk_document_by_marker(document: str, marker: str = "CHUNK_HERE") -> list:
    """
    Chunk the document by a specific marker.

    Args:
    - document (str): The full text document to be chunked.
    - marker (str): The marker to indicate where to chunk the document. Default is "CHUNK_HERE".

    Returns:
    - list: A list of text chunks split by the marker.
    """
    chunks = document.split(marker)  # Split the document by the marker
    cleaned_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]  # Remove extra whitespace and empty chunks
    return cleaned_chunks

# Split and embed the Markdown content
chunks = chunk_document_by_marker(markdown_content_to_chunk)
embeddings = [generate_embeddings(chunk) for chunk in chunks]


# ----------------------------------------------
# --- Optional Step 2.5: Store Chunks in S3 ---
# ----------------------------------------------
    
# def store_chunk_in_s3(document_id: str, chunk_index: int, chunk_content: str, user_id) -> str:
#     """Store the chunk content in S3 and return the URL."""
#     chunk_id = f"{document_id}_chunk_{chunk_index}"
#     s3_key = f"{user_id}/{chunk_id}.txt"
    
#     # Upload chunk to S3
#     s3.put_object(
#         Bucket=S3_BUCKET_NAME,
#         Key=s3_key,
#         Body=chunk_content,
#         ContentType='text/plain'
#     )
    
#     s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
#     print(f"Chunk {chunk_index} stored in S3 at {s3_url}")
#     return s3_url

# --------------------------------------------
# --- Step 3: Store Embeddings in Pinecone ---
# --------------------------------------------


pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)
index_name = os.getenv("PINECONE_INDEX_NAME")

index = pc.Index(host=index_name)

def store_embeddings_in_pinecone(chunks, embeddings, document_id, user_id):
    """Store embeddings for each chunk in Pinecone."""
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        
        # If you chose to store the chunks in s3:
        # 1. s3_url = store_chunk_in_s3(document_id, i, chunk, user_id)
        
        vector_id = f"{document_id}_chunk_{i}"
        vectors.append({
            'id': vector_id,
            'values': embedding,
            'metadata': {
                'chunk_index': i,
                'document_id': document_id,
                'user_id': user_id,
                # 2. 's3_url': s3_url,
                'chunk_content': chunk
            }
        })
    index.upsert(vectors=vectors)
    print(f"{len(vectors)} chunks uploaded to Pinecone for document_id: {document_id}")
    
store_embeddings_in_pinecone(chunks, embeddings, document_metadata['document_id'], document_metadata['user_id'])