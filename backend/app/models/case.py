"""
Data models for legal cases and evaluations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CaseMetadata(BaseModel):
    """Metadata for a legal case."""
    
    title: str = Field(..., description="Case title")
    jurisdiction: str = Field(..., description="Jurisdiction (e.g., California, NY, Federal)")
    case_type: str = Field(..., description="Case type: Civil, Criminal, Commercial, or Arbitration")
    claimed_damages: Optional[float] = Field(None, description="Claimed damages amount in USD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Smith v. Jones",
                "jurisdiction": "California",
                "case_type": "Civil",
                "claimed_damages": 500000
            }
        }


class CaseInput(BaseModel):
    """Input for case evaluation (metadata + optional file)."""
    
    metadata: CaseMetadata
    file_content: Optional[str] = Field(None, description="Extracted text from case file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "title": "Smith v. Jones",
                    "jurisdiction": "California",
                    "case_type": "Civil",
                    "claimed_damages": 500000
                },
                "file_content": "Contract details and case facts..."
            }
        }


class ScoreExplanation(BaseModel):
    """Explanation for a scoring component."""
    
    score: float = Field(..., ge=0, le=10, description="Score 0-10")
    reasoning: str = Field(..., description="Explanation of scoring")
    key_factors: List[str] = Field(default_factory=list, description="Key factors affecting score")


class CaseEvaluation(BaseModel):
    """Complete case evaluation with scores and reasoning."""
    
    case_id: str = Field(..., description="Unique case identifier")
    case_title: str = Field(..., description="Case title")
    
    legal_merit: ScoreExplanation = Field(..., description="Legal merit evaluation (0-10)")
    damages_potential: ScoreExplanation = Field(..., description="Damages potential evaluation (0-10)")
    case_complexity: ScoreExplanation = Field(..., description="Case complexity evaluation (0-10)")
    
    priority_score: float = Field(..., ge=0, le=10, description="Final priority score (0-10)")
    priority_rank: str = Field(..., description="Rank: High, Medium, or Low")
    
    # Formula: (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
    priority_reasoning: str = Field(..., description="Explanation of final priority score")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_001",
                "case_title": "Smith v. Jones",
                "legal_merit": {
                    "score": 7.5,
                    "reasoning": "Strong contractual evidence with clear breach",
                    "key_factors": ["Clear contract terms", "Documented breach", "Low dismissal risk"]
                },
                "damages_potential": {
                    "score": 8.0,
                    "reasoning": "High claimed damages with solvent defendant",
                    "key_factors": ["$500K claimed", "Defendant solvent", "Enforceable judgment"]
                },
                "case_complexity": {
                    "score": 3.0,
                    "reasoning": "Straightforward contract dispute",
                    "key_factors": ["Single contract", "Two parties", "Clear liability"]
                },
                "priority_score": 7.8,
                "priority_rank": "High",
                "priority_reasoning": "Strong legal merits and high damages potential with manageable complexity"
            }
        }


class CaseRanking(BaseModel):
    """Ranked list of cases."""
    
    cases: List[CaseEvaluation] = Field(..., description="Cases ranked by priority score (descending)")
    total_cases: int = Field(..., description="Total number of cases evaluated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cases": [],
                "total_cases": 0
            }
        }


class HealthCheck(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Status: ok or error")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
