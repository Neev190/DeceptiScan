import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Home from '../pages/Home';
import AnalysisDetail from '../pages/AnalysisDetail';
import * as apiService from '../services/api';
import { AnalysisHistoryItem, AnalysisResult } from '../types';

// Mock the API service
vi.mock('../services/api', () => ({
  apiService: {
    getRecentAnalyses: vi.fn(),
    getAnalysis: vi.fn(),
    getHistoryItem: vi.fn(),
  },
}));

// Mock router navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'test-analysis-id-123' }),
  };
});

describe('View Case Navigation Bug - Bug Condition Exploration Tests', () => {
  const mockUser = {
    id: 'user123',
    email: 'test@example.com',
    username: 'testuser',
    createdAt: '2024-01-01T00:00:00Z',
  };

  const mockRecentAnalysis: AnalysisHistoryItem = {
    id: 'test-analysis-id-123',
    authenticityScore: 85,
    classification: 'reliable' as const,
    createdAt: '2024-01-01T10:00:00Z',
    title: 'Test Analysis Result',
    input_text: 'This is a test article content for analysis...',
  };

  const mockAnalysisResult: AnalysisResult = {
    id: 'test-analysis-id-123',
    authenticityScore: 85,
    classification: 'reliable' as const,
    confidence: 0.9,
    sentenceAnalysis: [
      {
        index: 0,
        text: 'This is a test sentence.',
        isSuspicious: false,
        score: 85,
        confidence: 0.9,
        category: 'factual',
        flags: [],
        explanation: 'This sentence appears factual.',
      },
    ],
    processingTime: 1500,
    analyzedAt: '2024-01-01T10:00:00Z',
    modelVersion: '1.0.0',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock authenticated user
    const mockAuthContext = {
      isAuthenticated: true,
      user: mockUser,
      token: 'mock-token',
      login: vi.fn(),
      logout: vi.fn(),
      loading: false,
    };

    // Mock successful recent analyses fetch
    vi.mocked(apiService.apiService.getRecentAnalyses).mockResolvedValue([mockRecentAnalysis]);
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthProvider value={{
          isAuthenticated: true,
          user: mockUser,
          token: 'mock-token',
          login: vi.fn(),
          logout: vi.fn(),
          loading: false,
        }}>
          {component}
        </AuthProvider>
      </BrowserRouter>
    );
  };

  /**
   * **Validates: Requirements 1.1, 1.2, 1.3**
   * 
   * This is a Bug Condition Exploration Test that MUST FAIL on unfixed code.
   * 
   * Bug Condition: When users click "VIEW CASE" from Recent Archival Pulls,
   * they encounter a white page instead of analysis results.
   * 
   * Expected Behavior (when fixed): Clicking "VIEW CASE" should navigate to
   * analysis detail page and display complete analysis results including
   * authenticity score, classification, confidence level, and sentence analysis.
   * 
   * CRITICAL: This test is EXPECTED TO FAIL on unfixed code - failure confirms bug exists.
   */
  it('Property 1: Bug Condition - View Case Navigation displays complete analysis results', async () => {
    // Mock successful analysis fetch from both endpoints (analysis and history)
    vi.mocked(apiService.apiService.getAnalysis).mockResolvedValue(mockAnalysisResult);
    vi.mocked(apiService.apiService.getHistoryItem).mockResolvedValue(mockAnalysisResult);

    // 1. Render Home page with recent analyses
    renderWithProviders(<Home />);

    // Wait for recent analyses to load
    await waitFor(() => {
      expect(screen.getByText('Recent Archival Pulls')).toBeInTheDocument();
    });

    // Verify the recent analysis item is displayed
    await waitFor(() => {
      expect(screen.getByText('Test Analysis Result')).toBeInTheDocument();
      expect(screen.getByText('RELIABLE // 85%')).toBeInTheDocument();
    });

    // 2. Click the "VIEW CASE" link from Recent Archival Pulls
    const viewCaseLink = screen.getByText('VIEW CASE');
    expect(viewCaseLink.closest('a')).toHaveAttribute('href', '/analysis/test-analysis-id-123');
    
    // Simulate clicking "VIEW CASE" - this should trigger navigation
    await userEvent.click(viewCaseLink);

    // 3. Now render AnalysisDetail component to simulate the navigation result
    // This is where the bug manifests - the component should display content but doesn't
    renderWithProviders(<AnalysisDetail />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('RETRIEVING CASE FILE')).not.toBeInTheDocument();
    }, { timeout: 5000 });

    // 4. CRITICAL ASSERTIONS - These SHOULD PASS when bug is fixed, FAIL on unfixed code
    
    // Verify navigation breadcrumb is displayed (not white page)
    await waitFor(() => {
      expect(screen.getByText(/Case File #[A-Z0-9]+/)).toBeInTheDocument();
    });

    // Verify authenticity score is displayed
    expect(screen.getByText('85/100')).toBeInTheDocument();
    
    // Verify classification is displayed
    expect(screen.getByText(/reliable/i)).toBeInTheDocument();
    
    // Verify confidence level is displayed
    expect(screen.getByText(/90%/)).toBeInTheDocument();
    
    // Verify sentence-level analysis is displayed
    expect(screen.getByText('This is a test sentence.')).toBeInTheDocument();
    expect(screen.getByText('This sentence appears factual.')).toBeInTheDocument();

    // Verify NOT a white page - should have substantial content
    const analysisContent = screen.getByText('This is a test sentence.');
    expect(analysisContent).toBeInTheDocument();
    
    // Verify the page has rendered actual analysis data, not loading or error states
    expect(screen.queryByText('CASE FILE ACCESS DENIED')).not.toBeInTheDocument();
    expect(screen.queryByText('RETRIEVING CASE FILE')).not.toBeInTheDocument();
  });


});