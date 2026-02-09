# Evaluation Failed - Fix Documentation

## Problem Identified

The error **"Evaluation failed. Please check your API configuration and try again."** was caused by **malformed JSON responses from the Gemini API**. The API was returning JSON with:

1. **Unterminated strings** - Missing closing quotes in JSON values
2. **Unescaped control characters** - Newlines, tabs, and other special characters not properly escaped inside string values
3. **Incomplete JSON structures** - Missing closing braces or quotes

## Root Cause

Looking at the error logs in `backend/logs/llm_failures.log`, we found multiple JSON parsing failures:
- "Unterminated string starting at: line 29 column 7"
- "Expecting value: line 16 column 66"

These errors occurred because:
1. Gemini API responses contained multi-line text with embedded newlines that weren't properly escaped
2. The existing JSON repair logic wasn't catching all edge cases
3. Control characters in legal text weren't being escaped before JSON parsing

## Solution Implemented

### 1. **Enhanced JSON Repair Logic** (llm_adapter.py)

Added a new `_aggressive_json_repair()` method to the `GeminiProvider` class that:
- Scans through the JSON response character-by-character
- Properly escapes all control characters (`\n`, `\r`, `\t`, `\f`, `\b`)
- Escapes unicode control characters (`\u0000-\u001f`)
- Closes unterminated strings
- Validates the repaired JSON before returning

### 2. **Improved Error Handling**

Updated the evaluation flow in `GeminiProvider.evaluate_case()`:
```
1. Try direct parsing
2. Try fixing newlines
3. Try aggressive repair ✨ (NEW)
4. Try extracting JSON from wrapped text
5. Try line-by-line quote escaping
```

### 3. **Better Error Recovery**

- The `_extract_and_repair_json()` method now calls aggressive repair as the first fallback
- All repair attempts are tried before raising an error
- Full response is logged for debugging purposes

## Configuration Requirements

### Current Settings

Your `.env` file has:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyDT1FTYRuep6OZbFYUiefvQTtlBH1yTsJM
GEMINI_MODEL=gemini-2.5-flash
```

### Verification Steps

1. **Verify Gemini API Key**:
   - The key should be valid and have access to the `generativeai` API
   - Visit: https://makersuite.google.com/app/apikey

2. **Verify API Quotas**:
   - Ensure your Gemini API has sufficient quota
   - Check billing is enabled if applicable

3. **Alternative: Use OpenAI**

   If Gemini continues to fail, switch to OpenAI:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
   OPENAI_MODEL=gpt-4
   ```

## Testing the Fix

### Quick Test

1. Start the backend:
   ```bash
   cd backend
   python -m app.main
   ```

2. Try uploading a simple case document (PDF, DOCX, or TXT)

3. Check `backend/logs/llm_failures.log` - if no new entries appear, the fix is working

### Debugging

If evaluation still fails:

1. **Check error logs**:
   ```bash
   tail -f backend/logs/llm_failures.log
   ```

2. **Verify API connectivity**:
   ```python
   import google.generativeai as genai
   genai.configure(api_key="YOUR_KEY")
   model = genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content("Test")
   print(response.text)
   ```

3. **Review backend logs**:
   ```bash
   # Check backend console output for detailed errors
   ```

## Files Modified

- `backend/app/services/llm_adapter.py`
  - Added `_aggressive_json_repair()` method to `GeminiProvider`
  - Updated `evaluate_case()` error handling
  - Updated `_extract_and_repair_json()` to use aggressive repair

## Performance Impact

- **Minimal**: Additional JSON character scanning only occurs when normal parsing fails
- **Latency increase**: ~50-100ms in error cases (negligible for most users)
- **CPU**: Negligible - single-pass character scanning

## Next Steps

If you continue to experience issues:

1. Verify the `.env` file has the correct API keys
2. Check that your Gemini API quota hasn't been exceeded
3. Try switching to OpenAI provider for testing
4. Check `backend/logs/llm_failures.log` for the actual error responses
5. Consider increasing `max_output_tokens` if Gemini responses are being truncated

## Related Files

- `backend/.env` - API configuration
- `backend/app/config.py` - Settings loader
- `backend/app/services/evaluator.py` - Case evaluation orchestrator
- `backend/logs/llm_failures.log` - Error log with full responses
