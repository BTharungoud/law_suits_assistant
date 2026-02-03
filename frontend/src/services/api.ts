import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export interface CaseMetadata {
  title: string;
  jurisdiction: string;
  case_type: 'Civil' | 'Criminal' | 'Commercial' | 'Arbitration';
  claimed_damages?: number;
}

export interface ScoreExplanation {
  score: number;
  reasoning: string;
  key_factors: string[];
}

export interface CaseEvaluation {
  case_id: string;
  case_title: string;
  legal_merit: ScoreExplanation;
  damages_potential: ScoreExplanation;
  case_complexity: ScoreExplanation;
  priority_score: number;
  priority_rank: 'High' | 'Medium' | 'Low';
  priority_reasoning: string;
  created_at: string;
}

export interface CaseRanking {
  cases: CaseEvaluation[];
  total_cases: number;
}

// Health check
export const healthCheck = async () => {
  return api.get('/health');
};

// Evaluate case from file
export const evaluateCaseFromFile = async (
  file: File,
  metadata: CaseMetadata
) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);
  formData.append('jurisdiction', metadata.jurisdiction);
  formData.append('case_type', metadata.case_type);
  if (metadata.claimed_damages) {
    formData.append('claimed_damages', String(metadata.claimed_damages));
  }

  return api.post<CaseEvaluation>('/evaluate-from-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Evaluate case from text
export const evaluateCaseFromText = async (
  caseText: string,
  metadata: CaseMetadata
) => {
  const formData = new FormData();
  formData.append('title', metadata.title);
  formData.append('jurisdiction', metadata.jurisdiction);
  formData.append('case_type', metadata.case_type);
  formData.append('case_text', caseText);
  if (metadata.claimed_damages) {
    formData.append('claimed_damages', String(metadata.claimed_damages));
  }

  return api.post<CaseEvaluation>('/evaluate-text', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Evaluate multiple cases in parallel (batch upload)
export const evaluateCasesBatch = async (
  files: File[],
  metadataList: CaseMetadata[],
  onProgress?: (progress: { completed: number; total: number; caseName: string }) => void
) => {
  if (files.length === 0) {
    throw new Error('No files provided');
  }
  if (files.length !== metadataList.length) {
    throw new Error('Number of files must match number of metadata entries');
  }

  const formData = new FormData();
  
  // Append all files
  files.forEach(file => {
    formData.append('files', file);
  });

  // Append metadata arrays as JSON
  formData.append('titles', JSON.stringify(metadataList.map(m => m.title)));
  formData.append('jurisdictions', JSON.stringify(metadataList.map(m => m.jurisdiction)));
  formData.append('case_types', JSON.stringify(metadataList.map(m => m.case_type)));
  formData.append('claimed_damages_list', JSON.stringify(
    metadataList.map(m => m.claimed_damages || null)
  ));

  return api.post<CaseRanking & { errors?: Array<{ index: number; file: string; error: string }> }>(
    '/evaluate-batch',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  );
};

// Get all cases
export const getAllCases = async () => {
  return api.get<CaseRanking>('/cases');
};

// Get specific case
export const getCaseById = async (caseId: string) => {
  return api.get<CaseEvaluation>(`/cases/${caseId}`);
};

// Delete case
export const deleteCase = async (caseId: string) => {
  return api.delete(`/cases/${caseId}`);
};

// Clear all cases
export const clearAllCases = async () => {
  return api.delete('/cases');
};

// Get disclaimer
export const getDisclaimer = async () => {
  return api.get<{ disclaimer: string }>('/disclaimer');
};

export default api;
