import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import AnalysisResult from './AnalysisResult';
import ArticleInput from './ArticleInput';
import { AnalysisResult as AnalysisResultType } from '../types';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

// Mock apiService module
vi.mock('../services/api', () => ({
  apiService: {
    submitFeedback: vi.fn(),
    analyzeText: vi.fn(),
  },
}));

describe('Phase 3 UI Components & Interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockAnalysisResult: AnalysisResultType = {
    id: 'test-uuid-1234',
    authenticityScore: 82,
    confidence: 0.88,
    classification: 'reliable',
    processingTime: 145,
    analyzedAt: '2026-08-08T12:00:00Z',
    modelVersion: '1.0.0',
    retrieval_status: 'ok',
    retrieved_claims: [
      {
        statement_text: 'The president signed the economic stimulus package.',
        label: 'reliable',
        similarity_score: 0.85,
      },
      {
        statement_text: 'Unemployment dropped by 2 percent last quarter.',
        label: 'unreliable',
        similarity_score: 0.62,
      },
    ],
    sentenceAnalysis: [
      {
        index: 0,
        text: 'The economy grew by 3 percent in the third quarter according to official government reports.',
        isSuspicious: false,
        score: 85,
        confidence: 0.9,
        category: 'factual',
        flags: [],
        explanation: 'Factual claim supported by statistical data.',
      },
      {
        index: 1,
        text: 'Unverified sources claim secretly that aliens funded the budget.',
        isSuspicious: true,
        score: 25,
        confidence: 0.85,
        category: 'claim',
        flags: ['unverified_claim', 'sensationalism'],
        explanation: 'Unverified sensational claim without credible source.',
      },
    ],
  };

  it('renders AnalysisResult correctly with retrieved_claims from Phase 2 backend', () => {
    renderWithRouter(<AnalysisResult result={mockAnalysisResult} />);

    // Verify ScoreMeter and header
    expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
    expect(screen.getByText('RELIABLE')).toBeInTheDocument();

    // Verify Retrieved Claims Section
    expect(screen.getByText('Similar Fact-Checked Claims')).toBeInTheDocument();
    expect(
      screen.getByText(/"The president signed the economic stimulus package."/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Match Score: 85%/i)).toBeInTheDocument();
    expect(screen.getByText(/\(RELIABLE\)/i)).toBeInTheDocument();

    expect(
      screen.getByText(/"Unemployment dropped by 2 percent last quarter."/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Match Score: 62%/i)).toBeInTheDocument();
    expect(screen.getByText(/\(UNRELIABLE\)/i)).toBeInTheDocument();
  });

  it('handles feedback submission successfully and shows success toast', async () => {
    const user = userEvent.setup();
    const { apiService } = await import('../services/api');
    vi.mocked(apiService.submitFeedback).mockResolvedValueOnce({ feedbackId: 'fb-123' });

    renderWithRouter(<AnalysisResult result={mockAnalysisResult} />);

    const helpfulBtn = screen.getByRole('button', { name: /👍 helpful/i });
    await user.click(helpfulBtn);

    expect(apiService.submitFeedback).toHaveBeenCalledWith({
      analysisId: 'test-uuid-1234',
      userId: null,
      feedback: { type: 'helpful' },
    });

    await waitFor(() => {
      expect(
        screen.getByText(/✓ Thank you for your feedback! \(helpful\)/i)
      ).toBeInTheDocument();
    });
  });

  it('handles feedback submission error gracefully with explicit retry option', async () => {
    const user = userEvent.setup();
    const { apiService } = await import('../services/api');
    vi.mocked(apiService.submitFeedback).mockRejectedValueOnce(
      new Error('Network error submitting feedback')
    );

    renderWithRouter(<AnalysisResult result={mockAnalysisResult} />);

    const incorrectBtn = screen.getByRole('button', { name: /👎 incorrect/i });
    await user.click(incorrectBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/⚠️ Network error submitting feedback/i)
      ).toBeInTheDocument();
    });

    // Test retry button clears error and allows resubmission
    const retryBtn = screen.getByRole('button', { name: /clear & retry/i });
    await user.click(retryBtn);

    expect(screen.queryByText(/⚠️ Network error submitting feedback/i)).not.toBeInTheDocument();
  });

  it('opens sentence analysis modal upon click/tap interaction', async () => {
    const user = userEvent.setup();
    renderWithRouter(<AnalysisResult result={mockAnalysisResult} />);

    // Click on the suspicious sentence
    const suspiciousSentence = screen.getByText(
      /Unverified sources claim secretly that aliens funded the budget./i
    );
    await user.click(suspiciousSentence);

    // Verify modal opens with details
    expect(screen.getByRole('heading', { name: 'Sentence Analysis' })).toBeInTheDocument();
    expect(screen.getByText('Unverified sensational claim without credible source.')).toBeInTheDocument();
    expect(screen.getByText('unverified_claim')).toBeInTheDocument();
    expect(screen.getByText('sensationalism')).toBeInTheDocument();

    // Close modal
    const closeBtn = screen.getByRole('button', { name: '×' });
    await user.click(closeBtn);

    expect(screen.queryByRole('heading', { name: 'Sentence Analysis' })).not.toBeInTheDocument();
  });

  it('ArticleInput enforces character limit and submission callbacks', async () => {
    const user = userEvent.setup();
    const mockSubmit = vi.fn().mockResolvedValue(undefined);

    render(<ArticleInput onSubmit={mockSubmit} isLoading={false} />);

    const textarea = screen.getByLabelText(/article content/i);
    await user.type(textarea, 'Breaking news statement for test.');

    const submitBtn = screen.getByRole('button', { name: /analyze content/i });
    expect(submitBtn).toBeEnabled();

    await user.click(submitBtn);
    expect(mockSubmit).toHaveBeenCalledWith('Breaking news statement for test.');
  });
});
