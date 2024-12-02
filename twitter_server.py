from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Union
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime, timedelta
import os
import requests
from fastapi.responses import HTMLResponse
from config.platforms import PLATFORM_CONFIGS
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

conn = sqlite3.connect('logs.db')
cursor = conn.cursor()

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

def tweet_exists(tweet_text: str):
    """
    Check if a tweet with the given text exists in the logs table.
    Args:
        tweet_text: The text content of the tweet to check
    Returns:
        bool: True if tweet exists, False otherwise
    """
    cursor.execute('SELECT EXISTS(SELECT 1 FROM logs WHERE tweet = ?)', (tweet_text,))
    result = cursor.fetchone()[0]
    return bool(result)

app = FastAPI(title="Groq API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGroq(
    api_key=os.environ["GROQ_API_KEY"],
    model_name="mixtral-8x7b-32768"
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
        
        if not tweet_exists(request.prompt):
            messages = [HumanMessage(content=formatted_prompt)]
            response = llm.invoke(messages)
            
            response_text = response.content
            
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
                usage={"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
            )
        return CompletionResponse(
                text="Tweet already present",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "mixtral-8x7b-32768"}

@app.get("/logs")
async def get_tweet_logs():
    """Retrieve tweet logs from the last 24 hours that are AI-related."""
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        
        one_day_ago = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT id, tweet, response, user_name, tweet_url
            FROM logs
            WHERE response = 1
            AND id >= ?
            ORDER BY id DESC
        ''', (one_day_ago,))
        
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
            
        tweets_text = "\n".join([
            f"Tweet by {t['user_name']}: {t['tweet']} (URL: {t['tweet_url'] or 'N/A'})"
            for t in tweets
        ])
        
        prompt_template = PLATFORM_CONFIGS["twitter"].analysis_prompt
        analysis_prompt = prompt_template.format(
            content=tweets_text
        )

        messages = [HumanMessage(content=analysis_prompt)]
        result = llm.invoke(messages)
        
        summary = result.content.strip()
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