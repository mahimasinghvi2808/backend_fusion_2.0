import weaviate
from weaviate.auth import AuthApiKey
from dotenv import load_dotenv
import os
import json

load_dotenv()

WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')

# Initialize Weaviate client with proper v4 API
try:
    client = weaviate.connect_to_custom(
        http_host=WEAVIATE_URL.replace('https://', '').replace('http://', ''),
        http_port=443,
        http_secure=True,
        auth_credentials=AuthApiKey(api_key=WEAVIATE_API_KEY),
        headers={'X-OpenAI-Api-Key': os.getenv('OPENAI_API_KEY')}
    )
except Exception as e:
    print(f"Warning: Could not connect to Weaviate: {e}")
    client = None

# Schema definitions
def initialize_schema():
    if not client:
        print("Warning: Weaviate client not initialized, skipping schema initialization")
        return
    
    try:
        # Market News Class
        if client.collections.exists('MarketNews'):
            client.collections.delete('MarketNews')
        client.collections.create(
            name='MarketNews',
            description='Market news articles with embeddings',
            properties=[
                {'name': 'title', 'data_type': 'text'},
                {'name': 'content', 'data_type': 'text'},
                {'name': 'timestamp', 'data_type': 'date'},
            ]
        )

        # User Conversation Class
        if client.collections.exists('UserConversation'):
            client.collections.delete('UserConversation')
        client.collections.create(
            name='UserConversation',
            description='User conversation history with embeddings',
            properties=[
                {'name': 'user_id', 'data_type': 'int'},
                {'name': 'message', 'data_type': 'text'},
                {'name': 'timestamp', 'data_type': 'date'},
            ]
        )

        # Recommendation Class
        if client.collections.exists('Recommendation'):
            client.collections.delete('Recommendation')
        client.collections.create(
            name='Recommendation',
            description='AI-generated recommendations with embeddings',
            properties=[
                {'name': 'user_id', 'data_type': 'int'},
                {'name': 'text', 'data_type': 'text'},
                {'name': 'timestamp', 'data_type': 'date'},
            ]
        )
    except Exception as e:
        print(f"Error initializing schema: {e}")

# CRUD operations
def add_market_news(title, content, timestamp, vector):
    if not client:
        return {"error": "Weaviate client not available"}
    try:
        collection = client.collections.get('MarketNews')
        collection.data.insert(
            properties={
                'title': title,
                'content': content,
                'timestamp': timestamp,
            },
            vector=vector
        )
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def search_market_news(query_vector, limit=5):
    if not client:
        return []
    try:
        collection = client.collections.get('MarketNews')
        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit
        )
        return [obj.properties for obj in response.objects]
    except Exception as e:
        print(f"Error searching market news: {e}")
        return []

def add_conversation(user_id, message, timestamp, vector):
    if not client:
        return {"error": "Weaviate client not available"}
    try:
        collection = client.collections.get('UserConversation')
        collection.data.insert(
            properties={
                'user_id': user_id,
                'message': message,
                'timestamp': timestamp,
            },
            vector=vector
        )
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def get_conversation_history(user_id, limit=10):
    if not client:
        return []
    try:
        collection = client.collections.get('UserConversation')
        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("user_id").equal(user_id),
            limit=limit
        )
        return [obj.properties for obj in response.objects]
    except Exception as e:
        print(f"Error getting conversation history: {e}")
        return []

def add_recommendation(user_id, text, timestamp, vector):
    if not client:
        return {"error": "Weaviate client not available"}
    try:
        collection = client.collections.get('Recommendation')
        collection.data.insert(
            properties={
                'user_id': user_id,
                'text': text,
                'timestamp': timestamp,
            },
            vector=vector
        )
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def search_recommendations(query_vector, user_id=None, limit=5):
    if not client:
        return []
    try:
        collection = client.collections.get('Recommendation')
        filters = None
        if user_id:
            filters = weaviate.classes.query.Filter.by_property("user_id").equal(user_id)
        
        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            filters=filters
        )
        return [obj.properties for obj in response.objects]
    except Exception as e:
        print(f"Error searching recommendations: {e}")
        return []
