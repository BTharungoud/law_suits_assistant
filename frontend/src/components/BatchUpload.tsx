import React, { useState } from 'react';
import { evaluateCasesBatch } from '../services/api';
import './BatchUpload.css';

interface BatchUploadProps {
  onEvaluationComplete: () => void;
}

interface BatchCase {
  file: File;
  title: string;
  jurisdiction: string;
  case_type: 'Civil' | 'Criminal' | 'Commercial' | 'Arbitration';
  claimed_damages?: number;
}

export const BatchUpload: React.FC<BatchUploadProps> = ({ onEvaluationComplete }) => {
  const [cases, setCases] = useState<BatchCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ completed: number; total: number } | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files) {
      const newFiles = Array.from(e.dataTransfer.files);
      validateAndAddFiles(newFiles);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      validateAndAddFiles(newFiles);
    }
  };

  const validateAndAddFiles = (newFiles: File[]) => {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const validFiles = newFiles.filter(file => {
      if (!validTypes.includes(file.type)) {
        setError(`Skipped ${file.name}: invalid type (only PDF, DOCX, TXT)`);
        return false;
      }
      return true;
    });

    const newCases = validFiles.map(file => ({
      file,
      title: file.name.replace(/\.[^/.]+$/, ''),
      jurisdiction: 'California',
      case_type: 'Civil' as const,
      claimed_damages: undefined
    }));

    setCases(prev => [...prev, ...newCases]);
    setError(null);
  };

  const updateCase = (index: number, updates: Partial<BatchCase>) => {
    setCases(prev => [
      ...prev.slice(0, index),
      { ...prev[index], ...updates },
      ...prev.slice(index + 1)
    ]);
  };

  const removeCase = (index: number) => {
    setCases(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (cases.length === 0) {
      setError('Please add at least one case');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress({ completed: 0, total: cases.length });

    try {
      const files = cases.map(c => c.file);
      const metadataList = cases.map(c => ({
        title: c.title,
        jurisdiction: c.jurisdiction,
        case_type: c.case_type,
        claimed_damages: c.claimed_damages
      }));

      await evaluateCasesBatch(files, metadataList, (prog) => {
        setProgress(prog);
      });

      // Reset form
      setCases([]);
      onEvaluationComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Batch evaluation failed');
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  return (
    <div className="batch-upload-container">
      <div className="upload-header">
        <h2>Batch Upload Cases</h2>
        <p>Upload multiple case files at once for parallel evaluation</p>
      </div>

      {error && <div className="error-alert">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="batch-files"
            multiple
            onChange={handleFileInput}
            accept=".pdf,.docx,.txt"
            style={{ display: 'none' }}
          />
          <label htmlFor="batch-files" className="drop-label">
            <div className="drop-icon">📁</div>
            <div className="drop-text">
              <strong>Drag files here or click to browse</strong>
              <p>Supports PDF, DOCX, TXT (multiple files)</p>
            </div>
          </label>
        </div>

        {cases.length > 0 && (
          <div className="cases-table">
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Case Title</th>
                  <th>Jurisdiction</th>
                  <th>Type</th>
                  <th>Damages ($)</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((caseItem, idx) => (
                  <tr key={idx}>
                    <td className="file-name">{caseItem.file.name}</td>
                    <td>
                      <input
                        type="text"
                        value={caseItem.title}
                        onChange={(e) => updateCase(idx, { title: e.target.value })}
                        placeholder="Case title"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={caseItem.jurisdiction}
                        onChange={(e) => updateCase(idx, { jurisdiction: e.target.value })}
                        placeholder="Jurisdiction"
                      />
                    </td>
                    <td>
                      <select
                        value={caseItem.case_type}
                        onChange={(e) => updateCase(idx, { case_type: e.target.value as any })}
                      >
                        <option value="Civil">Civil</option>
                        <option value="Criminal">Criminal</option>
                        <option value="Commercial">Commercial</option>
                        <option value="Arbitration">Arbitration</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type="number"
                        value={caseItem.claimed_damages || ''}
                        onChange={(e) => updateCase(idx, { claimed_damages: e.target.value ? parseFloat(e.target.value) : undefined })}
                        placeholder="Amount"
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={() => removeCase(idx)}
                        disabled={loading}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {progress && (
              <div className="progress-section">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${(progress.completed / progress.total) * 100}%` }}
                  />
                </div>
                <p className="progress-text">
                  Evaluating: {progress.completed} / {progress.total} cases
                </p>
              </div>
            )}

            <button type="submit" className="submit-btn" disabled={loading || cases.length === 0}>
              {loading ? `Evaluating ${cases.length} cases...` : `Evaluate ${cases.length} Case${cases.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        )}
      </form>

      <div className="disclaimer">
        <strong>⚠️ Disclaimer:</strong> This evaluation is for decision-support purposes only and does NOT constitute legal advice.
        Please consult with qualified attorneys before making case decisions.
      </div>
    </div>
  );
};
