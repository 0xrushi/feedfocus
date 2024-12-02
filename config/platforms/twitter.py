from dataclasses import dataclass
from typing import Dict, List, Optional
from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

@dataclass
class PlatformConfig:
    """Configuration for a specific platform's content analysis"""
    filter_prompt: ChatPromptTemplate
    analysis_prompt: ChatPromptTemplate
    port: int
    recommended_models: Dict[str, str]

class PromptTemplates:
    """Base templates for content filtering and analysis"""
    
    BASE_FILTER_SYSTEM = """You are a Twitter content classifier focused on AI industry developments.
Your task is to identify tweets about significant AI developments by returning only YES or NO.

Include tweets about:
- New AI model releases or major updates (e.g., GPT-4, Claude 3, Gemini)
- Significant AI agent developments or breakthroughs
- AI performance benchmarks and competition results
- AI in finance, quantitative research, or algorithmic trading
- Research paper announcements with notable findings

Exclude tweets about:
- Tutorials or educational content
- General AI discussions
- Personal opinions without news
- Marketing or promotional content
"""

    BASE_FILTER_HUMAN = """Analyze this tweet and respond with YES if it contains significant AI news or NO if it doesn't:

{content}"""

    BASE_ANALYSIS_SYSTEM = """You are an AI Industry Analyst synthesizing key developments from Twitter content.

Focus on extracting and summarizing:
- New AI model launches and capabilities
- Major company releases and updates
- Technical breakthroughs and benchmark results
- Developments in AI-powered finance and trading
- Significant research findings

For each important development, structure your response as:

SUMMARY: [Concise description of the key development]
SOURCE: [Twitter username]
LINK: [Tweet URL]

Skip any content about tutorials, courses, or general discussions.
Separate multiple findings with blank lines.
"""

    BASE_ANALYSIS_HUMAN = """Analyze these tweets for key AI industry developments:

{content}"""

def create_twitter_config() -> PlatformConfig:
    """Create Twitter platform configuration with chat prompts"""
    
    # Create filter prompt
    filter_system = SystemMessagePromptTemplate.from_template(PromptTemplates.BASE_FILTER_SYSTEM)
    filter_human = HumanMessagePromptTemplate.from_template(PromptTemplates.BASE_FILTER_HUMAN)
    filter_prompt = ChatPromptTemplate.from_messages([filter_system, filter_human])

    # Create analysis prompt
    analysis_system = SystemMessagePromptTemplate.from_template(PromptTemplates.BASE_ANALYSIS_SYSTEM)
    analysis_human = HumanMessagePromptTemplate.from_template(PromptTemplates.BASE_ANALYSIS_HUMAN)
    analysis_prompt = ChatPromptTemplate.from_messages([analysis_system, analysis_human])

    return PlatformConfig(
        filter_prompt=filter_prompt,
        analysis_prompt=analysis_prompt,
        port=8000,
        recommended_models={
            "filter": "mixtral-8x7b-32768",  # for classification
            "analysis": "mixtral-8x7b-32768"  # for detailed analysis
        }
    )

TWITTER_CONFIG=create_twitter_config()