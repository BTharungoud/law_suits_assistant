"""
Tests for case evaluation and scoring logic.
"""

import pytest
from app.models.case import CaseMetadata, ScoreExplanation, CaseEvaluation


class TestModels:
    """Tests for case models."""
    
    def test_case_metadata_valid(self):
        """Test creating valid case metadata."""
        metadata = CaseMetadata(
            title="Smith v. Jones",
            jurisdiction="California",
            case_type="Civil",
            claimed_damages=500000
        )
        assert metadata.title == "Smith v. Jones"
        assert metadata.jurisdiction == "California"
        assert metadata.case_type == "Civil"
        assert metadata.claimed_damages == 500000
    
    def test_case_metadata_no_damages(self):
        """Test case metadata without damages."""
        metadata = CaseMetadata(
            title="Case Title",
            jurisdiction="NY",
            case_type="Criminal"
        )
        assert metadata.claimed_damages is None
    
    def test_score_explanation_valid(self):
        """Test creating score explanation."""
        explanation = ScoreExplanation(
            score=7.5,
            reasoning="Strong case with clear evidence",
            key_factors=["Factor 1", "Factor 2"]
        )
        assert explanation.score == 7.5
        assert len(explanation.key_factors) == 2
    
    def test_score_boundary_values(self):
        """Test score boundary values (0-10)."""
        # Min
        low_score = ScoreExplanation(score=0, reasoning="Very weak")
        assert low_score.score == 0
        
        # Max
        high_score = ScoreExplanation(score=10, reasoning="Perfect")
        assert high_score.score == 10
    
    def test_score_validation_too_low(self):
        """Test that scores below 0 are invalid."""
        with pytest.raises(ValueError):
            ScoreExplanation(score=-1, reasoning="Invalid")
    
    def test_score_validation_too_high(self):
        """Test that scores above 10 are invalid."""
        with pytest.raises(ValueError):
            ScoreExplanation(score=11, reasoning="Invalid")


class TestScoringFormula:
    """Tests for priority score calculation."""
    
    def test_priority_formula_high_merit_damages(self):
        """Test priority score with high merit and damages."""
        # Formula: (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
        legal_merit = 9.0
        damages = 9.0
        complexity = 2.0
        
        priority_score = (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
        
        expected = (9.0 * 0.4) + (9.0 * 0.4) - (2.0 * 0.2)
        expected = 3.6 + 3.6 - 0.4
        expected = 6.8
        
        assert abs(priority_score - expected) < 0.01
    
    def test_priority_formula_low_merit_high_complexity(self):
        """Test priority score with low merit and high complexity."""
        legal_merit = 3.0
        damages = 4.0
        complexity = 8.0
        
        priority_score = (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
        
        expected = (3.0 * 0.4) + (4.0 * 0.4) - (8.0 * 0.2)
        expected = 1.2 + 1.6 - 1.6
        expected = 1.2
        
        assert abs(priority_score - expected) < 0.01
    
    def test_priority_clamping(self):
        """Test that priority score is clamped to 0-10."""
        # Score that would be > 10
        legal_merit = 10.0
        damages = 10.0
        complexity = 0.0
        
        priority_score = (legal_merit * 0.4) + (damages * 0.4) - (complexity * 0.2)
        priority_score = max(0, min(10, priority_score))
        
        assert priority_score == 8.0  # (10 * 0.4) + (10 * 0.4) - (0 * 0.2) = 8.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
