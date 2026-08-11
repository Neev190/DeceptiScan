import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AnalysisResult from './AnalysisResult';
import { AnalysisResult as AnalysisResultType } from '../types';

const mockResultReliable: AnalysisResultType = {
  id: 'test-id-1',
  authenticityScore: 85,
  confidence: 0.92,
  classification: 'reliable',
  sentenceAnalysis: [
    {
      index: 0,
      text: 'The earth orbits around the sun.',
      isSuspicious: false,
      score: 95,
      confidence: 0.95,
      category: 'factual',
      flags: [],
      explanation: 'Established scientific fact.',
    },
  ],
  processingTime: 120,
  analyzedAt: '2026-07-31T12:00:00Z',
  modelVersion: 'distilbert-liar-v1',
};

const mockResultUnknown: AnalysisResultType = {
  id: 'test-id-2',
  authenticityScore: 50,
  confidence: 0.25,
  classification: 'unknown',
  warning: 'Low confidence in model prediction. Classification marked as unknown.',
  sentenceAnalysis: [],
  processingTime: 50,
  analyzedAt: '2026-07-31T12:00:00Z',
  modelVersion: 'distilbert-liar-v1',
};

describe('AnalysisResult Component', () => {
  it('renders analysis score and classification correctly', () => {
    render(<AnalysisResult result={mockResultReliable} />);
    expect(screen.getByText('85/100')).toBeInTheDocument();
    expect(screen.getByText('RELIABLE')).toBeInTheDocument();
    expect(screen.getByText('The earth orbits around the sun.')).toBeInTheDocument();
  });

  it('renders disclaimer warning when classification is unknown or warning exists', () => {
    render(<AnalysisResult result={mockResultUnknown} />);
    expect(screen.getByText(/Low confidence in model prediction/i)).toBeInTheDocument();
    expect(screen.getByText(/Disclaimer/i)).toBeInTheDocument();
  });

  it('allows clicking a sentence to open the sentence detail modal', () => {
    render(<AnalysisResult result={mockResultReliable} />);
    const sentenceEl = screen.getByText('The earth orbits around the sun.');
    fireEvent.click(sentenceEl);

    expect(screen.getByText('Sentence Analysis')).toBeInTheDocument();
    expect(screen.getByText('Established scientific fact.')).toBeInTheDocument();
  });

  describe('retrieved_claims rendering', () => {
    it('renders without crashing when retrieved_claims is null', () => {
      const resultWithNullClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: null,
      };
      render(<AnalysisResult result={resultWithNullClaims} />);
      expect(screen.getByText('85/100')).toBeInTheDocument();
    });

    it('hides similar claims section when retrieved_claims is null', () => {
      const resultWithNullClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: null,
      };
      render(<AnalysisResult result={resultWithNullClaims} />);
      expect(screen.getByText(/NO RELATED CASES ON FILE/i)).toBeInTheDocument();
    });

    it('renders without crashing when retrieved_claims is empty array', () => {
      const resultWithEmptyClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: [],
      };
      render(<AnalysisResult result={resultWithEmptyClaims} />);
      expect(screen.getByText('85/100')).toBeInTheDocument();
    });

    it('hides similar claims section when retrieved_claims is empty array', () => {
      const resultWithEmptyClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: [],
      };
      render(<AnalysisResult result={resultWithEmptyClaims} />);
      expect(screen.getByText(/NO RELATED CASES ON FILE/i)).toBeInTheDocument();
    });

    it('renders without crashing when retrieved_claims is populated', () => {
      const resultWithClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: [
          {
            statement_text: 'The moon landing happened in 1969.',
            label: 'true',
            similarity_score: 0.85,
          },
          {
            statement_text: 'Water boils at 100 degrees Celsius.',
            label: 'true',
            similarity_score: 0.72,
          },
        ],
      };
      render(<AnalysisResult result={resultWithClaims} />);
      expect(screen.getByText('85/100')).toBeInTheDocument();
    });

    it('shows similar claims section when retrieved_claims is populated', () => {
      const resultWithClaims: AnalysisResultType = {
        ...mockResultReliable,
        retrieved_claims: [
          {
            statement_text: 'The moon landing happened in 1969.',
            label: 'true',
            similarity_score: 0.85,
          },
          {
            statement_text: 'Water boils at 100 degrees Celsius.',
            label: 'true',
            similarity_score: 0.72,
          },
        ],
      };
      render(<AnalysisResult result={resultWithClaims} />);
      
      // Verify claims are rendered
      expect(screen.getByText(/The moon landing happened in 1969/i)).toBeInTheDocument();
      expect(screen.getByText(/Water boils at 100 degrees Celsius/i)).toBeInTheDocument();
      
      // Verify labels are rendered (two claims, both labeled TRUE)
      expect(screen.getAllByText(/\(TRUE\)/i)).toHaveLength(2);
      
      // Verify similarity scores are rendered
      expect(screen.getByText(/Match Score: 85%/i)).toBeInTheDocument();
      expect(screen.getByText(/Match Score: 72%/i)).toBeInTheDocument();
    });
  });
});
