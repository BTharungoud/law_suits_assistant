"""
LLM adapter for dual provider support (OpenAI and Google Gemini).
Provides a unified interface to swap between providers via .env configuration.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a legal case and return structured scoring data."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        from openai import AsyncOpenAI
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate case using OpenAI GPT-4.
        
        Args:
            case_text: Extracted case document text
            metadata: Case metadata (title, jurisdiction, type, claimed damages)
            
        Returns:
            Dictionary with legal_merit, damages_potential, complexity scores and reasoning
        """
        prompt = self._build_prompt(case_text, metadata)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal case analyst. Evaluate cases on legal merit, damages potential, and complexity. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError:
            # Fallback: extract JSON from response if wrapped in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Failed to parse OpenAI response as JSON")
    
    def _build_prompt(self, case_text: str, metadata: Dict[str, Any]) -> str:
        """Build evaluation prompt for OpenAI."""
        return f"""
Analyze the following legal case and provide a structured evaluation.

CASE METADATA:
- Title: {metadata.get('title', 'N/A')}
- Jurisdiction: {metadata.get('jurisdiction', 'N/A')}
- Case Type: {metadata.get('case_type', 'N/A')}
- Claimed Damages: ${metadata.get('claimed_damages', 'N/A')}

CASE DOCUMENT:
{case_text[:5000]}

Evaluate this case on three dimensions (0-10 scale each) and respond ONLY with valid JSON:

{{
  "legal_merit": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "damages_potential": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "case_complexity": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }}
}}

SCORING GUIDELINES:

Legal Merit (0-10):
- 9-10: Strong case with clear legal basis, solid evidence, low dismissal risk
- 7-8: Good case with reasonable legal grounds and supportive evidence
- 5-6: Moderate case with arguable legal positions
- 3-4: Weak case with significant legal or evidentiary challenges
- 0-2: Very weak case with major legal flaws or missing evidence

Damages Potential (0-10):
- 9-10: High damages ($1M+), solvent defendant, easy enforcement
- 7-8: Substantial damages ($500K-$1M), likely collectible
- 5-6: Moderate damages ($100K-$500K), reasonable recovery probability
- 3-4: Low damages (<$100K), difficult enforcement
- 0-2: Minimal damages or uncollectible defendant

Case Complexity (0-10):
- 0-2: Simple case, straightforward facts, 6-12 month timeline
- 3-4: Moderate case, standard procedures, 12-18 month timeline
- 5-6: Complex case, multiple parties/issues, 18-24 month timeline
- 7-8: Very complex case, novel issues, 24+ month timeline
- 9-10: Extremely complex case, high procedural difficulty, uncertain timeline

CRITICAL: Respond ONLY with valid JSON - no other text.
"""


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self):
        """Initialize Gemini provider."""
        import google.generativeai as genai
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
    
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate case using Google Gemini.
        
        Args:
            case_text: Extracted case document text
            metadata: Case metadata (title, jurisdiction, type, claimed damages)
            
        Returns:
            Dictionary with legal_merit, damages_potential, complexity scores and reasoning
        """
        prompt = self._build_prompt(case_text, metadata)
        
        try:
            # Gemini API is synchronous; wrap in async context
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0,
                    "top_p": 1,
                    "max_output_tokens": 2048,
                }
            )
            
            response_text = response.text
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError:
            # Fallback: extract JSON from response if wrapped in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Failed to parse Gemini response as JSON")
    
    def _build_prompt(self, case_text: str, metadata: Dict[str, Any]) -> str:
        """Build evaluation prompt (same for both providers)."""
        return f"""
Analyze the following legal case and provide a structured evaluation.

CASE METADATA:
- Title: {metadata.get('title', 'N/A')}
- Jurisdiction: {metadata.get('jurisdiction', 'N/A')}
- Case Type: {metadata.get('case_type', 'N/A')}
- Claimed Damages: ${metadata.get('claimed_damages', 'N/A')}

CASE DOCUMENT:
{case_text[:5000]}  # Limit to first 5000 chars to avoid token overflow

Evaluate this case on three dimensions (0-10 scale each) and respond ONLY with valid JSON:

{{
  "legal_merit": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "damages_potential": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "case_complexity": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }}
}}

SCORING GUIDELINES:

Legal Merit (0-10):
- 9-10: Strong case with clear legal basis, solid evidence, low dismissal risk
- 7-8: Good case with reasonable legal grounds and supportive evidence
- 5-6: Moderate case with arguable legal positions
- 3-4: Weak case with significant legal or evidentiary challenges
- 0-2: Very weak case with major legal flaws or missing evidence

Damages Potential (0-10):
- 9-10: High damages ($1M+), solvent defendant, easy enforcement
- 7-8: Substantial damages ($500K-$1M), likely collectible
- 5-6: Moderate damages ($100K-$500K), reasonable recovery probability
- 3-4: Low damages (<$100K), difficult enforcement
- 0-2: Minimal damages or uncollectible defendant

Case Complexity (0-10):
- 0-2: Simple case, straightforward facts, 6-12 month timeline
- 3-4: Moderate case, standard procedures, 12-18 month timeline
- 5-6: Complex case, multiple parties/issues, 18-24 month timeline
- 7-8: Very complex case, novel issues, 24+ month timeline
- 9-10: Extremely complex case, high procedural difficulty, uncertain timeline

CRITICAL INSTRUCTIONS:
1. Be CAUTIOUS and FACTUAL - only score based on case facts presented
2. If information is missing, state assumptions explicitly in reasoning
3. Never hallucinate legal precedents or make legal predictions
4. Focus on extractable factors from the provided text
5. Respond ONLY with valid JSON - no other text
"""


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.
    
    Returns:
        LLMProvider instance based on LLM_PROVIDER setting
        
    Raises:
        ValueError: If provider is not recognized
    """
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Choose 'openai' or 'gemini'")
