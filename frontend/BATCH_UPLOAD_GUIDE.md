# Batch Upload Feature

## Overview

The batch upload feature allows you to evaluate multiple legal cases in parallel with a single submission. This is ideal for law firms processing multiple cases at once.

## Features

✅ **Drag-and-drop multiple files** - Upload 5, 10, or 100+ cases at once
✅ **Parallel processing** - All cases evaluated simultaneously (faster)
✅ **Inline metadata editing** - Edit case title, jurisdiction, type, damages in a table
✅ **Progress tracking** - Real-time progress bar during evaluation
✅ **Automatic ranking** - Results sorted by priority score
✅ **Error handling** - Partial success if some cases fail
✅ **Responsive design** - Works on mobile and desktop

## How to Use

### 1. Go to Batch Upload Tab

Click **"📁 Batch Upload"** in the navigation.

### 2. Add Files

**Method A - Drag and Drop:**
- Drag multiple PDF, DOCX, or TXT files onto the drop zone
- All files will be added to the queue

**Method B - Click to Browse:**
- Click the drop zone
- Select multiple files from your computer

### 3. Edit Case Details (Optional)

A table appears with each file. You can:
- **Edit Case Title**: Default is the filename
- **Set Jurisdiction**: E.g., California, NY, Texas
- **Choose Case Type**: Civil, Criminal, Commercial, or Arbitration
- **Add Damages Amount**: Optional claimed damages in USD
- **Remove Cases**: Click ✕ to remove any case

### 4. Submit for Evaluation

Click **"Evaluate N Cases"** button to start batch processing.

### 5. Monitor Progress

- Progress bar shows number of cases evaluated
- Status updates in real-time
- Results appear in order of priority score (highest first)

### 6. View Results

Automatically navigates to **"📋 View Cases"** tab showing all ranked cases.

---

## Example Workflow

```
1. Drag 5 PDF files → Added to queue
2. Edit titles, jurisdictions, types in table
3. Click "Evaluate 5 Cases"
4. Progress bar: 1/5 → 2/5 → 3/5 → 4/5 → 5/5
5. Results ranked by priority score
6. Click any case for detailed analysis
```

---

## API Endpoint

**POST /api/evaluate-batch**

Request:
```json
{
  "files": [File, File, File],
  "titles": ["Case 1", "Case 2", "Case 3"],
  "jurisdictions": ["California", "NY", "Texas"],
  "case_types": ["Civil", "Civil", "Commercial"],
  "claimed_damages_list": [500000, 250000, 1000000]
}
```

Response:
```json
{
  "cases": [
    {
      "case_id": "abc123",
      "case_title": "Smith v. Jones",
      "priority_score": 7.8,
      "priority_rank": "High",
      ...
    }
  ],
  "total_cases": 3,
  "errors": [
    {
      "index": 1,
      "file": "broken.pdf",
      "error": "Failed to parse PDF"
    }
  ]
}
```

---

## Performance

### Parallel Processing

All cases are evaluated **simultaneously** using Python's `asyncio.gather()`:

- **1 case**: ~10-15 seconds
- **5 cases**: ~10-15 seconds (parallel, same time!)
- **10 cases**: ~10-15 seconds
- **100 cases**: ~10-15 seconds (depending on LLM provider rate limits)

**Result**: 10x faster than uploading one case at a time!

### File Size Limits

- Recommended: <5MB per file
- Typical: 50-200 KB for PDF
- Large: 500 KB - 2 MB for complex documents

### Maximum Batch Size

- **Recommended**: 10-50 cases per batch
- **Safe limit**: Up to 100 cases
- **Rate limits**: Check your LLM provider limits (OpenAI/Gemini)

---

## Error Handling

If some cases fail during batch processing:

1. Successful cases are still returned and ranked
2. Failed cases listed with error reason
3. You can fix and re-upload failed cases
4. Response shows: `"successful_count": 4, "failed_count": 1`

---

## Tips & Best Practices

### Before Upload

✅ Ensure all files are PDF, DOCX, or TXT
✅ Check file names are descriptive (used as default titles)
✅ Verify claimed damages amounts are in USD
✅ Keep batch size <50 for faster processing

### During Evaluation

✅ Don't close the browser during progress
✅ Watch progress bar (takes 10-15 seconds typically)
✅ Check for errors in response

### After Results

✅ Click high-priority cases for detailed analysis
✅ Use "Clear All" to reset and upload new batch
✅ Delete individual cases with trash icon

---

## Troubleshooting

### "API key error" during batch evaluation
- Check `.env` has valid OpenAI/Gemini key
- Restart backend after editing `.env`

### "Batch evaluation failed" message
- Check all files are valid (PDF/DOCX/TXT)
- Verify file sizes aren't too large
- Try with fewer files (test with 2-3 first)

### Progress bar stuck
- Backend may be processing large files
- Wait 20-30 seconds
- Check backend logs for errors

### Some files fail but others succeed
- Normal behavior - error is returned for failed files
- Review errors in response
- Re-upload failed files individually

---

## Advantages Over Single Upload

| Feature | Single Upload | Batch Upload |
|---------|---------------|--------------|
| Files Per Session | 1 | Unlimited |
| Speed | 10-15s each | 10-15s for all |
| Editing Metadata | Form fields | Inline table |
| Parallel Processing | No | Yes |
| Error Recovery | Full upload fails | Partial success |
| Typical Use Case | Single case | 5-100 cases |

---

## API Integration Example

### JavaScript/TypeScript

```typescript
import { evaluateCasesBatch, CaseMetadata } from './services/api';

const files = [file1, file2, file3];
const metadata: CaseMetadata[] = [
  { title: "Case 1", jurisdiction: "CA", case_type: "Civil", claimed_damages: 500000 },
  { title: "Case 2", jurisdiction: "NY", case_type: "Civil", claimed_damages: 250000 },
  { title: "Case 3", jurisdiction: "TX", case_type: "Commercial", claimed_damages: 1000000 }
];

try {
  const result = await evaluateCasesBatch(files, metadata, (progress) => {
    console.log(`Evaluated ${progress.completed} of ${progress.total}`);
  });
  console.log('Results:', result.data.cases);
} catch (error) {
  console.error('Batch failed:', error);
}
```

### cURL

```bash
curl -X POST http://localhost:8000/api/evaluate-batch \
  -F "files=@case1.pdf" \
  -F "files=@case2.pdf" \
  -F "files=@case3.pdf" \
  -F 'titles=["Case 1","Case 2","Case 3"]' \
  -F 'jurisdictions=["California","New York","Texas"]' \
  -F 'case_types=["Civil","Civil","Commercial"]' \
  -F 'claimed_damages_list=[500000,250000,1000000]'
```

---

## Important

**⚠️ Disclaimer**: This batch evaluation is for decision-support purposes only and does NOT constitute legal advice.

Always consult qualified attorneys before making case decisions.

---

**Happy batch evaluating!** 📁⚖️
