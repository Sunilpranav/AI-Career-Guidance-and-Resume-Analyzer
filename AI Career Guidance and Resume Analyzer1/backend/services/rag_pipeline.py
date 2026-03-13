import chromadb
from chromadb.utils import embedding_functions
import ollama
import os

# Persistent storage for ChromaDB
# We store it in the backend folder to keep it consistent
persist_directory = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
client = chromadb.PersistentClient(path=persist_directory)

# Use nomic-embed-text via Ollama
embedding_func = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text"
)

collection = client.get_or_create_collection(name="careers", embedding_function=embedding_func)

def add_career_data(documents, metadatas, ids):
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def retrieve_relevant_careers(query_text, n_results=3):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results