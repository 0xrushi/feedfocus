from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Union
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import requests
from fastapi.responses import HTMLResponse
from config.platforms import PLATFORM_CONFIGS
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from db import LogsDB
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

db = LogsDB()  # Use the new DB class


app = FastAPI(title="Groq API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamically instantiate LLM backend from config
llm_config = PLATFORM_CONFIGS["twitter"].llm_config
if llm_config["backend"] == "ollama":
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=llm_config["model"],
        temperature=llm_config.get("temperature", 0.8),
        base_url=llm_config["base_url"],
    )
# elif llm_config["backend"] == "groq":
#     from langchain_groq import ChatGroq
#     llm = ChatGroq(...)
else:
    raise ValueError(f"Unsupported LLM backend: {llm_config['backend']}")


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
    """
    Endpoint for generating AI completions and logging tweet analysis.
    """
    try:
        logger.debug(f"Received completion request: {request}")
        prompt_template = PLATFORM_CONFIGS["twitter"].filter_prompt
        formatted_prompt = prompt_template.format(content=request.prompt)
        logger.debug(f"Formatted prompt: {formatted_prompt}")

        if not db.tweet_exists(request.prompt):
            messages = [("human", formatted_prompt)]
            logger.debug(f"LLM messages: {messages}")
            response = llm.invoke(messages)
            logger.debug(f"LLM response: {response}")

            response_text = response.content
            is_ai_related = "YES" in response_text.strip().upper()
            logger.debug(f"Is AI-related: {is_ai_related}")

            db.insert_log(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request.prompt,
                request.user_name,
                is_ai_related,
                request.tweet_url,
            )
            logger.debug(f"Inserted log for tweet: {request.prompt}")
            return CompletionResponse(
                text=response_text,
                usage={
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None,
                },
            )
        logger.debug(f"Tweet already present in logs: {request.prompt}")
        return CompletionResponse(
            text="Tweet already present",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )
    except Exception as e:
        logger.exception("Error in generate_completion")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "phi3"}


@app.get("/logs")
async def get_tweet_logs():
    """Retrieve tweet logs from the last 24 hours that are AI-related."""
    try:
        one_day_ago = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"Fetching AI-related logs since: {one_day_ago}")
        results = db.get_ai_related_logs(one_day_ago)
        logger.debug(f"Fetched {len(results)} logs")
        return results
    except Exception as e:
        logger.exception("Error in get_tweet_logs")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/{platform}", response_class=HTMLResponse)
async def analyze_tweets(platform: str = "twitter"):
    """Analyze AI-related tweets and provide a summary of key developments."""
    try:
        one_day_ago = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"Analyzing tweets since: {one_day_ago}")
        tweets = db.get_ai_related_logs(one_day_ago)
        logger.debug(f"Number of tweets to analyze: {len(tweets)}")

        if not tweets:
            logger.debug("No tweets found for analysis.")
            return (
                "<div class='analysis-container'>Nothing much interesting found.</div>"
            )

        tweets_text = "\n".join(
            [
                f"Tweet by {t['user_name']}: {t['tweet']} (URL: {t['tweet_url'] or 'N/A'})"
                for t in tweets
            ]
        )
        logger.debug(
            f"Tweets text for analysis prompt: {tweets_text[:300]}{'...' if len(tweets_text) > 300 else ''}"
        )

        prompt_template = PLATFORM_CONFIGS["twitter"].analysis_prompt
        analysis_prompt = prompt_template.format(content=tweets_text)
        logger.debug(
            f"Analysis prompt: {analysis_prompt[:300]}{'...' if len(analysis_prompt) > 300 else ''}"
        )

        messages = [
            ("system", PLATFORM_CONFIGS["twitter"].system_prompt),
            ("human", analysis_prompt),
        ]
        logger.debug(f"LLM messages for analysis: {messages}")
        result = llm.invoke(messages)
        logger.debug(f"LLM analysis result: {result}")

        summary = result.content.strip()
        formatted_summary = summary.replace("\n", "<br>")
        formatted_summary = formatted_summary.replace("&lt;", "<").replace("&gt;", "")

        logger.debug(
            f"Formatted summary: {formatted_summary[:300]}{'...' if len(formatted_summary) > 300 else ''}"
        )
        return f"""
        <div class='analysis-container'>
            <div class='analysis-summary'>{formatted_summary}</div>
            <div class='tweet-count'>Analyzed {len(tweets)} tweets</div>
        </div>
        """
    except Exception as e:
        logger.exception("Error in analyze_tweets")
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host="0.0.0.0", port=PLATFORM_CONFIGS["twitter"].port):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
