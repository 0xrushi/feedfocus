from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
from typing import Optional, List, Union
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import csv
from datetime import datetime
import os
import sqlite3
import requests
from fastapi.responses import HTMLResponse
from config.platforms import PLATFORM_CONFIGS
from config.models import MODEL_CONFIGS

# Connect to database
conn = sqlite3.connect('logs.db')
cursor = conn.cursor()

# Create table with unique constraint on tweet
cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id TEXT,
        tweet TEXT UNIQUE,
        response TEXT,
        user_name TEXT,
        tweet_url TEXT
    )
''')

# Example of inserting data
def insert_log(id, tweet, user_name, model_response, tweet_url=None):
    cursor.execute('''
        INSERT OR IGNORE INTO logs (id, tweet, user_name, response, tweet_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, tweet, user_name, model_response, tweet_url))
    conn.commit()

app = FastAPI(title="Llama API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_path = MODEL_CONFIGS["qwen2-7b"]["path"]
small_llm = Llama(
    model_path=model_path,
)

class CompletionRequest(BaseModel):
    prompt: str
    user_name: str
    tweet_url: Optional[str] = None
    max_tokens: Optional[int] = 32
    stop: Optional[Union[str, List[str]]] = None
    echo: Optional[bool] = False
    temperature: Optional[float] = 0.8
    top_p: Optional[float] = 0.95

class CompletionResponse(BaseModel):
    text: str
    usage: dict

@app.post("/completion", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):    
    try:
        prompt_template = PLATFORM_CONFIGS["twitter"].filter_prompt
        formatted_prompt = prompt_template.format(
            content=request.prompt
        )
            
        output = small_llm(
            prompt=formatted_prompt,
            max_tokens=request.max_tokens,
            stop=request.stop,
            echo=request.echo,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        response_text = output['choices'][0]['text']
        
        is_ai_related = "YES" in response_text.strip().upper()
        
        insert_log(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            request.prompt, 
            request.user_name, 
            is_ai_related,
            request.tweet_url
        )
        
        return CompletionResponse(
            text=response_text,
            usage=output.get('usage', {})
        )
    except Exception as e:
        log_response(str(e), "error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    # Log health check
    log_response("Health check performed", "health_check")
    return {"status": "healthy", "model": "qwen2-7b-instruct"}


@app.get("/logs")
async def get_tweet_logs():
    """Retrieve tweet logs with optional filtering for AI-related tweets."""
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, tweet, response, user_name, tweet_url
            FROM logs
            WHERE response = 1
            ORDER BY id DESC
        ''')
        
        columns = ['id', 'tweet', 'response', 'user_name', 'tweet_url']
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{platform}", response_class=HTMLResponse)
async def analyze_tweets(platform: str = "twitter"):
    """Analyze AI-related tweets and provide a summary of key developments."""
    try:
        tweets = await get_tweet_logs()
        
        if not tweets:
            return "<div class='analysis-container'>Nothing much interesting found.</div>"
            
        # Prepare tweets text - don't encode URLs
        tweets_text = "\n".join([
            f"Tweet by {t['user_name']}: {t['tweet']} (URL: {t['tweet_url'] or 'N/A'})"
            for t in tweets
        ])
        
        prompt_template = PLATFORM_CONFIGS["twitter"].analysis_prompt
        analysis_prompt = prompt_template.format(
            content=tweets_text
        )
        model_name = MODEL_CONFIGS["qwen2-72b"]["name"]
        model_url = MODEL_CONFIGS["qwen2-72b"]["url"]
        # Use requests to call Ollama API
        response = requests.post(
            model_url,
            json={
                "model": model_name,
                "prompt": analysis_prompt,
                "stream": False
            }
        )
        
        result = response.json()
        summary = result.get('response', '').strip()
        
        formatted_summary = summary.replace('\n', '<br>')
        formatted_summary = formatted_summary.replace('&lt;', '<').replace('&gt;', '>')
        
        return f"""
        <div class='analysis-container'>
            <div class='analysis-summary'>{formatted_summary}</div>
            <div class='tweet-count'>Analyzed {len(tweets)} tweets</div>
        </div>
        """
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host="0.0.0.0", port=PLATFORM_CONFIGS["twitter"].port):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()