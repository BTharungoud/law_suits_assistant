# Law Assistant Backend

## Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in your API keys
cp .env.example .env
```

## Configuration

Edit `.env`:
```
LLM_PROVIDER=openai              # or 'gemini'
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
FRONTEND_URL=http://localhost:3000
DEBUG=True
```

## Running

```bash
# Development with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

## API Endpoints

### Health Check
- `GET /api/health` - Check backend status

### Evaluate Cases
- `POST /api/evaluate-from-file` - Upload case file (PDF, DOCX, TXT) for evaluation
- `POST /api/evaluate-text` - Evaluate case from raw text

### Case Management
- `GET /api/cases` - Get all evaluated cases (ranked by priority)
- `GET /api/cases/{case_id}` - Get specific case details
- `DELETE /api/cases/{case_id}` - Delete specific case
- `DELETE /api/cases` - Delete all cases

### Utilities
- `GET /api/disclaimer` - Get legal disclaimer
