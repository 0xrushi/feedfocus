# FeedFocus: Turn Endless Feeds into Quick Insights

Are you tired of losing hours to endless scrolling on Twitter, LinkedIn, or Reddit? FeedFocus simplifies your day by curating and summarizing the content that matters most to you. Stay updated on AI breakthroughs, industry trends, and niche discussions—all without the noise.

Reclaim your time: FeedFocus transforms hours of browsing into just minutes of actionable updates.

## Getting Started

Follow these steps to set up FeedFocus on your machine:

### 1. Set Up Your Environment

Start by creating and activating a virtual environment:

```
python -m venv venv  
source venv/bin/activate  
```

Move to the project directory and install dependencies:

```
cd feedfocus  
pip install -r requirements.txt  
```

### 2. Model Configuration

Download `qwen2-7b-instruct-q4_k_m.gguf` and place it in the data folder.

Run the Ollama server to host the Qwen model:
```
ollama pull qwen2:72b-instruct-q4_K_S  
ollama serve  
```

### 3. Configure Your Settings

Update the configuration files:
	•	config/models.py
	•	config/platforms/twitter.py

### 4. Install Browser Extension

Install the Tampermonkey extension for Chrome.

•	Copy the script from userscripts/v3.js.

•	Paste it into a new script in Tampermonkey and enable it.

### 5. Run the Server

Start the FeedFocus server with:
```
python twitter_server.py  
```

### 6. Capture Your Feed

Open x.com (formerly Twitter) and start scrolling. Use the Page Down key or scroll manually to let the script capture content for summarization.

Or run the below script to automatically press pagedown
```
python press_pgdown.py
```
