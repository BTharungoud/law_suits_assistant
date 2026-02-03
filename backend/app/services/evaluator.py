"""
Case evaluation orchestration service.
Coordinates file parsing, LLM evaluation, and scoring logic.
"""

import uuid
from typing import Dict, Any, Optional
from app.models.case import CaseMetadata, CaseEvaluation, ScoreExplanation
from app.services.llm_adapter import get_llm_provider
from app.utils.parsers import extract_text_from_file
from datetime import datetime


class CaseEvaluator:
    """Orchestrates case evaluation pipeline."""
    
    # DISCLAIMER for all evaluations
    LEGAL_DISCLAIMER = (
        "This evaluation is provided for decision-support purposes only and does NOT constitute legal advice. "
        "It is based on AI analysis of provided documents and should not be relied upon as a substitute for "
        "professional legal counsel. Please consult with qualified attorneys before making case decisions."
    )
    
    def __init__(self):
        """Initialize evaluator."""
        self.llm_provider = get_llm_provider()
    
    async def evaluate_case_from_file(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: CaseMetadata
    ) -> CaseEvaluation:
        """
        Evaluate a case from an uploaded file.
        
        Args:
            file_bytes: File contents as bytes
            filename: Original filename (for parsing)
            metadata: Case metadata
            
        Returns:
            CaseEvaluation with scores and reasoning
        """
        # Extract text from file
        case_text = extract_text_from_file(file_bytes, filename)
        
        # Evaluate using LLM
        return await self.evaluate_case_from_text(case_text, metadata)
    
    async def evaluate_case_from_text(
        self,
        case_text: str,
        metadata: CaseMetadata
    ) -> CaseEvaluation:
        """
        Evaluate a case from raw text.
        
        Args:
            case_text: Case document text
            metadata: Case metadata
            
        Returns:
            CaseEvaluation with scores and reasoning
        """
        case_id = str(uuid.uuid4())[:8]
        
        # Call LLM for evaluation
        metadata_dict = metadata.model_dump()
        llm_response = await self.llm_provider.evaluate_case(case_text, metadata_dict)
        
        # Extract scores from LLM response
        legal_merit_data = llm_response.get("legal_merit", {})
        damages_data = llm_response.get("damages_potential", {})
        complexity_data = llm_response.get("case_complexity", {})
        
        # Build score objects
        legal_merit = ScoreExplanation(
            score=float(legal_merit_data.get("score", 5)),
            reasoning=legal_merit_data.get("reasoning", "Unable to determine"),
            key_factors=legal_merit_data.get("key_factors", [])
        )
        
        damages_potential = ScoreExplanation(
            score=float(damages_data.get("score", 5)),
            reasoning=damages_data.get("reasoning", "Unable to determine"),
            key_factors=damages_data.get("key_factors", [])
        )
        
        case_complexity = ScoreExplanation(
            score=float(complexity_data.get("score", 5)),
            reasoning=complexity_data.get("reasoning", "Unable to determine"),
            key_factors=complexity_data.get("key_factors", [])
        )
        
        # Compute priority score using formula
        # priority_score = (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
        priority_score = (
            (legal_merit.score * 0.4) +
            (damages_potential.score * 0.4) -
            (case_complexity.score * 0.2)
        )
        
        # Clamp to 0-10 range
        priority_score = max(0, min(10, priority_score))
        
        # Determine priority rank
        if priority_score >= 7:
            priority_rank = "High"
        elif priority_score >= 4:
            priority_rank = "Medium"
        else:
            priority_rank = "Low"
        
        # Build priority reasoning
        priority_reasoning = self._build_priority_reasoning(
            legal_merit.score,
            damages_potential.score,
            case_complexity.score,
            priority_score
        )
        
        # Create evaluation object
        evaluation = CaseEvaluation(
            case_id=case_id,
            case_title=metadata.title,
            legal_merit=legal_merit,
            damages_potential=damages_potential,
            case_complexity=case_complexity,
            priority_score=priority_score,
            priority_rank=priority_rank,
            priority_reasoning=priority_reasoning,
            created_at=datetime.utcnow()
        )
        
        return evaluation
    
    def _build_priority_reasoning(
        self,
        legal_merit: float,
        damages: float,
        complexity: float,
        priority_score: float
    ) -> str:
        """
        Build human-readable explanation for priority score.
        
        Args:
            legal_merit: Legal merit score (0-10)
            damages: Damages potential score (0-10)
            complexity: Case complexity score (0-10)
            priority_score: Final priority score (0-10)
            
        Returns:
            Explanation string
        """
        merit_desc = "strong" if legal_merit >= 7 else ("moderate" if legal_merit >= 4 else "weak")
        damages_desc = "high" if damages >= 7 else ("moderate" if damages >= 4 else "low")
        complexity_desc = "manageable" if complexity <= 4 else ("significant" if complexity <= 7 else "very high")
        
        reason = f"Case has {merit_desc} legal merits (score: {legal_merit:.1f}) and {damages_desc} damages potential (score: {damages:.1f}). "
        reason += f"Case complexity is {complexity_desc} (score: {complexity:.1f}). "
        reason += f"Overall priority score: {priority_score:.1f}/10."
        
        return reason
    
    @staticmethod
    def get_disclaimer() -> str:
        """Get the legal disclaimer for all evaluations."""
        return CaseEvaluator.LEGAL_DISCLAIMER
