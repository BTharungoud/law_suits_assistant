import React, { useState } from 'react';
import { CaseEvaluation } from '../services/api';
import './CaseDetail.css';

interface CaseDetailProps {
  case: CaseEvaluation;
  onClose: () => void;
}

export const CaseDetail: React.FC<CaseDetailProps> = ({ case: caseData, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'legal_merit' | 'damages' | 'complexity'>('overview');

  return (
    <div className="case-detail-overlay" onClick={onClose}>
      <div className="case-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{caseData.case_title}</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'legal_merit' ? 'active' : ''}`}
            onClick={() => setActiveTab('legal_merit')}
          >
            Legal Merit
          </button>
          <button
            className={`tab ${activeTab === 'damages' ? 'active' : ''}`}
            onClick={() => setActiveTab('damages')}
          >
            Damages
          </button>
          <button
            className={`tab ${activeTab === 'complexity' ? 'active' : ''}`}
            onClick={() => setActiveTab('complexity')}
          >
            Complexity
          </button>
        </div>

        <div className="modal-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="score-grid">
                <div className="score-box">
                  <label>Priority Score</label>
                  <div className="large-score">{caseData.priority_score.toFixed(1)}</div>
                  <span className="rank-badge">{caseData.priority_rank}</span>
                </div>
                <div className="score-box">
                  <label>Legal Merit</label>
                  <div className="large-score">{caseData.legal_merit.score.toFixed(1)}</div>
                </div>
                <div className="score-box">
                  <label>Damages Potential</label>
                  <div className="large-score">{caseData.damages_potential.score.toFixed(1)}</div>
                </div>
                <div className="score-box">
                  <label>Complexity</label>
                  <div className="large-score">{caseData.case_complexity.score.toFixed(1)}</div>
                </div>
              </div>

              <div className="priority-section">
                <h3>Priority Analysis</h3>
                <p className="reasoning">{caseData.priority_reasoning}</p>
                <div className="formula-note">
                  <strong>Calculation:</strong> (Legal Merit × 0.4) + (Damages × 0.4) - (Complexity × 0.2) = {caseData.priority_score.toFixed(2)}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'legal_merit' && (
            <div className="detail-section">
              <h3>Legal Merit Analysis</h3>
              <div className="score-detail">
                <div className="score-number">{caseData.legal_merit.score.toFixed(1)}/10</div>
                <p className="reasoning">{caseData.legal_merit.reasoning}</p>
              </div>
              <div className="factors">
                <h4>Key Factors:</h4>
                <ul>
                  {caseData.legal_merit.key_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'damages' && (
            <div className="detail-section">
              <h3>Damages Potential Analysis</h3>
              <div className="score-detail">
                <div className="score-number">{caseData.damages_potential.score.toFixed(1)}/10</div>
                <p className="reasoning">{caseData.damages_potential.reasoning}</p>
              </div>
              <div className="factors">
                <h4>Key Factors:</h4>
                <ul>
                  {caseData.damages_potential.key_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'complexity' && (
            <div className="detail-section">
              <h3>Case Complexity Analysis</h3>
              <div className="score-detail">
                <div className="score-number">{caseData.case_complexity.score.toFixed(1)}/10</div>
                <p className="reasoning">{caseData.case_complexity.reasoning}</p>
              </div>
              <div className="factors">
                <h4>Key Factors:</h4>
                <ul>
                  {caseData.case_complexity.key_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <small>Case ID: {caseData.case_id}</small>
          <small>Created: {new Date(caseData.created_at).toLocaleString()}</small>
        </div>
      </div>
    </div>
  );
};
