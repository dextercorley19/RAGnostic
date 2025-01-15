from pipeline import generate_embeddings
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from openai import OpenAI
# IF using S3 for chunks
# import requests

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(
  api_key=api_key)

pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)
index_name = os.getenv("PINECONE_INDEX_NAME")


query = "Explain what the hybrid structure router does as if your audience is grade school students."


# -------------------------------------------------------
# --- Step 4: Query Embeddings (Test Semantic Search) ---
# -------------------------------------------------------

def query_pinecone(query_text):
    """Query the Pinecone index using an embedding of the query text."""
    query_embedding = generate_embeddings(query_text)
    
    query_result = index.query(
        namespace='',
        top_k=10,
        vector=query_embedding,
        include_metadata=True
    )
    
    print(f"🔍 Query Results for: '{query_text}'")
    for match in query_result['matches']:
        print(f"Score: {match['score']}, Content Preview: {match['metadata']['chunk_content']}, Chunk Idx: {match['metadata']['chunk_index']}")
    
    return query_result

# Query the embeddings
# query_results = query_pinecone(query)
# print(query_results)

# -----------------------
# --- Step 6: Chatbot ---
# -----------------------

# Conversation Memory
# Store the conversation in memory (global variable or local state)
conversation_history = []

def update_conversation(user_message: str, assistant_message: str) -> None:
    """Update the conversation history with user and assistant messages."""
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": assistant_message})

def get_conversation_history() -> list:
    """Return the full conversation history."""
    return conversation_history


# ------------------------------
# Retrieve Context from Pinecone
# ------------------------------

# Connect to your index
index = pc.Index(host=index_name)

def retrieve_context(query: str, top_k: int = 10) -> str:
    """Retrieve the most relevant context from Pinecone for the user's query."""
    # Generate embedding for the query
    query_embedding = generate_embeddings(query)
    query_result = index.query(
        namespace='',
        top_k=top_k,
        vector=query_embedding,
        include_metadata=True
    )    
        
    # Retrieve the chunk content for the top-k relevant chunks
    chunks_content = []
    for match in query_result['matches']:
        
    # IF you are using pinecone to store chunk contents
        chunks_content.append(match['metadata']['chunk_content'])
        return chunks_content
    
    
    # IF you are using S3 to store chunk content, not pinecone    
    #     user_id = int(match['metadata']['user_id'])
    #     chunk_index = int(match['metadata']['chunk_index'])
    #     document_id = match['metadata']['document_id']
        
    #     chunk_id = f"{document_id}_chunk_{chunk_index}"
    #     s3_key = f"{user_id}/{chunk_id}.txt"
    #     print(s3_key)
        
    #     presigned_url = generate_presigned_url('nord-prod-documents', s3_key)
    #     # Download the file using the presigned URL
    #     response = requests.get(presigned_url)
    #     if response.status_code == 200:
    #         print(f"Successfully retrieved content from S3 for chunk: {chunk_id}")
    #         chunks_content.append(response.text)
    #     else:
    #         print(f"Failed to retrieve content (Status: {response.status_code})")
        
        
    # print(f"Retrieved {len(chunks_content)} chunks of content from S3.")
    # return chunks_content
    
# ------------------------------------    
# Call ChatGPT with Context and Memory
# ------------------------------------


def chat_with_gpt(query: str) -> str:
    """Send the query to ChatGPT along with context and memory."""
    # Get context from Pinecone
    context = retrieve_context(query, top_k=5)
    
    # Get conversation history
    history = get_conversation_history()
    
    # Build prompt
    system_message = {
        "role": "assistant", 
        "content": (
            "You are a helpful assistant. Use the following context to answer the user's question.\n\n"
            f"Context:\n{context}\n\n"
            "Conversation history:\n" + 
            "\n".join([f"{msg['role']}: {msg['content']}" for msg in history]) + 
            "\n\n"
        )
    }
    
    messages = [system_message] + history + [{"role": "user", "content": query}]
    
    # Send to OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or newer depending on your needs, I've found that 3.5 good enough with RAG
        messages=messages
    )
    
    assistant_message = response.choices[0].message.content

    # Update conversation history
    update_conversation(query, assistant_message)
    
    # Return the context as well if you're interested to see what it deemed relevant
    return assistant_message #, context