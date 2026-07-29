---
name: frontend-dev
description: Build and maintain the React/TypeScript frontend, including components, pages, types, and API integration.
---

## Frontend Development — DeceptiScan

### Stack
- React 18, TypeScript 5 (strict mode), Vite 5
- react-router-dom v6, axios
- Vitest + Testing Library for tests

### Project Layout
```
frontend/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Root component with routing
│   ├── index.css             # Global styles and design tokens
│   ├── components/
│   │   ├── index.ts          # Named exports: ArticleInput, AnalysisResult, ScoreMeter
│   │   ├── ArticleInput.tsx  # Text submission form
│   │   ├── AnalysisResult.tsx# Results display with sentence highlighting
│   │   ├── ScoreMeter.tsx    # Authenticity score gauge
│   │   └── *.test.tsx        # Co-located tests
│   ├── pages/
│   │   ├── Home.tsx          # Main analysis page
│   │   ├── Login.tsx         # Login form
│   │   └── Register.tsx      # Registration form
│   ├── services/
│   │   └── api.ts            # Axios API singleton
│   ├── types/
│   │   └── index.ts          # All TypeScript interfaces
│   └── test/
│       └── setup.ts          # Test setup (jest-dom)
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Conventions
- Strict TypeScript — no `any`, no implicit `any`
- Components in named exports via `components/index.ts`
- No inline comments — code should be self-documenting
- Styles in `index.css` (no CSS modules — keeps bundle small)
- API calls go through `apiService` singleton from `services/api.ts`
- JWT stored in `localStorage` under `authToken` key
- Component props typed in `types/index.ts`

### Key Types
- `AnalysisResult`: id, authenticityScore (0–100), confidenceScore (0–1), classification, sentenceAnalysis[]
- `SentenceAnalysis`: index, text, isSuspicious, score (0–100), confidence, category, flags[], explanation
- `ScoreMeterProps`: score, label, confidence?
- `Classification`: 'reliable' | 'mixed' | 'unreliable' | 'unknown'

### Score Thresholds
- **Reliable**: score ≥ 75 (green)
- **Mixed**: 40–74 (yellow/amber)
- **Unreliable**: < 40 (red)
- **Unknown**: confidence < 0.3 (grey, with disclaimer)

### Common Tasks

**Add a new component:**
1. Create file in `frontend/src/components/`
2. Export from `components/index.ts`
3. Add props TypeScript interface in `types/index.ts`
4. Add tests co-located (`ComponentName.test.tsx`)

**Add a new page:**
1. Create file in `frontend/src/pages/`
2. Add route in `App.tsx`

**Run dev server:**
```bash
cd frontend && npm run dev
```

**Run tests:**
```bash
cd frontend && npm test
```

**Run lint:**
```bash
cd frontend && npm run lint
```
