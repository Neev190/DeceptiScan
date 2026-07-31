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
});
