# Upwork Scraper - Frontend

Modern React frontend for the Upwork Scraper application, built with Vite, Zustand, and Tailwind CSS.

## Features

- **Dashboard**: Monitor scraping activities and view stats in real-time
- **URL Management**: CRUD interface for managing Upwork search URLs
- **Jobs Browser**: Advanced table with filtering and pagination using TanStack Table
- **Job Details**: Detailed job view with on-demand detail scraping
- **Real-time Updates**: Server-Sent Events (SSE) for live scraping progress
- **Modern UI**: Built with Shadcn/UI components and Tailwind CSS

## Tech Stack

- **Framework**: React 19 with Vite
- **State Management**: Zustand
- **Routing**: React Router v7
- **UI Components**: Shadcn/UI (Radix UI primitives)
- **Styling**: Tailwind CSS
- **Table**: TanStack Table v8
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on \`http://localhost:8000\` (or configure via \`.env\`)

### Installation

\`\`\`bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
\`\`\`

### Environment Configuration

The \`.env\` file is already configured:

\`\`\`env
VITE_API_URL=http://localhost:8000
\`\`\`

## Project Structure

\`\`\`
frontend/
├── src/
│   ├── components/ui/       # Shadcn/UI components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # API client and utilities
│   ├── pages/               # Page components
│   ├── store/               # Zustand store
│   ├── App.jsx              # Main app component
│   └── main.jsx             # Entry point
├── .env                     # Environment variables
└── package.json
\`\`\`

## Usage

1. **Start the backend** (from the backend directory):
   \`\`\`bash
   cd ../backend
   python -m uvicorn app.main:app --reload
   \`\`\`

2. **Start the frontend** (from this directory):
   \`\`\`bash
   npm run dev
   \`\`\`

3. **Open your browser**: http://localhost:5173

## Features Overview

### Dashboard
- View overall statistics
- Trigger search and detail scraping
- Monitor real-time progress
- See recent jobs

### URL Management
- Add Upwork search URLs
- Enable/disable URLs
- Edit URL names
- Delete URLs
- View scraping history

### Jobs
- Browse all scraped jobs
- Filter and search
- Sort by any column
- View job details
- Trigger detail scraping

### Job Details
- View full job information
- See client details
- View required skills
- Scrape details on-demand
- Link to original posting

## Development

\`\`\`bash
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
\`\`\`
