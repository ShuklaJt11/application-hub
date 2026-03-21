# Frontend Development Guide

## Project Setup Completion

The frontend has been fully set up with the following features:

### ✅ Vite + React + TypeScript
- Latest versions of React 18, Vite 5, and TypeScript 5
- Configured with HMR (Hot Module Replacement) for development
- Optimized build configuration with code splitting

### ✅ ESLint + Prettier
- ESLint configured with TypeScript support and React rules
- Prettier configured for consistent code formatting
- Pre-commit hooks ready (install with: `npm run lint:fix`)

### ✅ TailwindCSS
- Full Tailwind CSS setup with custom color schemes
- PostCSS configured with autoprefixer
- Responsive design utilities included

### ✅ Feature-Based Folder Structure
```
src/
├── features/              # Feature modules
│   ├── common/           # Shared across features
│   │   ├── components/   # Button, Card, Header
│   │   ├── hooks/        # useAsync, custom hooks
│   │   └── utils/        # formatDate, cn, etc.
│   ├── auth/             # Authentication feature
│   ├── dashboard/        # Dashboard feature
│   ├── applications/     # Applications management
│   └── reminders/        # Reminders management
├── api/                  # API client configuration
├── types/                # Global type definitions
└── styles/               # Global styles
```

### ✅ Environment Variables
- `.env.example` with all required variables
- `.env` with development defaults
- VITE_API_URL pointing to backend
- VITE_API_TIMEOUT for request timeout
- App metadata variables

### ✅ Absolute Imports
Configured path aliases in `tsconfig.json` and `vite.config.ts`:
```typescript
import Button from '@components/Button'
import { formatDate } from '@utils/helpers'
import { useAsync } from '@hooks/useAsync'
import { User } from '@types'
import { apiConfig } from '@api/config'
```

### ✅ Docker Setup
- Multi-stage Dockerfile for optimized production build
- Health checks configured
- Proper volume mounting for development
- Frontend service integrated in docker-compose.yml

## Getting Started

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Development Server
```bash
npm run dev
```
Visit `http://localhost:5173`

### 3. Build for Production
```bash
npm run build
```

### 4. Docker Setup
To run with Docker Compose:
```bash
docker-compose up -d
```

The frontend will be available at `http://localhost:5173`

## Development Commands

```bash
# Start development server
npm run dev

# Build production bundle
npm run build

# Preview production build locally
npm run preview

# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Format code with Prettier
npm run format

# Check formatting without changes
npm run format:check
```

## Adding a New Feature

1. Create feature folder in `src/features/your-feature/`
2. Add subfolders: `components/`, `pages/`, `services/`, `hooks/`
3. Export components from `index.ts`
4. Use absolute imports with `@features/your-feature`

Example:
```typescript
import { YourComponent } from '@features/your-feature/components'
```

## API Integration

API client is configured in `src/api/config.ts`:

```typescript
import { apiConfig } from '@api/config'

const response = await fetch(`${apiConfig.baseURL}/endpoint`)
```

## Common Patterns

### Using Custom Hooks
```typescript
import { useAsync } from '@hooks/useAsync'

const { data, status, error, execute } = useAsync(fetchData)
```

### Component with Styles
```typescript
import { cn } from '@utils/helpers'

const MyComponent = ({ className }) => (
  <div className={cn('base-styles', className)}>
    Content
  </div>
)
```

### Type-Safe API Calls
```typescript
import { Application } from '@types'
import { apiConfig } from '@api/config'

const fetchApplications = async (): Promise<Application[]> => {
  const response = await fetch(`${apiConfig.baseURL}/applications`)
  return response.json()
}
```

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | http://localhost:8000/api | Backend API base URL |
| `VITE_API_TIMEOUT` | 30000 | API request timeout in ms |
| `VITE_APP_NAME` | Application Hub | Application display name |
| `VITE_APP_VERSION` | 0.1.0 | Application version |
| `VITE_ENABLE_ANALYTICS` | false | Enable usage analytics |

## Next Steps

1. Create feature-specific pages and components
2. Set up API service layer in each feature
3. Implement authentication flow
4. Add state management (if needed - React Context API is pre-configured)
5. Create dashboard and application listing pages
6. Set up form validation and handling
7. Implement error boundaries and error handling

## Troubleshooting

### Port 5173 already in use
```bash
# Use a different port
npm run dev -- --port 3000
```

### Dependencies not installing in Docker
```bash
# Rebuild without cache
docker-compose up -d --build
```

### API calls failing
- Check backend is running: `http://localhost:8000`
- Verify VITE_API_URL in `.env`
- Check CORS settings in backend
