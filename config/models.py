MODEL_CONFIGS = {
    "qwen2-7b": {
        "name": "qwen2-7b-instruct-q4_k_m.gguf",
        "path": "./data/qwen2-7b-instruct-q4_k_m.gguf",
        "type": "llama_cpp",
        "max_tokens_default": 32,
        "temperature_default": 0.3,
        "top_p_default": 0.9,
        "url": None,
    },
    "qwen2-72b": {
        "name": "qwen2:72b-instruct-q4_K_S",
        "path": "<not needed served by ollama>",
        "type": "ollama",
        "max_tokens_default": 1024,
        "temperature_default": 0.3,
        "top_p_default": 0.9,
        "url": "http://localhost:11434/api/generate",
    },
    "phi4-mini": {
        "name": "phi4-mini",
        "path": "<not needed served by ollama>",
        "type": "ollama",
        "max_tokens_default": 1024,
        "temperature_default": 0.3,
        "top_p_default": 0.9,
        "url": "http://localhost:11434/api/generate",
    }
}