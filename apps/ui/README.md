# Entertainment Planner UI

A React-based UI for the Entertainment Planner API with vibe selection and route planning.

## Features

- **Vibe Selection**: Choose from preset vibes (Lazy, Cozy, Scenic, Budget, Date) or enter custom
- **Quick Intents**: One-click selection for common activities (🍜 Tom Yum, 🌿 Park Walk, 🍸 Rooftop)
- **Route Building**: Generate 3-step entertainment routes based on vibe and intents
- **Route Display**: View place cards with names, summaries, tags, and distances
- **Step Replacement**: Replace step 2 with alternatives when available
- **Responsive Design**: Clean, dark theme with Tailwind CSS

## Prerequisites

- Node.js 16+ and npm
- Entertainment Planner API running on port 8000

## Quick Start

### 1. Start the API Server
```bash
# From project root
./scripts/run_api.sh
```

### 2. Start the UI Development Server
```bash
# From project root
./scripts/start_ui.sh
```

Or manually:
```bash
cd apps/ui
npm install
npm start
```

The UI will be available at [http://localhost:3000](http://localhost:3000)

## Demo Workflow

1. **Select a vibe**: Click on "Lazy" or type "lazy" in the custom input
2. **Choose intents**: Click on 🍜 Tom Yum, 🌿 Park Walk, and 🍸 Rooftop
3. **Build Route**: Click "Build Route" button
4. **View Results**: See 3 place cards with route information
5. **Replace Step 2**: If alternatives are available, click "Replace Step 2"

## API Integration

- **Proxy Configuration**: UI proxies API calls to `http://localhost:8000`
- **Endpoints Used**:
  - `GET /api/places/recommend` - Build routes
  - `GET /api/places/{id}` - Get place details
- **Hardcoded Coordinates**: Uses Bangkok center (13.7563, 100.5018)

## Development

### Project Structure
```
apps/ui/
├── src/
│   ├── App.tsx          # Main application component
│   ├── index.tsx        # React entry point
│   └── index.css        # Tailwind CSS imports
├── public/
│   └── index.html       # HTML template
├── package.json          # Dependencies and scripts
├── tailwind.config.js    # Tailwind configuration
└── tsconfig.json        # TypeScript configuration
```

### Key Components

- **Vibe Selection**: Radio-style buttons with custom text input
- **Intent Chips**: Toggleable emoji-labeled buttons
- **Route Cards**: Individual place displays with step numbers
- **Replace Button**: Dynamic button for step 2 alternatives

### Styling

- **Tailwind CSS**: Minimal, utility-first styling
- **Dark Theme**: Black background with gray accents
- **Responsive**: Mobile-friendly layout with proper spacing
- **Interactive**: Hover states and loading indicators

## Troubleshooting

### Common Issues

1. **API Connection Error**: Ensure the API server is running on port 8000
2. **Build Errors**: Run `npm install` to install dependencies
3. **Port Conflicts**: UI runs on port 3000, API on port 8000

### Development Commands

```bash
npm start          # Start development server
npm run build     # Build for production
npm test          # Run tests
npm run eject     # Eject from Create React App (not recommended)
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
