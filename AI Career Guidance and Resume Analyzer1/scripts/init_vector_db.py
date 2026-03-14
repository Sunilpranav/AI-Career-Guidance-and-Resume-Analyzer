import sys
import json
import os
import shutil
import time

# Setup Paths
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

import chromadb
import ollama 
from backend.services import ai_engine

# Config
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'chroma_db')
DATA_FILE = os.path.join(PROJECT_ROOT, 'backend', 'data', 'career_data.json')

def main():
    # 1. Clean up old database
    if os.path.exists(DB_PATH):
        print(f"Deleting old database...")
        try:
            shutil.rmtree(DB_PATH)
        except Exception as e:
            print(f"Could not delete automatically. Please manually delete the folder: {DB_PATH}")
            print(f"Error: {e}")
            return

    # 2. Initialize ChromaDB (No embedding function, we do it manually)
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    # We create the collection WITHOUT an embedding function
    collection = client.get_or_create_collection(name="careers")

    # 3. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        return

    with open(DATA_FILE, 'r') as f:
        careers = json.load(f)
    
    print(f"Found {len(careers)} careers.")
    print("Generating embeddings one by one (this may take a few minutes)...")

    # 4. Process ONE BY ONE
    docs = []
    metas = []
    ids = []
    embeddings = []

    for i, c in enumerate(careers):
        try:
            # Create text
            text = f"Title: {c['title']}. Description: {c['description']}. Skills: {', '.join(c['required_skills'])}. Tools: {', '.join(c['tools'])}. Responsibilities: {c['responsibilities']}. Salary: {c.get('salary_range', 'N/A')}. Future: {c.get('future_scope', 'N/A')}."
            
            # Generate embedding manually using ollama library
            # This uses the model defined in ai_engine.py
            emb_response = ollama.embeddings(model=ai_engine.MODEL_NAME, prompt=text)
            vector = emb_response['embedding']

            docs.append(text)
            metas.append({"title": c['title'], "skills": ", ".join(c['required_skills'])})
            ids.append(c['id'])
            embeddings.append(vector)

            # Print progress every 10 items
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(careers)} careers...")
                
        except Exception as e:
            print(f"Error processing item {i+1} ({c['title']}): {e}")
            print("Skipping...")

    # 5. Add to ChromaDB in one go (now that we have vectors)
    if docs:
        print(f"Adding {len(docs)} documents to database...")
        collection.add(
            documents=docs,
            embeddings=embeddings,
            metadatas=metas,
            ids=ids
        )
        print("Success! Data fully ingested.")
    else:
        print("No data was processed.")

if __name__ == "__main__":
    main()
