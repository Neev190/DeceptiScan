# DeceptiScan Frontend

A React-based web application for AI-powered misinformation detection, built with TypeScript and Vite.

## Features

- **Modern React Architecture**: Built with React 18, TypeScript, and Vite for optimal development experience
- **Component-Based Design**: Modular components following design specifications
- **Analysis Interface**: Rich text input with real-time character counting and validation
- **Visual Results**: Interactive sentence-level highlighting with detailed analysis
- **Score Visualization**: Color-coded authenticity meter with interpretive labels  
- **User Authentication**: Complete login/register flow with form validation
- **Responsive Design**: Mobile-first responsive layout with accessibility support
- **API Integration**: Comprehensive service layer with error handling and caching

## Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development with comprehensive interface definitions
- **Vite** - Fast build tool with HMR for development
- **Axios** - HTTP client for API communication with interceptors
- **React Router DOM** - Client-side routing for SPA navigation
- **CSS Variables** - Modern styling with design token system

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ArticleInput.tsx    # Text submission component
│   ├── AnalysisResult.tsx  # Results display with highlighting
│   ├── ScoreMeter.tsx      # Authenticity score visualization
│   └── index.ts            # Component exports
├── pages/              # Route components  
│   ├── Home.tsx           # Main analysis page
│   ├── Login.tsx          # Authentication login
│   └── Register.tsx       # User registration
├── services/           # API and external services
│   └── api.ts             # Axios-based API service layer
├── types/              # TypeScript type definitions
│   └── index.ts           # All application types and interfaces
├── App.tsx             # Main app component with routing
├── main.tsx           # React DOM entry point
└── index.css          # Global styles and design tokens
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:5000

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Environment setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open application**: Navigate to http://localhost:3000

### Available Scripts

- `npm run dev` - Start development server with HMR
- `npm run build` - Build production bundle  
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint code analysis

## Component Architecture

### ArticleInput Component
- Text input with validation and character limits
- Optional metadata fields (title, source URL)
- Real-time validation and user feedback
- Submit handling with loading states

### AnalysisResult Component  
- Interactive sentence highlighting (red for suspicious, green for reliable)
- Clickable sentences with detailed analysis modal
- Analysis metadata and processing information
- Responsive design for mobile and desktop

### ScoreMeter Component
- Visual authenticity score from 0-100
- Color-coded interpretation (reliable, mixed, unreliable)
- Threshold markers and explanatory text
- Animated progress bar with smooth transitions

## API Integration

The application uses a comprehensive API service layer built with Axios:

### Features
- **Automatic Authentication**: JWT token management with interceptors
- **Error Handling**: Centralized error processing with user-friendly messages  
- **Request/Response Types**: Full TypeScript coverage for all endpoints
- **Caching Support**: Local storage for authentication state
- **Timeout Management**: Configurable timeouts for long-running analysis

### Endpoints
- `POST /api/v1/analyze` - Submit content for analysis
- `GET /api/v1/analyze/{id}` - Retrieve analysis by ID
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/history` - Analysis history (authenticated users)
- `POST /api/v1/feedback` - Submit analysis feedback

## Design System

### Color Scheme
- **Primary Blue**: #2563eb (interactive elements, highlights)
- **Success Green**: #22c55e (reliable content indicators)
- **Warning Orange**: #f59e0b (mixed reliability)
- **Danger Red**: #ef4444 (suspicious content flags)
- **Neutral Gray**: #64748b (secondary text, borders)

### Typography
- **System Font Stack**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
- **Scale**: Consistent size scale from 0.75rem to 3rem
- **Weight Hierarchy**: 400 (normal), 500 (medium), 600 (semibold), 700+ (bold)

### Spacing
- **Base Unit**: 0.25rem (4px) with consistent 4px grid
- **Component Padding**: 0.75rem to 2rem based on hierarchy
- **Layout Margins**: 1rem to 4rem for section spacing

## Accessibility Features

- **Semantic HTML**: Proper heading hierarchy and ARIA labels
- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Color Contrast**: WCAG AA compliant color combinations
- **Screen Reader**: Descriptive text for analysis results and interactions
- **Focus Management**: Visible focus indicators and logical tab order
- **Reduced Motion**: Respects user preference for reduced animations

## Performance Optimizations

### Build Optimizations
- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Unused code elimination in production builds  
- **Asset Optimization**: Minification and compression of CSS/JS
- **Source Maps**: Development debugging with production source maps

### Runtime Optimizations
- **React.memo**: Prevents unnecessary component re-renders
- **Lazy Loading**: Route-based lazy loading for better initial load
- **Request Debouncing**: Prevents excessive API calls during typing
- **Local Caching**: Client-side caching for analysis results

## Development Guidelines

### Code Style
- **TypeScript**: Strict typing with comprehensive interfaces
- **ESLint**: Enforced code quality and consistency rules
- **Component Props**: Explicit prop interfaces for all components  
- **Error Boundaries**: Graceful error handling and user feedback

### Best Practices
- **Single Responsibility**: Each component has a focused purpose
- **Composition over Inheritance**: Favor component composition
- **Immutable State**: Use state updates that don't mutate existing state
- **Error-First Design**: Handle error states prominently in UI

## Testing Strategy

### Recommended Testing Approach
- **Unit Tests**: Component logic and utility functions
- **Integration Tests**: Component interaction and API integration  
- **E2E Tests**: Full user workflows and critical paths
- **Visual Testing**: Component styling and responsive behavior

### Testing Framework Suggestions  
- **Vitest**: Fast unit testing with Vite integration
- **React Testing Library**: Component testing with user-focused queries
- **Playwright**: End-to-end testing with real browser automation
- **Storybook**: Component development and visual testing

## Deployment

### Build Configuration
The application builds to a static `dist/` directory:

```bash
npm run build
```

### Environment Variables
Production deployment requires:
- `VITE_API_URL`: Backend API base URL
- `VITE_APP_NAME`: Application name for branding
- `VITE_APP_VERSION`: Version number for footer/about

### Static Hosting
Compatible with:
- **Netlify**: Drag-and-drop deployment with automatic builds
- **Vercel**: Git-based deployment with preview environments  
- **AWS S3 + CloudFront**: Scalable static hosting with CDN
- **GitHub Pages**: Free hosting for public repositories

## Browser Support

- **Modern Browsers**: Chrome 88+, Firefox 85+, Safari 14+, Edge 88+
- **Mobile Browsers**: iOS Safari 14+, Chrome Mobile 88+
- **ES2020 Support**: Uses modern JavaScript features with Vite polyfills

## Contributing

1. **Follow TypeScript**: Maintain strict typing for all new code
2. **Component Structure**: Use established patterns for new components  
3. **Testing**: Add tests for new functionality and bug fixes
4. **Accessibility**: Ensure new features meet WCAG guidelines
5. **Performance**: Consider impact on bundle size and runtime performance

## License

This project is part of the DeceptiScan misinformation detection system.