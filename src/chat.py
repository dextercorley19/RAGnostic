from pinecone import Pinecone
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI and Pinecone clients
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
index = pc.Index(host=index_name)

# Conversation memory
conversation_history = []

def update_conversation(user_message: str, assistant_message: str) -> None:
    """Update the conversation history with user and assistant messages."""
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": assistant_message})

def get_conversation_history() -> list:
    """Return the full conversation history."""
    return conversation_history

def generate_embeddings(document_content, model="text-embedding-ada-002"):
    """Generate embeddings for a chunk of text."""
    text = document_content.replace("\n", " ")
    print(f"Embedding generated for content length: {len(text)}")
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def retrieve_context(query: str, top_k: int = 10) -> str:
    """Retrieve the most relevant context from Pinecone for the user's query."""
    query_embedding = generate_embeddings(query)
    query_result = index.query(
        namespace='',
        top_k=top_k,
        vector=query_embedding,
        include_metadata=True
    )
    return [match['metadata']['chunk_content'] for match in query_result['matches']]

def chat_with_gpt(query: str) -> str:
    """Send the query to ChatGPT along with context and memory."""
    context = retrieve_context(query, top_k=5)
    history = get_conversation_history()
    
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
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # could use a newer model, but I've found that 3.5 works well with RAG and is much cheaper
        messages=messages
    )
    
    assistant_message = response.choices[0].message.content
    update_conversation(query, assistant_message)
    return assistant_message

def main():
    """Main loop for interactive chatbot."""
    print("🤖 Chatbot is ready! Type your message or 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        response = chat_with_gpt(user_input)
        print(f"Assistant: {response}")

if __name__ == "__main__":
    main()