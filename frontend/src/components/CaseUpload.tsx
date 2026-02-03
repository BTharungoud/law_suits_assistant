import React, { useState } from 'react';
import { CaseMetadata, evaluateCaseFromFile, evaluateCaseFromText } from '../services/api';
import './CaseUpload.css';

interface CaseUploadProps {
  onEvaluationComplete: () => void;
}

export const CaseUpload: React.FC<CaseUploadProps> = ({ onEvaluationComplete }) => {
  const [uploadMode, setUploadMode] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [caseText, setCaseText] = useState('');
  const [metadata, setMetadata] = useState<CaseMetadata>({
    title: '',
    jurisdiction: '',
    case_type: 'Civil',
    claimed_damages: undefined
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setMetadata(prev => ({
      ...prev,
      [name]: name === 'claimed_damages' ? (value ? parseFloat(value) : undefined) : value
    }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      
      if (!validTypes.includes(selectedFile.type)) {
        setError('Please upload a PDF, DOCX, or TXT file');
        return;
      }
      
      setFile(selectedFile);
      setError(null);
      setSuccess(`✅ File selected: ${selectedFile.name}`);
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCaseText(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!metadata.title || !metadata.jurisdiction || !metadata.case_type) {
      setError('Please fill in all required fields');
      return;
    }

    if (uploadMode === 'file' && !file) {
      setError('Please select a file');
      return;
    }

    if (uploadMode === 'text' && !caseText.trim()) {
      setError('Please enter case text');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (uploadMode === 'file' && file) {
        setSuccess(`📤 Uploading ${file.name}...`);
        await evaluateCaseFromFile(file, metadata);
        setSuccess('✅ Case evaluated successfully! Redirecting to results...');
      } else {
        setSuccess('📤 Processing case text...');
        await evaluateCaseFromText(caseText, metadata);
        setSuccess('✅ Case evaluated successfully! Redirecting to results...');
      }

      // Reset form after brief delay
      setTimeout(() => {
        setFile(null);
        setCaseText('');
        setMetadata({
          title: '',
          jurisdiction: '',
          case_type: 'Civil',
          claimed_damages: undefined
        });
        setSuccess(null);
        onEvaluationComplete();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Evaluation failed. Please check your API configuration and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="case-upload-container">
      <div className="upload-header">
        <h2>Evaluate Legal Case</h2>
        <p>Upload a case file or enter case details for AI-powered prioritization</p>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        {error && <div className="error-alert">❌ {error}</div>}
        {success && <div className="success-alert">{success}</div>}

        <div className="mode-selector">
          <button
            type="button"
            className={`mode-btn ${uploadMode === 'file' ? 'active' : ''}`}
            onClick={() => { setUploadMode('file'); setError(null); }}
          >
            📄 Upload File
          </button>
          <button
            type="button"
            className={`mode-btn ${uploadMode === 'text' ? 'active' : ''}`}
            onClick={() => { setUploadMode('text'); setError(null); }}
          >
            ✏️ Enter Text
          </button>
        </div>

        <div className="form-section">
          <h3>Case Information</h3>
          
          <div className="form-group">
            <label htmlFor="title">Case Title *</label>
            <input
              id="title"
              type="text"
              name="title"
              value={metadata.title}
              onChange={handleMetadataChange}
              placeholder="e.g., Smith v. Jones"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="jurisdiction">Jurisdiction *</label>
              <input
                id="jurisdiction"
                type="text"
                name="jurisdiction"
                value={metadata.jurisdiction}
                onChange={handleMetadataChange}
                placeholder="e.g., California"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="case_type">Case Type *</label>
              <select
                id="case_type"
                name="case_type"
                value={metadata.case_type}
                onChange={handleMetadataChange}
              >
                <option value="Civil">Civil</option>
                <option value="Criminal">Criminal</option>
                <option value="Commercial">Commercial</option>
                <option value="Arbitration">Arbitration</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="claimed_damages">Claimed Damages (USD)</label>
            <input
              id="claimed_damages"
              type="number"
              name="claimed_damages"
              value={metadata.claimed_damages || ''}
              onChange={handleMetadataChange}
              placeholder="e.g., 500000"
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Case Details</h3>

          {uploadMode === 'file' ? (
            <div className="file-upload">
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="file-input"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt"
                />
                <label htmlFor="file-input" className="file-label">
                  <span className="file-icon">📎</span>
                  <span>Choose file (PDF, DOCX, or TXT)</span>
                </label>
              </div>
              {file && (
                <p className="file-name">
                  {loading ? (
                    <>
                      <span className="loader"></span>
                      Processing: {file.name}
                    </>
                  ) : (
                    <>✅ Selected: {file.name}</>
                  )}
                </p>
              )}
            </div>
          ) : (
            <div className="text-input">
              <textarea
                value={caseText}
                onChange={handleTextChange}
                placeholder="Enter case details, facts, arguments, and relevant information..."
                rows={10}
              />
            </div>
          )}
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Evaluating...' : 'Evaluate Case'}
        </button>
      </form>

      <div className="disclaimer">
        <strong>Disclaimer:</strong> This evaluation is for decision-support purposes only and does NOT constitute legal advice.
        Please consult with qualified attorneys before making case decisions.
      </div>
    </div>
  );
};
