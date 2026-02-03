# Law Assistant Frontend

Modern React application for evaluating and prioritizing legal cases.

## Setup

```bash
npm install
npm run dev        # Development server (http://localhost:3000)
npm run build      # Production build
npm run preview    # Preview production build
```

## Structure

```
src/
  ├── App.tsx                   # Main app component
  ├── App.css                   # Global styles
  ├── main.tsx                  # React entry point
  ├── index.css                 # Base styles
  ├── components/
  │   ├── CaseUpload.tsx        # Case upload form
  │   ├── CaseList.tsx          # Case listing & ranking
  │   ├── CaseCard.tsx          # Case preview card
  │   ├── CaseDetail.tsx        # Case detail modal
  │   └── *.css                 # Component styles
  └── services/
      └── api.ts                # API client & types
```

## Key Components

### CaseUpload
Upload case files (PDF, DOCX, TXT) or enter case text with metadata:
- Title, Jurisdiction, Case Type, Claimed Damages
- File upload or text input modes
- Client-side validation
- Loading states and error handling

### CaseList
Display evaluated cases ranked by priority score:
- Sorted high-to-low by priority
- Inline case cards with key scores
- Delete individual cases or clear all
- Click to view detailed analysis

### CaseDetail
Full case analysis modal:
- Tabbed interface (Overview, Legal Merit, Damages, Complexity)
- Score breakdowns with explanations
- Key factors for each dimension
- Priority calculation formula

## API Integration

API client in `src/services/api.ts`:
- Evaluate from file: `evaluateCaseFromFile(file, metadata)`
- Evaluate from text: `evaluateCaseFromText(text, metadata)`
- Get all cases: `getAllCases()`
- Get single case: `getCaseById(caseId)`
- Delete case: `deleteCase(caseId)`
- Clear all: `clearAllCases()`

## Styling

All components use CSS with:
- Responsive design (mobile-first)
- Blue gradient theme (brand colors)
- Accessible contrast ratios
- Smooth transitions
- Modern layout (CSS Grid, Flexbox)

## Environment

Configure via environment variables (or use defaults):
```
REACT_APP_API_URL=http://localhost:8000/api
```

Or set in `.env`:
```
VITE_API_URL=http://localhost:8000/api
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance

- Async API calls with Axios
- Efficient re-renders (React hooks)
- Optimized CSS (single stylesheet per component)
- Lazy component loading via tabs
