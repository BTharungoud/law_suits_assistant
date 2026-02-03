import React from 'react';
import { CaseEvaluation } from '../services/api';
import './CaseCard.css';

interface CaseCardProps {
  case: CaseEvaluation;
  onClick: () => void;
}

export const CaseCard: React.FC<CaseCardProps> = ({ case: caseData, onClick }) => {
  const getRankColor = (rank: string) => {
    switch (rank) {
      case 'High':
        return '#22c55e';
      case 'Medium':
        return '#eab308';
      case 'Low':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  // Build comprehensive explanation
  const getExplanation = () => {
    const legalMerit = caseData.legal_merit.score >= 7 ? 'strong' : caseData.legal_merit.score >= 5 ? 'moderate' : 'weak';
    const damages = caseData.damages_potential.score >= 7 ? 'significant' : caseData.damages_potential.score >= 5 ? 'moderate' : 'minimal';
    const complexity = caseData.case_complexity.score >= 7 ? 'very high' : caseData.case_complexity.score >= 5 ? 'moderate' : 'low';
    
    return `This case has ${legalMerit} legal merits, ${damages} damages potential, and ${complexity} complexity. ` +
           `${caseData.priority_rank === 'High' ? 'This case should be prioritized.' : 
             caseData.priority_rank === 'Medium' ? 'This case should be reviewed alongside higher priority cases.' :
             'This case may be deprioritized in favor of cases with stronger merits.'}`;
  };

  return (
    <div className="case-card" onClick={onClick}>
      <div className="case-header">
        <div className="case-title-section">
          <h3>{caseData.case_title}</h3>
          <p className="case-meta">
            <span className="case-id">ID: {caseData.case_id}</span>
            <span className="case-date">{new Date(caseData.created_at).toLocaleDateString()}</span>
          </p>
        </div>
        <div
          className="priority-badge"
          style={{ backgroundColor: getRankColor(caseData.priority_rank) }}
        >
          {caseData.priority_rank}
        </div>
      </div>

      <div className="score-display">
        <div className="score-item">
          <label>Priority Score</label>
          <div className="score-value">{caseData.priority_score.toFixed(1)}</div>
          <span className="score-unit">/10</span>
        </div>
        <div className="score-item">
          <label>Legal Merit</label>
          <div className="score-value">{caseData.legal_merit.score.toFixed(1)}</div>
          <span className="score-unit">/10</span>
        </div>
        <div className="score-item">
          <label>Damages</label>
          <div className="score-value">{caseData.damages_potential.score.toFixed(1)}</div>
          <span className="score-unit">/10</span>
        </div>
        <div className="score-item">
          <label>Complexity</label>
          <div className="score-value">{caseData.case_complexity.score.toFixed(1)}</div>
          <span className="score-unit">/10</span>
        </div>
      </div>

      <div className="case-explanation">
        <p className="explanation-text">{getExplanation()}</p>
      </div>

      <p className="priority-reasoning">
        <strong>Scoring Summary:</strong> {caseData.priority_reasoning}
      </p>

      <div className="case-footer">
        <button className="view-details-btn">View Details →</button>
      </div>
    </div>
  );
};
