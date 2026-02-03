# SECURITY & COMPLIANCE

## Data Handling

### Storage
- **Default Mode**: Ephemeral (no persistence)
- **Optional**: SQLite for audit trails (disabled by default)
- **Encrypted**: All LLM API communications use HTTPS
- **No Logging**: Case text never logged to disk

### Privacy Controls
- ✅ File contents are not saved after evaluation
- ✅ Evaluation results stored in-memory only (lost on restart)
- ✅ No user tracking or telemetry
- ✅ No third-party data sharing
- ✅ API keys never exposed in responses

### Data Retention
- **Evaluations**: In-memory only (cleared on server restart)
- **Logs**: Console only, no file persistence
- **Database**: Optional, configurable retention (if enabled)
- **Manual Deletion**: `/api/cases` and `/api/cases/{id}` endpoints

## Legal Compliance

### Decision-Support Only
Every evaluation includes explicit disclaimer:
> "This evaluation is provided for decision-support purposes only and does NOT constitute legal advice."

### No Legal Advice
- ✅ No legal conclusions
- ✅ No predictive statements ("will win")
- ✅ No legal recommendations
- ✅ Factual analysis only

### Transparency
- ✅ Scores clearly explained with reasoning
- ✅ Key factors listed explicitly
- ✅ Formula visible to user
- ✅ Assumptions stated (missing info)
- ✅ No hidden algorithms

### Limitations Acknowledged
- ✅ AI errors possible
- ✅ Information gaps cause inaccuracy
- ✅ No replacement for lawyers
- ✅ Input quality matters (garbage in = garbage out)

## API Security

### CORS
- Origin restricted to configured frontend domain
- Methods: GET, POST, DELETE
- Headers: JSON content-type

### Input Validation
- ✅ File type validation (PDF, DOCX, TXT only)
- ✅ File size limits (5MB recommended)
- ✅ Metadata validation (all fields required)
- ✅ Text length limits (max 100KB)
- ✅ Case type enum (Civil, Criminal, Commercial, Arbitration)

### Error Handling
- ✅ Graceful error messages (no system details exposed)
- ✅ Input validation errors (user-friendly)
- ✅ LLM failures handled (user notified)
- ✅ File parsing errors caught

## LLM Provider Security

### OpenAI
- ✅ API key in `.env` (never committed)
- ✅ HTTPS-only communication
- ✅ No request logging by default
- ✅ Temperature=0 for consistency

### Google Gemini
- ✅ API key in `.env` (never committed)
- ✅ HTTPS-only communication
- ✅ No request logging
- ✅ Temperature=0 for consistency

## Deployment Security

### Development
```bash
DEBUG=False          # Always disable in production
LLM_PROVIDER=openai  # Choose provider
OPENAI_API_KEY=***   # Use secrets manager
GEMINI_API_KEY=***   # Use secrets manager
FRONTEND_URL=<your_domain>
```

### Production
- ✅ Use environment secrets management (not .env)
- ✅ Enable HTTPS for all connections
- ✅ Configure CORS to exact domain
- ✅ Set DEBUG=False
- ✅ Use reverse proxy (nginx) for API
- ✅ Add rate limiting
- ✅ Monitor API usage for abuse
- ✅ Regular security updates

### Docker
- ✅ API key passed as env vars (not in image)
- ✅ Run as non-root user
- ✅ Minimal base image (python:3.11-slim)
- ✅ Health checks enabled
- ✅ Volume mount for config (not secrets)

## Audit & Monitoring

### Available for Enhancement
- [ ] Request logging (audit trail)
- [ ] Evaluation history with persistence
- [ ] User authentication (future)
- [ ] Access logs
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (DataDog)

## Incident Response

If API keys are compromised:
1. Revoke compromised keys immediately (OpenAI/Gemini dashboards)
2. Rotate `.env` secrets
3. Redeploy with new keys
4. Review audit logs if available

---

**All users must understand**: This system provides analysis guidance, not legal advice. Consult qualified attorneys for binding legal decisions.
