# PriceWatch — Frontend

Vite + React 19 + TypeScript frontend for the PriceWatch FastAPI backend.

## Tech stack

- **Vite 8** + **React 19** + **TypeScript 6**
- **react-router-dom 7** — client-side routing
- **recharts** — price-history line chart
- **oxlint** — linting (bundled by Vite template)
- No CSS framework — inline styles matching sale-tracker aesthetic

## Pages

| Route        | Auth     | Description                                                                           |
| ------------ | -------- | ------------------------------------------------------------------------------------- |
| `/login`     | public   | Email + password login, stores access + refresh tokens                                |
| `/register`  | public   | Account creation                                                                      |
| `/products`  | optional | Product grid with brand tab, keyword search, sort; click card for price history chart |
| `/watchlist` | required | Create / edit / delete keyword + target-price watches                                 |
| `/alerts`    | required | Paginated alert history (newest first)                                                |

## Environment variable

| Variable            | Default                 | Description              |
| ------------------- | ----------------------- | ------------------------ |
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI backend base URL |

Create a `.env.local` file (git-ignored) to override:

```
VITE_API_BASE_URL=https://your-production-domain.com
```

## Quick start

```bash
# Install dependencies
bun install

# Development server (proxies /auth /products /watchlist /alerts to localhost:8000)
bun run dev

# Type-check + production build
bun run build

# Preview production build locally
bun run preview

# Lint
bun run lint
```

## Project structure

```
src/
├── types.ts                  # TypeScript types mirroring backend schemas
├── lib/
│   ├── auth.ts               # localStorage token helpers
│   └── api.ts                # Centralised API client (auto-refresh on 401)
├── context/
│   └── AuthContext.tsx       # Auth state + login/register/logout
├── components/
│   ├── NavBar.tsx
│   ├── ProductCard.tsx
│   ├── PriceHistoryModal.tsx # Recharts line chart + product detail
│   ├── Spinner.tsx
│   └── ErrorMessage.tsx
└── pages/
    ├── AuthPage.tsx          # Shared login / register form
    ├── ProductsPage.tsx
    ├── WatchlistPage.tsx
    └── AlertsPage.tsx
```

## API client notes

- All requests go through `src/lib/api.ts` which automatically attaches `Authorization: Bearer <token>`.
- On a 401 response it attempts one silent refresh via `POST /auth/refresh`. If refresh fails, tokens are cleared and the user is redirected to `/login`.
- The Vite dev-server proxy forwards backend paths so CORS is not an issue in development.
