import React, { useState, useEffect } from 'react';
import { CaseEvaluation, getAllCases, clearAllCases, deleteCase } from '../services/api';
import { CaseCard } from './CaseCard';
import { CaseDetail } from './CaseDetail';
import './CaseList.css';

interface CaseListProps {
  refreshTrigger: number;
}

export const CaseList: React.FC<CaseListProps> = ({ refreshTrigger }) => {
  const [cases, setCases] = useState<CaseEvaluation[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCase, setSelectedCase] = useState<CaseEvaluation | null>(null);

  useEffect(() => {
    loadCases();
  }, [refreshTrigger]);

  const loadCases = async () => {
    setLoading(true);
    try {
      const response = await getAllCases();
      setCases(response.data.cases);
    } catch (error) {
      console.error('Failed to load cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCase = async (caseId: string) => {
    try {
      await deleteCase(caseId);
      setCases(cases.filter(c => c.case_id !== caseId));
      setSelectedCase(null);
    } catch (error) {
      console.error('Failed to delete case:', error);
    }
  };

  const handleClearAll = async () => {
    if (window.confirm('Are you sure you want to delete all cases?')) {
      try {
        await clearAllCases();
        setCases([]);
        setSelectedCase(null);
      } catch (error) {
        console.error('Failed to clear cases:', error);
      }
    }
  };

  return (
    <div className="case-list-container">
      <div className="list-header">
        <h2>Evaluated Cases</h2>
        <div className="header-actions">
          <span className="case-count">{cases.length} case{cases.length !== 1 ? 's' : ''}</span>
          {cases.length > 0 && (
            <button className="clear-btn" onClick={handleClearAll}>
              Clear All
            </button>
          )}
        </div>
      </div>

      {loading && <div className="loading">Loading cases...</div>}

      {!loading && cases.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <p>No cases evaluated yet</p>
          <small>Upload and evaluate a legal case to see it appear here</small>
        </div>
      )}

      {!loading && cases.length > 0 && (
        <div className="cases-grid">
          {cases.map(caseData => (
            <div key={caseData.case_id} className="case-item">
              <CaseCard
                case={caseData}
                onClick={() => setSelectedCase(caseData)}
              />
              <button
                className="delete-case-btn"
                onClick={() => handleDeleteCase(caseData.case_id)}
                title="Delete case"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}

      {selectedCase && (
        <CaseDetail
          case={selectedCase}
          onClose={() => setSelectedCase(null)}
        />
      )}
    </div>
  );
};
