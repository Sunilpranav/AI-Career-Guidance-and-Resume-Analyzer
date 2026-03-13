import sys
import json
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.rag_pipeline import add_career_data

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'career_data.json')

def main():
    with open(DATA_FILE, 'r') as f:
        careers = json.load(f)
    
    docs = []
    metas = []
    ids = []

    for c in careers:
        text = f"Title: {c['title']}. Description: {c['description']}. Skills: {', '.join(c['required_skills'])}. Tools: {', '.join(c['tools'])}."
        docs.append(text)
        metas.append({"title": c['title'], "skills": ", ".join(c['required_skills'])})
        ids.append(c['id'])

    print("Ingesting data into ChromaDB...")
    add_career_data(docs, metas, ids)
    print("Done.")

if __name__ == "__main__":
    main()