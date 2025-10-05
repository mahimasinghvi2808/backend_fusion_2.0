import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv('OLLAMA_HOST')
OLLAMA_MODEL = 'llama3'  # Default model - user can change in .env if needed

def generate_recommendation(prompt, max_tokens=150):
    """
    Generate AI recommendation using Ollama LLM
    Returns generated text
    """
    try:
        response = requests.post(
            f'http://{OLLAMA_HOST}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'options': {
                    'num_predict': max_tokens,
                    'temperature': 0.7
                }
            }
        )
        response.raise_for_status()
        return response.json()['response'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_risk(portfolio_data):
    """
    Generate risk analysis using Ollama LLM
    Returns risk score (0-100) and explanation
    """
    prompt = f"Analyze risk for portfolio: {portfolio_data}. Provide risk score (0-100) and explanation."
    response = generate_recommendation(prompt)
    
    # Simple parsing - in production would use proper JSON parsing
    risk_score = 50  # Default value
    explanation = "Basic risk analysis"
    
    if "risk score" in response.lower():
        parts = response.split()
        for i, part in enumerate(parts):
            if "score" in part.lower() and i+1 < len(parts):
                try:
                    risk_score = min(100, max(0, int(parts[i+1])))
                except:
                    pass
        explanation = response
    
    return {
        'risk_score': risk_score,
        'explanation': explanation
    }
