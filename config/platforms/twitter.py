from dataclasses import dataclass
from typing import Dict, List, Optional
from langchain.prompts import PromptTemplate

@dataclass
class PlatformConfig:
    """Configuration for a specific platform's content analysis"""
    filter_prompt: PromptTemplate
    analysis_prompt: PromptTemplate
    port: int
    recommended_models: Dict[str, str]

class PromptTemplates:
    """Base templates for content filtering and analysis"""
    
    BASE_FILTER = """<|im_start|>system
You are a {platform} Content Filter, an AI system that follows these rules:
{filter_rules}
Follow the above instructions and return YES or NO.
<|im_end|>
<|im_start|>user
{content_type}: {content}
<|im_end|>
<|im_start|>assistant"""

    BASE_ANALYSIS = """<|im_start|>system
You are an AI Industry Analyst who analyzes {platform} content about AI developments. Focus on:
{analysis_focus}

For each significant development, provide:
{output_format}

Skip any {content_type} that are about {exclude_content}.
Format multiple findings as separate entries with a blank line between them.
<|im_end|>
<|im_start|>user
Analyze these {content_type}s and extract the key developments:

{content}
<|im_end|>
<|im_start|>assistant"""

class TwitterRules:
    """Twitter-specific filtering rules and analysis parameters"""
    
    FILTER_RULES = """I have a JSON file of tweets. For each tweet, return YES if it mentions:
•   New developments in AI agents.
•   Releases of new LLMs (e.g., ChatGPT, Claude, v0, Cursor) or updates from OpenAI/Anthropic
•   Announcements of models outperforming others or setting new benchmarks or AI Agents
•   Announcements related to finance, quant or research papers or algorithmic trading

Exclude any tweets about courses, tutorials, or general discussions. Return NO for all other tweets."""

    ANALYSIS_FOCUS = """
- New AI models and capabilities
- Major releases from AI companies
- Performance breakthroughs and benchmarks
- Financial and trading developments"""

    OUTPUT_FORMAT = """
SUMMARY: One-line description of the key development
BY: The Twitter username
URL: The full tweet URL provided in parentheses"""

    EXCLUDE_CONTENT = "tutorials, courses, or general discussions"

def create_twitter_config() -> PlatformConfig:
    """Create Twitter platform configuration"""
    
    # Create Twitter filter prompt
    filter_prompt = PromptTemplate(
        input_variables=["content"],
        template=PromptTemplates.BASE_FILTER.format(
            platform="Twitter",
            filter_rules=TwitterRules.FILTER_RULES,
            content_type="Tweet",
            content="{content}"
        )
    )

    # Create Twitter analysis prompt
    analysis_prompt = PromptTemplate(
        input_variables=["content"],
        template=PromptTemplates.BASE_ANALYSIS.format(
            platform="Twitter",
            content_type="tweet",
            analysis_focus=TwitterRules.ANALYSIS_FOCUS,
            output_format=TwitterRules.OUTPUT_FORMAT,
            exclude_content=TwitterRules.EXCLUDE_CONTENT,
            content="{content}"
        )
    )

    return PlatformConfig(
        filter_prompt=filter_prompt,
        analysis_prompt=analysis_prompt,
        port=8000,
        recommended_models={
            "filter": "qwen2-7b",  # for quick YES/NO
            "analysis": "qwen2-72b"  # for detailed analysis
        }
    )

TWITTER_CONFIG = create_twitter_config()