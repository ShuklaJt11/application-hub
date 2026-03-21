# Frontend

The frontend application built with Vite, React, and TypeScript.

## Quick Start

### Prerequisites
- Node.js 16+ and npm/yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Linting & Formatting

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Format code with Prettier
npm run format

# Check formatting
npm run format:check
```

## Project Structure

```
src/
├── main.tsx                 # Entry point
├── App.tsx                  # Root component
├── index.css               # Global styles
├── types/                  # TypeScript type definitions
├── api/                    # API client configuration
├── styles/                 # Global stylesheets
└── features/               # Feature-based structure
    ├── common/            # Shared components, hooks, utils
    ├── auth/              # Authentication feature
    ├── dashboard/         # Dashboard feature
    ├── applications/      # Applications management
    └── reminders/         # Reminders management
```

## Environment Variables

Copy `.env.example` to `.env` and update the values:

```
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
```

## Features

- ✅ Vite + React 18
- ✅ TypeScript
- ✅ TailwindCSS for styling
- ✅ ESLint + Prettier
- ✅ Absolute imports with path aliases
- ✅ Feature-based folder structure
- ✅ API client with environment configuration
- ✅ Custom hooks and utilities
- ✅ Pre-configured common components
