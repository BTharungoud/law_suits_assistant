"""
Case evaluation orchestration service.
Coordinates file parsing, LLM evaluation, and scoring logic.
"""

import uuid
import hashlib
import json
import os
import re
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
        # Simple in-memory cache to ensure repeat evaluations for identical inputs are deterministic
        # Keyed by sha256(case_text + canonicalized metadata)
        self._cache: Dict[str, CaseEvaluation] = {}
        self._cache_raw: Dict[str, Dict[str, Any]] = {}

        # Persistent cache file (kept in backend/.cache)
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cache_dir = os.path.join(base, '.cache')
        os.makedirs(cache_dir, exist_ok=True)
        self._cache_path = os.path.join(cache_dir, 'eval_cache.json')

        # Try to load existing cache
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, 'r', encoding='utf-8') as cf:
                    raw = json.load(cf)
                for k, v in raw.items():
                    try:
                        # Reconstruct model from saved raw data
                        model = CaseEvaluation.model_validate(v)
                        self._cache[k] = model
                        self._cache_raw[k] = v
                    except Exception:
                        # Skip entries that cannot be validated
                        continue
            except Exception:
                # Non-fatal: if cache is corrupt, ignore
                self._cache = {}
                self._cache_raw = {}
    
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
        # Prepare metadata dict and deterministic case id based on content to avoid inconsistent re-evaluations
        metadata_dict = metadata.model_dump()
        meta_json = json.dumps(metadata_dict, sort_keys=True, ensure_ascii=False)
        digest_source = (case_text or '') + meta_json
        digest = hashlib.sha256(digest_source.encode('utf-8')).hexdigest()
        cache_key = digest

        # If we've already evaluated this exact input, return cached result
        if cache_key in self._cache:
            return self._cache[cache_key]

        case_id = digest[:8]
        
        # Call LLM for evaluation
        llm_response = await self.llm_provider.evaluate_case(case_text, metadata_dict)
        
        # Extract scores from LLM response
        legal_merit_data = llm_response.get("legal_merit", {})
        damages_data = llm_response.get("damages_potential", {})
        complexity_data = llm_response.get("case_complexity", {})

        # Normalization helpers: ensure key_factors are lists of short strings
        def _normalize_key_factors(value):
            if value is None:
                return []
            # If already a list, ensure items are strings
            if isinstance(value, list):
                return [str(v).strip() for v in value if v is not None and str(v).strip()]
            # If it's a dict, try to pull a 'key_factors' key
            if isinstance(value, dict):
                return _normalize_key_factors(value.get('key_factors'))
            # If it's a string, split on newlines or bullet markers
            if isinstance(value, str):
                s = value.strip()
                # Common bullet separators
                parts = []
                if '\n' in s:
                    parts = [p.strip(" \t\-\u2022") for p in s.split('\n') if p.strip()]
                elif ';' in s:
                    parts = [p.strip() for p in s.split(';') if p.strip()]
                elif '•' in s:
                    parts = [p.strip() for p in s.split('•') if p.strip()]
                else:
                    # Fallback: split into short sentences (by period)
                    parts = [p.strip() for p in re.split(r'(?<=[\.\?\!])\s+', s) if p.strip()]

                # Keep only shortish factors (<= 200 chars)
                factors = [p for p in parts if len(p) > 0 and len(p) <= 200]
                # If none found, return the whole string as one factor (trimmed)
                return factors if factors else ([s] if s else [])

        # If key_factors are missing, try to extract top 3 short phrases from reasoning
        def _ensure_factors(data):
            reasoning = data.get('reasoning', '') if isinstance(data, dict) else ''
            raw_factors = data.get('key_factors') if isinstance(data, dict) else None
            normalized = _normalize_key_factors(raw_factors)
            if normalized:
                return normalized
            # Try to extract from reasoning: split into sentences and take first 3
            if isinstance(reasoning, str) and reasoning.strip():
                sents = [p.strip() for p in re.split(r'(?<=[\.\?\!])\s+', reasoning) if p.strip()]
                return sents[:3]
            return []
        
        # Build score objects
        legal_merit = ScoreExplanation(
            score=float(legal_merit_data.get("score", 5)),
            reasoning=legal_merit_data.get("reasoning", "Unable to determine"),
            key_factors=_ensure_factors(legal_merit_data)
        )
        
        damages_potential = ScoreExplanation(
            score=float(damages_data.get("score", 5)),
            reasoning=damages_data.get("reasoning", "Unable to determine"),
            key_factors=_ensure_factors(damages_data)
        )
        
        case_complexity = ScoreExplanation(
            score=float(complexity_data.get("score", 5)),
            reasoning=complexity_data.get("reasoning", "Unable to determine"),
            key_factors=_ensure_factors(complexity_data)
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
        # Store in evaluator cache so repeated requests with same content are deterministic
        self._cache[cache_key] = evaluation

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
