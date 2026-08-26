from pathlib import Path
import sqlite3
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv

# Load .env file (if running the bot standalone)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

def get_api_key(filename):
    """ Given a filename, return the API key in that file """
    try:
        with open(filename, 'r') as f:
            # File should contain a single line, with the API key
            return f.read().strip()
    except FileNotFoundError:
        print("'%s' file not found" % filename)

#OPENAI_API_KEY = get_api_key('openAI_APIkey')
#PINECONE_API_KEY = get_api_key('pinecone_APIkey')
INDEX_NAME = "myindex"
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db.sqlite3"
EMBEDDING_MODEL = "text-embedding-ada-002"

client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)


def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding


def ensure_index(dimension=1536):
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            INDEX_NAME,
            dimension=1536, # dimensionality of text-embedding-ada-002
            metric='cosine',
            spec=ServerlessSpec(cloud = 'aws', region = 'us-east-1')
        )
    return pc.Index(INDEX_NAME)


def populate_index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT EventID, Title, Description FROM events_event")
    rows = cursor.fetchall()

    index = ensure_index()
    to_upsert = []

    for row in rows:
        event_id, title, summary = row
        content = f"{title}. {summary}"
        embedding = get_embedding(content)
        metadata = {"title": title, "summary": summary}
        to_upsert.append((str(event_id), embedding, metadata))

    index.upsert(vectors=to_upsert)
    print(f"✅ Upserted {len(to_upsert)} events to Pinecone.")


if __name__ == "__main__":
    populate_index()
