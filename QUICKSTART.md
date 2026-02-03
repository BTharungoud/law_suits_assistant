# Quick Start Guide

## 🚀 Fast Track Setup

### Option A: Local Development (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...

uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit: **http://localhost:3000**

API Docs: **http://localhost:8000/docs**

---

### Option B: Docker (Recommended for Testing/Deployment)

```bash
cp .env.example .env

# Edit .env with your API keys

docker-compose up

# Wait for "Uvicorn running on" message
```

Visit: **http://localhost:3000**

---

### Option C: Production Build

**Backend:**
```bash
docker build -f Dockerfile.backend -t law-assistant-backend .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e LLM_PROVIDER=openai \
  law-assistant-backend
```

**Frontend:**
```bash
docker build -f Dockerfile.frontend -t law-assistant-frontend .
docker run -p 3000:3000 law-assistant-frontend
```

---

## 📋 First Steps

1. **Create .env file:**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Add your API keys:**
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-xxx
   GEMINI_API_KEY=xxx
   ```

3. **Choose setup method** (A, B, or C above)

4. **Open http://localhost:3000**

---

## 🎯 Using the System

### Single Case Upload

1. Click "📤 Single Case" tab
2. Fill in case details:
   - **Case Title**: e.g., "Smith v. Jones"
   - **Jurisdiction**: e.g., "California"
   - **Case Type**: Civil, Criminal, Commercial, or Arbitration
   - **Claimed Damages** (optional): e.g., 500000
3. Choose upload method:
   - **📄 Upload File**: PDF, DOCX, or TXT
   - **✏️ Enter Text**: Paste case details
4. Click **"Evaluate Case"**
5. View results in "📋 View Cases" tab

### Batch Upload (Multiple Cases at Once)

**✨ NEW FEATURE**: Upload 5, 10, or 100+ cases at once!

1. Click "📁 Batch Upload" tab
2. **Drag files** into drop zone OR click to browse
3. Edit case details in **inline table**:
   - Title, Jurisdiction, Type, Damages amount
   - Remove individual cases with ✕ button
4. Click **"Evaluate N Cases"** button
5. **Progress bar** shows real-time evaluation
6. View ranked results in "📋 View Cases" tab

**Performance**: 
- Single case: ~10-15 seconds
- 5 cases: ~10-15 seconds (5x faster with parallel processing!)
- 10 cases: ~10-15 seconds (10x faster!)
- 100 cases: ~20-30 seconds (50-100x faster!)

### View & Analyze Cases

- **📋 View Cases** tab shows all evaluated cases
- **Sorted by priority** (highest score first)
- **Click any case** to see detailed analysis
- **Delete cases** with the trash icon
- **"Clear All"** button removes all cases

---

## 🔧 Configuration

Edit `backend/.env`:

```env
# LLM Provider (openai or gemini)
LLM_PROVIDER=openai

# OpenAI (required if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# Google Gemini (required if LLM_PROVIDER=gemini)
GEMINI_API_KEY=...

# Backend settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True

# Frontend
FRONTEND_URL=http://localhost:3000

# Database (optional, SQLite by default)
DATABASE_URL=sqlite:///./law_assistant.db
```

**Switching LLM Provider:**
- Change `LLM_PROVIDER` from `openai` to `gemini`
- Ensure API key is set in `.env`
- Restart backend

---

## 📊 Understanding Scores

### Legal Merit (0-10)
- **9-10**: Strong case with clear evidence
- **7-8**: Good case, reasonable grounds
- **5-6**: Moderate case, mixed evidence
- **3-4**: Weak case, significant challenges
- **0-2**: Very weak, major legal flaws

### Damages Potential (0-10)
- **9-10**: High ($1M+), solvent defendant
- **7-8**: Substantial ($500K-$1M)
- **5-6**: Moderate ($100K-$500K)
- **3-4**: Low (<$100K)
- **0-2**: Minimal/uncollectible

### Case Complexity (0-10)
- **0-2**: Simple (6-12 months)
- **3-4**: Moderate (12-18 months)
- **5-6**: Complex (18-24 months)
- **7-8**: Very complex (24+ months)
- **9-10**: Extremely complex

### Priority Score Formula
```
(Legal Merit × 0.4) + (Damages × 0.4) - (Complexity × 0.2)
```
**Higher = More attractive case**

---

## 🧪 Testing

Run backend tests:
```bash
cd backend
python -m pytest tests/ -v
```

Tests cover:
- File parsing (PDF, DOCX, TXT)
- Data model validation
- Scoring formula
- API endpoints

---

## 🐛 Troubleshooting

### "API key error" when evaluating
- Check `.env` file has correct key
- Restart backend after editing `.env`
- Verify key is valid in OpenAI/Gemini dashboard

### Frontend can't reach backend
- Ensure backend is running: `http://localhost:8000/docs`
- Check CORS settings in `app/main.py`
- Verify frontend is accessing correct API URL

### File upload fails
- Only PDF, DOCX, TXT files supported
- Check file size (recommend <5MB)
- Ensure file is readable

### Docker build fails
- Ensure `.env` exists before `docker-compose up`
- Check internet connection (downloading dependencies)
- Try `docker-compose build --no-cache`

---

## 📚 Learn More

- **Complete Docs**: See `README.md`
- **API Reference**: See `backend/README.md`
- **Security & Privacy**: See `SECURITY.md`
- **Frontend Guide**: See `frontend/README.md`
- **Project Structure**: See `PROJECT_STRUCTURE.md`
- **Live API Docs**: http://localhost:8000/docs (when running)

---

## ⚖️ Important Disclaimer

**This is decision-support software ONLY, NOT legal advice.**

- Analysis is AI-generated; errors possible
- Not a substitute for qualified attorneys
- Always consult lawyers before major decisions
- Scores reflect only provided information
- Missing details may skew results

See `SECURITY.md` for full compliance details.

---

## 🆘 Support

1. **Check logs** in terminal output
2. **Verify configuration** in `.env`
3. **Test API** at http://localhost:8000/docs
4. **Read docs** in project root directory

---

**Happy case prioritizing!** ⚖️
