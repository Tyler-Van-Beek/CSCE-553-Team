import openai
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from pathlib import Path

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
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-4o-mini"

openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)


def get_embedding(text):
    response = openai.Embedding.create(input=text, model=EMBEDDING_MODEL)
    return response["data"][0]["embedding"]


def query_similar_events(user_query, top_k=3):
    index = pc.Index(INDEX_NAME)
    query_embedding = get_embedding(user_query)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

    events = []
    for match in results['matches']:
        metadata = match['metadata']
        events.append(f"Title: {metadata['title']}\nSummary: {metadata['summary']}\n")

    return events


def get_recommendation(user_query):
    similar_events = query_similar_events(user_query)

    prompt = f"""You are a helpful assistant. A user asked: "{user_query}"

Here are 3 recent current events that may be relevant:
{chr(10).join(similar_events)}

Based on these, what would you recommend? Provide a thoughtful answer.
"""

    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    user_input = input("🔍 Ask your question: ")
    answer = get_recommendation(user_input)
    print("\n💡 Recommendation:\n")
    print(answer)
    