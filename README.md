# Law Assistant

A production-ready AI-powered legal case prioritization system with explainable scoring and ranking.

## Overview

Law Assistant helps lawyers make data-driven decisions about which cases to accept by evaluating cases on three key dimensions:

1. **Legal Merit** (0-10): Strength of case, evidence quality, legal clarity, dismissal risk
2. **Damages Potential** (0-10): Financial value, recovery likelihood, defendant solvency, enforceability
3. **Case Complexity** (0-10): Duration, procedural difficulty, documentation volume, party count

Cases are ranked using a transparent formula:
```
Priority Score = (Legal Merit × 0.4) + (Damages × 0.4) - (Complexity × 0.2)
```

**Higher scores = more attractive cases**

## Features

✅ **Dual LLM Support**: OpenAI GPT-4 or Google Gemini (switchable via `.env`)
✅ **Multiple Input Methods**: File upload (PDF, DOCX, TXT) or direct text entry
✅ **Batch Upload**: Upload 5-100+ cases at once for parallel evaluation
✅ **Real-Time Evaluation**: Instant case analysis and ranking
✅ **Explainable AI**: Detailed reasoning for every score with key factors
✅ **Responsive Web UI**: Modern React dashboard with detailed case views
✅ **Production-Ready**: Clean architecture, comprehensive error handling, Docker support
✅ **Legal Compliance**: Built-in disclaimers, decision-support framing, no legal advice

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- OpenAI or Google Gemini API key

### Option 1: Local Development

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

**Frontend Setup (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

### Option 2: Docker Compose

```bash
cp .env.example .env
# Edit .env with your API keys

docker-compose up
```

Visit: http://localhost:3000

### Option 3: Production Build

```bash
docker build -f Dockerfile.backend -t law-assistant-backend .
docker build -f Dockerfile.frontend -t law-assistant-frontend .

# Run containers
docker run -p 8000:8000 -e OPENAI_API_KEY=xxx law-assistant-backend
docker run -p 3000:3000 law-assistant-frontend
```

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│   (Upload • Metadata • Ranking • Detail Views)          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                       │
│  ┌──────────────┬──────────────┬──────────────────────┐ │
│  │  File Parse  │  LLM Adapter │  Scoring Engine      │ │
│  │  (PDF/DOCX)  │  (OpenAI/    │  (Formula + Logic)   │ │
│  │              │   Gemini)    │                      │ │
│  └──────────────┴──────────────┴──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints

### Health & Info
- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/disclaimer` - Legal disclaimer

### Case Evaluation
- `POST /api/evaluate-from-file` - Upload file (PDF, DOCX, TXT) + metadata
- `POST /api/evaluate-text` - Evaluate text + metadata
- `POST /api/evaluate-batch` - **NEW**: Batch upload multiple files (parallel evaluation)

### Case Management
- `GET /api/cases` - All cases (ranked by priority)
- `GET /api/cases/{case_id}` - Case details
- `DELETE /api/cases/{case_id}` - Delete case
- `DELETE /api/cases` - Clear all cases

### Request Example (Text Evaluation)

```bash
curl -X POST http://localhost:8000/api/evaluate-text \
  -F "title=Smith v. Jones" \
  -F "jurisdiction=California" \
  -F "case_type=Civil" \
  -F "claimed_damages=500000" \
  -F "case_text=<case document text>"
```

### Response Example

```json
{
  "case_id": "a1b2c3d4",
  "case_title": "Smith v. Jones",
  "legal_merit": {
    "score": 7.5,
    "reasoning": "Strong contractual evidence with clear breach",
    "key_factors": ["Clear contract terms", "Documented breach"]
  },
  "damages_potential": {
    "score": 8.0,
    "reasoning": "High claimed damages with solvent defendant",
    "key_factors": ["$500K claimed", "Defendant solvent"]
  },
  "case_complexity": {
    "score": 3.0,
    "reasoning": "Straightforward contract dispute",
    "key_factors": ["Single contract", "Two parties"]
  },
  "priority_score": 7.8,
  "priority_rank": "High",
  "priority_reasoning": "Strong legal merits and high damages potential with manageable complexity",
  "created_at": "2026-02-03T10:30:45.123456"
}
```

## Configuration

`.env` file:
```env
# LLM Selection
LLM_PROVIDER=openai              # or 'gemini'
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True

# Database (future)
DATABASE_URL=sqlite:///./law_assistant.db

# Frontend
FRONTEND_URL=http://localhost:3000
```

## Scoring Guidelines

### Legal Merit (0-10)

| Score | Description |
|-------|-------------|
| 9-10 | Strong case: clear legal basis, solid evidence, low dismissal risk |
| 7-8 | Good case: reasonable legal grounds, supportive evidence |
| 5-6 | Moderate case: arguable legal positions, mixed evidence |
| 3-4 | Weak case: significant challenges, evidentiary gaps |
| 0-2 | Very weak: major legal flaws, insufficient evidence |

### Damages Potential (0-10)

| Score | Description |
|-------|-------------|
| 9-10 | High: $1M+, solvent defendant, easy enforcement |
| 7-8 | Substantial: $500K-$1M, likely collectible |
| 5-6 | Moderate: $100K-$500K, reasonable recovery |
| 3-4 | Low: <$100K, difficult enforcement |
| 0-2 | Minimal: uncollectible defendant |

### Case Complexity (0-10)

| Score | Description |
|-------|-------------|
| 0-2 | Simple: straightforward facts, 6-12 months |
| 3-4 | Moderate: standard procedures, 12-18 months |
| 5-6 | Complex: multiple parties/issues, 18-24 months |
| 7-8 | Very complex: novel issues, 24+ months |
| 9-10 | Extremely complex: high procedural difficulty |

## Security & Compliance

### Privacy
- ✅ No persistent storage by default (ephemeral processing)
- ✅ File contents never logged or stored
- ✅ LLM API calls encrypted (HTTPS)
- ✅ Configurable database for audit trails (optional)

### Legal Compliance
- ✅ Explicit disclaimer on all outputs
- ✅ Framed as decision-support only (not legal advice)
- ✅ No legal conclusions or predictions
- ✅ Factual analysis only
- ✅ States assumptions explicitly
- ✅ Avoids hallucinations

### Data Handling
- ✅ No auth required (internal use assumed)
- ✅ CORS configured for frontend domain
- ✅ Input validation on all endpoints
- ✅ Structured error responses

## Explainability

Every evaluation includes:
1. **Numeric scores** (0-10 for each dimension)
2. **Written reasoning** (why this score was assigned)
3. **Key factors** (list of factors that influenced the score)
4. **Formula transparency** (how priority score is computed)

Example reasoning:
> "Strong contractual evidence with clear breach. The contract clearly specifies obligations, and documented emails show defendant's explicit violation of terms."

## Testing

Run unit tests:
```bash
cd backend
python -m pytest tests/ -v
```

Tests cover:
- File parsing (PDF, DOCX, TXT)
- Scoring logic and formulas
- Data models and validation
- API endpoints (basic)

## Limitations & Disclaimers

⚠️ **This is decision-support software only, NOT legal advice.**

- Analysis based on AI; errors possible
- No replacement for qualified attorneys
- Scores reflect only provided information
- Missing info may skew results
- Not a substitute for due diligence
- Consult lawyers before major decisions

## Roadmap

- [ ] Vector database integration for case similarity search
- [ ] Persistent case history with audit trail
- [ ] User authentication & role-based access
- [ ] Advanced filters and search
- [ ] Batch case processing
- [ ] Integration with legal databases
- [ ] Custom scoring weights per firm

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
1. Check existing GitHub issues
2. File a new issue with reproduction steps
3. Contact the development team

---

**Built with** ⚖️ **for legal professionals** 🏛️
