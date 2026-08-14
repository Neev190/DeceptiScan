import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import * as fc from 'fast-check';
import { AuthProvider } from '../context/AuthContext';
import AnalysisDetail from '../pages/AnalysisDetail';
import History from '../pages/History';
import Home from '../pages/Home';
import * as apiService from '../services/api';
import { AnalysisResult, AnalysisHistoryItem, PaginatedResponse } from '../types';

// Mock the API service
vi.mock('../services/api', () => ({
  apiService: {
    getAnalysis: vi.fn(),
    getHistoryItem: vi.fn(),
    getAnalysisHistory: vi.fn(),
    analyzeText: vi.fn(),
    getRecentAnalyses: vi.fn(),
  },
}));

describe('Navigation Preservation Property Tests', () => {
  const mockUser = {
    id: 'user123',
    email: 'test@example.com',
    username: 'testuser',
    createdAt: '2024-01-01T00:00:00Z',
  };

  const createMockAnalysisResult = (id: string, score?: number): AnalysisResult => ({
    id,
    authenticityScore: score ?? Math.floor(Math.random() * 100),
    classification: ['reliable', 'mixed', 'unreliable'][Math.floor(Math.random() * 3)] as 'reliable' | 'mixed' | 'unreliable',
    confidence: Math.random(),
    sentenceAnalysis: [
      {
        index: 0,
        text: `Analysis sentence for ${id}`,
        isSuspicious: Math.random() > 0.5,
        score: score ?? Math.floor(Math.random() * 100),
        confidence: Math.random(),
        category: 'factual',
        flags: [],
        explanation: 'Test explanation',
      },
    ],
    processingTime: 1500,
    analyzedAt: new Date().toISOString(),
    modelVersion: '1.0.0',
  });

  const renderWithProviders = (component: React.ReactElement, initialEntries?: string[]) => {
    const RouterComponent = initialEntries ? MemoryRouter : BrowserRouter;
    const routerProps = initialEntries ? { initialEntries } : {};

    return render(
      <RouterComponent {...routerProps}>
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
      </RouterComponent>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * **Validates: Requirements 3.1**
   * 
   * Property 2: Preservation - Direct URL Navigation Behavior
   * 
   * This test verifies that direct URL navigation to /analysis/{id} continues
   * to work correctly. This behavior MUST remain unchanged after the bug fix.
   * 
   * EXPECTED OUTCOME: Tests PASS (confirms baseline behavior to preserve)
   */
  describe('Property 2a: Direct URL Navigation Preservation', () => {
    it('should handle direct navigation to analysis URLs with various valid IDs', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate various UUID formats and analysis IDs
          fc.oneof(
            fc.uuid(),
            fc.hexaString({ minLength: 8, maxLength: 36 }),
            fc.string({ minLength: 6, maxLength: 20 }).map(s => s.replace(/[^a-zA-Z0-9-]/g, ''))
          ).filter(id => id.length >= 6),
          async (analysisId) => {
            const mockResult = createMockAnalysisResult(analysisId);
            vi.mocked(apiService.apiService.getAnalysis).mockResolvedValue(mockResult);
            vi.mocked(apiService.apiService.getHistoryItem).mockResolvedValue(mockResult);

            // Simulate direct URL navigation (e.g., typing URL or bookmark)
            renderWithProviders(
              <AnalysisDetail />, 
              [`/analysis/${analysisId}`]
            );

            // Verify the analysis loads correctly
            await waitFor(() => {
              expect(screen.queryByText('RETRIEVING CASE FILE')).not.toBeInTheDocument();
            });

            // Should display analysis content, not error or white page
            await waitFor(() => {
              const scoreElement = screen.getByText(`${mockResult.authenticityScore}/100`);
              expect(scoreElement).toBeInTheDocument();
            });

            // Should display classification
            expect(screen.getByText(new RegExp(mockResult.classification, 'i'))).toBeInTheDocument();

            // Should display sentence analysis
            expect(screen.getByText(`Analysis sentence for ${analysisId}`)).toBeInTheDocument();

            // Should NOT show error states
            expect(screen.queryByText('CASE FILE ACCESS DENIED')).not.toBeInTheDocument();
          }
        ),
        { numRuns: 10, timeout: 5000 }
      );
    });

    it('should handle direct URL navigation with proper error states for invalid IDs', async () => {
      const invalidId = 'invalid-analysis-id-404';
      
      vi.mocked(apiService.apiService.getAnalysis).mockRejectedValue({
        code: 'NOT_FOUND',
        message: 'Analysis not found',
        response: { status: 404 }
      });
      vi.mocked(apiService.apiService.getHistoryItem).mockRejectedValue({
        code: 'NOT_FOUND', 
        message: 'Analysis not found',
        response: { status: 404 }
      });

      renderWithProviders(
        <AnalysisDetail />, 
        [`/analysis/${invalidId}`]
      );

      // Should show proper error state, not white page
      await waitFor(() => {
        expect(screen.getByText('CASE FILE ACCESS DENIED')).toBeInTheDocument();
        expect(screen.getByText('Analysis not found')).toBeInTheDocument();
      });

      // Should provide navigation options
      expect(screen.getByText('NEW INVESTIGATION')).toBeInTheDocument();
      expect(screen.getByText('VIEW ARCHIVE')).toBeInTheDocument();
    });
  });

  /**
   * **Validates: Requirements 3.4**
   * 
   * Property 2b: Preservation - History Page Navigation Behavior
   * 
   * This test verifies that navigation from the dedicated history page continues
   * to work correctly. This behavior MUST remain unchanged after the bug fix.
   */
  describe('Property 2b: History Page Navigation Preservation', () => {
    it('should handle navigation from history page with various analysis items', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arrays of history items
          fc.array(
            fc.record({
              id: fc.uuid(),
              authenticityScore: fc.integer({ min: 0, max: 100 }),
              classification: fc.oneof(
                fc.constant('reliable' as const),
                fc.constant('mixed' as const), 
                fc.constant('unreliable' as const)
              ),
              createdAt: fc.date().map(d => d.toISOString()),
              title: fc.string({ minLength: 5, maxLength: 50 }),
              input_text: fc.string({ minLength: 10, maxLength: 200 })
            }),
            { minLength: 1, maxLength: 5 }
          ),
          async (historyItems) => {
            // Mock history page data
            const mockPaginatedResponse: PaginatedResponse<AnalysisHistoryItem> = {
              data: historyItems,
              pagination: {
                page: 1,
                limit: 10,
                total: historyItems.length,
                totalPages: 1
              }
            };
            
            vi.mocked(apiService.apiService.getAnalysisHistory).mockResolvedValue(mockPaginatedResponse);

            // Mock analysis detail fetching for each item
            historyItems.forEach(item => {
              const mockResult = createMockAnalysisResult(item.id, item.authenticityScore);
              vi.mocked(apiService.apiService.getAnalysis).mockResolvedValue(mockResult);
              vi.mocked(apiService.apiService.getHistoryItem).mockResolvedValue(mockResult);
            });

            // Render history page
            renderWithProviders(<History />);

            // Wait for history items to load
            await waitFor(() => {
              expect(screen.getByText('CASE ARCHIVE')).toBeInTheDocument();
            });

            // Verify history items are displayed
            for (const item of historyItems) {
              await waitFor(() => {
                expect(screen.getByText(item.title)).toBeInTheDocument();
              });
            }

            // Test navigation from history page to first item
            const firstItem = historyItems[0];
            const viewCaseLink = screen.getAllByText('VIEW CASE')[0];
            expect(viewCaseLink.closest('a')).toHaveAttribute('href', `/analysis/${firstItem.id}`);

            // This confirms the link structure is correct - actual navigation 
            // testing would require more complex setup, but the preservation
            // property is that history page links maintain proper hrefs
          }
        ),
        { numRuns: 5, timeout: 10000 }
      );
    });
  });

  /**
   * **Validates: Requirements 3.3**
   * 
   * Property 2c: Preservation - Fresh Analysis Result Viewing
   * 
   * This test verifies that viewing fresh analysis results immediately after
   * completion continues to work correctly.
   */
  describe('Property 2c: Fresh Analysis Result Viewing Preservation', () => {
    it('should handle fresh analysis results with various content types and scores', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            content: fc.string({ minLength: 10, maxLength: 500 }),
            authenticityScore: fc.integer({ min: 0, max: 100 }),
            classification: fc.oneof(
              fc.constant('reliable' as const),
              fc.constant('mixed' as const),
              fc.constant('unreliable' as const)
            ),
            confidence: fc.float({ min: 0.1, max: 1.0 })
          }),
          async (analysisData) => {
            const mockResult: AnalysisResult = {
              id: 'fresh-analysis-123',
              authenticityScore: analysisData.authenticityScore,
              classification: analysisData.classification,
              confidence: analysisData.confidence,
              sentenceAnalysis: [
                {
                  index: 0,
                  text: analysisData.content.substring(0, 100),
                  isSuspicious: analysisData.authenticityScore < 50,
                  score: analysisData.authenticityScore,
                  confidence: analysisData.confidence,
                  category: 'factual',
                  flags: [],
                  explanation: 'Fresh analysis explanation',
                }
              ],
              processingTime: 1500,
              analyzedAt: new Date().toISOString(),
              modelVersion: '1.0.0',
            };

            vi.mocked(apiService.apiService.analyzeText).mockResolvedValue(mockResult);
            vi.mocked(apiService.apiService.getRecentAnalyses).mockResolvedValue([]);

            // Render Home page and simulate fresh analysis
            renderWithProviders(<Home />);

            // Find and fill the analysis input
            const inputArea = screen.getByRole('textbox');
            await userEvent.type(inputArea, analysisData.content);

            // Submit analysis
            const analyzeButton = screen.getByText('INITIATE INVESTIGATION');
            await userEvent.click(analyzeButton);

            // Wait for analysis to complete and results to display
            await waitFor(() => {
              expect(screen.queryByText('ANALYZING EVIDENCE')).not.toBeInTheDocument();
            }, { timeout: 10000 });

            // Verify fresh analysis results are displayed correctly
            await waitFor(() => {
              expect(screen.getByText(`${analysisData.authenticityScore}/100`)).toBeInTheDocument();
            });

            expect(screen.getByText(new RegExp(analysisData.classification, 'i'))).toBeInTheDocument();
            expect(screen.getByText('Fresh analysis explanation')).toBeInTheDocument();

            // Should not show loading or error states
            expect(screen.queryByText('ANALYSIS FAILED')).not.toBeInTheDocument();
          }
        ),
        { numRuns: 8, timeout: 15000 }
      );
    });
  });

  /**
   * **Validates: Requirements 3.2**
   * 
   * Property 2d: Preservation - Other Home Page Navigation Elements
   * 
   * This test verifies that other navigation elements on the home page
   * continue to function without interference from the view case fix.
   */
  describe('Property 2d: Other Home Page Navigation Preservation', () => {
    it('should maintain proper navigation structure for non-Recent-Archival-Pulls elements', async () => {
      vi.mocked(apiService.apiService.getRecentAnalyses).mockResolvedValue([]);

      renderWithProviders(<Home />);

      // Wait for page to load
      await waitFor(() => {
        expect(screen.getByText('Recent Archival Pulls')).toBeInTheDocument();
      });

      // Verify login link works (for unauthenticated state)
      const AuthProviderUnauthenticated = ({ children }: { children: React.ReactNode }) => (
        <div data-testid="auth-provider">{children}</div>
      );

      const { rerender } = render(
        <BrowserRouter>
          <AuthProviderUnauthenticated>
            <Home />
          </AuthProviderUnauthenticated>
        </BrowserRouter>
      );

      // Re-render with unauthenticated state
      rerender(
        <BrowserRouter>
          <AuthProvider value={{
            isAuthenticated: false,
            user: null,
            token: null,
            login: vi.fn(),
            logout: vi.fn(),
            loading: false,
          }}>
            <Home />
          </AuthProvider>
        </BrowserRouter>
      );

      await waitFor(() => {
        const loginLink = screen.getByText('LOG IN TO SYSTEM');
        expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
      });

      // Verify main navigation elements are preserved
      expect(screen.getByText('RESTRICTED ACCESS')).toBeInTheDocument();
      
      // Verify analysis input area is still functional
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByText('INITIATE INVESTIGATION')).toBeInTheDocument();
    });
  });

  /**
   * **Validates: Requirements 3.1**
   * 
   * Property 2e: Preservation - Bookmark Access Patterns
   * 
   * This test verifies that bookmarked analysis URLs continue to work correctly.
   * Simulates the behavior of users accessing saved/bookmarked analysis links.
   */
  describe('Property 2e: Bookmark Access Preservation', () => {
    it('should handle bookmarked analysis URLs with proper authentication flow', async () => {
      const bookmarkedAnalysisId = 'bookmarked-analysis-456';
      const mockResult = createMockAnalysisResult(bookmarkedAnalysisId, 92);

      // Mock successful bookmark access
      vi.mocked(apiService.apiService.getAnalysis).mockResolvedValue(mockResult);
      vi.mocked(apiService.apiService.getHistoryItem).mockResolvedValue(mockResult);

      // Simulate bookmark navigation (direct URL with authenticated user)
      renderWithProviders(
        <AnalysisDetail />, 
        [`/analysis/${bookmarkedAnalysisId}`]
      );

      // Should load without issues
      await waitFor(() => {
        expect(screen.queryByText('RETRIEVING CASE FILE')).not.toBeInTheDocument();
      });

      // Should display bookmarked analysis content
      await waitFor(() => {
        expect(screen.getByText('92/100')).toBeInTheDocument();
        expect(screen.getByText(`Analysis sentence for ${bookmarkedAnalysisId}`)).toBeInTheDocument();
      });

      // Should show proper breadcrumb navigation
      expect(screen.getByText(/Case File #[A-Z0-9]+/)).toBeInTheDocument();
      
      // Should not show error states
      expect(screen.queryByText('CASE FILE ACCESS DENIED')).not.toBeInTheDocument();

      // Verify API was called with correct endpoint
      expect(apiService.apiService.getAnalysis).toHaveBeenCalledWith(bookmarkedAnalysisId);
    });

    it('should handle bookmark access with authentication errors gracefully', async () => {
      const bookmarkedAnalysisId = 'auth-error-analysis-789';

      // Mock authentication error
      vi.mocked(apiService.apiService.getAnalysis).mockRejectedValue({
        code: 'UNAUTHORIZED',
        message: 'Authentication required',
        response: { status: 401 }
      });
      vi.mocked(apiService.apiService.getHistoryItem).mockRejectedValue({
        code: 'UNAUTHORIZED', 
        message: 'Authentication required',
        response: { status: 401 }
      });

      renderWithProviders(
        <AnalysisDetail />, 
        [`/analysis/${bookmarkedAnalysisId}`]
      );

      // Should show proper error handling for auth issues
      await waitFor(() => {
        expect(screen.getByText('CASE FILE ACCESS DENIED')).toBeInTheDocument();
        expect(screen.getByText('Authentication required')).toBeInTheDocument();
      });

      // Should provide recovery options
      expect(screen.getByText('NEW INVESTIGATION')).toBeInTheDocument();
      expect(screen.getByText('VIEW ARCHIVE')).toBeInTheDocument();
    });
  });
});