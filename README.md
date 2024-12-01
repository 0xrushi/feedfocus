# FeedFocus: Turn Endless Feeds into Quick Insights

Are you tired of losing hours to endless scrolling on Twitter? FeedFocus simplifies your day by curating and summarizing the content that matters most to you. Stay updated on AI breakthroughs, industry trends, and niche discussions—all without the noise.

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

Install the [Tampermonkey](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) extension for Chrome.

•	Copy the script from userscripts/v3.js.

•	Paste it into a new script in Tampermonkey and enable it.

![image](https://github.com/user-attachments/assets/72eb03bd-faa9-4511-ad7b-13ccd83de621)
![image](https://github.com/user-attachments/assets/fcf4b57c-d28c-47d1-aabe-31609a01d8dd)

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

## Demo GIF
![output](https://github.com/user-attachments/assets/877fcdb9-14be-424d-a62b-71fb23b30b41)

#### Anthropic Claude
![image](https://github.com/user-attachments/assets/2cd3ca19-5738-42bd-8f43-da22145fc009)

#### Qwen2 72b 4bit gguf
![image](https://github.com/user-attachments/assets/9a830f81-7143-4f56-af1d-85ba2de3cb7a)



