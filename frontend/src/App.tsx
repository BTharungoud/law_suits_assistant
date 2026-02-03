import React, { useState } from 'react';
import { CaseUpload } from './components/CaseUpload';
import { BatchUpload } from './components/BatchUpload';
import { CaseList } from './components/CaseList';
import './App.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeTab, setActiveTab] = useState<'upload' | 'batch' | 'list'>('upload');

  const handleEvaluationComplete = () => {
    setRefreshTrigger(prev => prev + 1);
    setActiveTab('list');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <h1>⚖️ Law Assistant</h1>
            <p>AI-Powered Legal Case Prioritization</p>
          </div>
        </div>
      </header>

      <div className="app-tabs">
        <button
          className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📤 Single Case
        </button>
        <button
          className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          📁 Batch Upload
        </button>
        <button
          className={`tab-btn ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          📋 View Cases
        </button>
      </div>

      <main className="app-main">
        {activeTab === 'upload' && (
          <CaseUpload onEvaluationComplete={handleEvaluationComplete} />
        )}
        {activeTab === 'batch' && (
          <BatchUpload onEvaluationComplete={handleEvaluationComplete} />
        )}
        {activeTab === 'list' && (
          <CaseList refreshTrigger={refreshTrigger} />
        )}
      </main>

      <footer className="app-footer">
        <p>
          <strong>⚠️ Disclaimer:</strong> This system provides decision-support analysis only and does NOT constitute legal advice.
          Always consult with qualified attorneys before making case decisions.
        </p>
      </footer>
    </div>
  );
}

export default App;
