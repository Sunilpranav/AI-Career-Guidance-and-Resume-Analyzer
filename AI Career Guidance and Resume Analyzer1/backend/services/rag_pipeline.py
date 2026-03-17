import chromadb
import ollama
import os
from . import ai_engine

persist_dir = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
client = chromadb.PersistentClient(path=persist_dir)

collection = client.get_or_create_collection(name="careers")

def get_embedding(text):
    try:
        # Try newer method
        response = ollama.embed(model=ai_engine.MODEL_NAME, input=text)
        if 'embeddings' in response and len(response['embeddings']) > 0:
            return response['embeddings'][0]
        
        # Fallback
        response = ollama.embeddings(model=ai_engine.MODEL_NAME, prompt=text)
        if 'embedding' in response:
            return response['embedding']
    except Exception as e:
        print(f"Embedding Error: {e}")
    return None

def retrieve_relevant_careers(query_text, n_results=3):
    query_embedding = get_embedding(query_text)
    
    empty_result = {'documents': [[]], 'metadatas': [[]], 'ids': [[]]}
    
    if query_embedding is None:
        return empty_result

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Safety Check: Ensure structure is valid
        if not results: return empty_result
        if not results.get('documents'): return empty_result
        if len(results['documents']) == 0: return empty_result
        
        return results
    except Exception as e:
        print(f"Query Error: {e}")
        return empty_result
