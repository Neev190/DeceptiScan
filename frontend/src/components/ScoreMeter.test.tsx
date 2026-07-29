import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ScoreMeter from './ScoreMeter';

describe('ScoreMeter', () => {
  it('displays score value correctly', () => {
    render(<ScoreMeter score={85} label="Reliable" />);
    
    expect(screen.getByText('85/100')).toBeInTheDocument();
  });

  it('displays green styling for reliable scores (>= 75)', () => {
    render(<ScoreMeter score={85} label="Reliable" />);
    
    const scoreValue = screen.getByText('85/100');
    expect(scoreValue).toHaveStyle({ color: '#22c55e' });
    
    const label = screen.getByText('Reliable');
    expect(label).toBeInTheDocument();
  });

  it('displays yellow styling for mixed scores (40-74)', () => {
    render(<ScoreMeter score={55} label="Mixed" />);
    
    const scoreValue = screen.getByText('55/100');
    expect(scoreValue).toHaveStyle({ color: '#f59e0b' });
  });

  it('displays red styling for unreliable scores (< 40)', () => {
    render(<ScoreMeter score={25} label="Unreliable" />);
    
    const scoreValue = screen.getByText('25/100');
    expect(scoreValue).toHaveStyle({ color: '#ef4444' });
  });

  it('displays confidence level when provided', () => {
    render(<ScoreMeter score={75} label="Reliable" confidence={0.85} />);
    
    expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
  });

  it('does not display confidence when not provided', () => {
    render(<ScoreMeter score={75} label="Reliable" />);
    
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  it('handles edge case scores correctly', () => {
    // Test boundary values
    render(<ScoreMeter score={0} label="Unreliable" />);
    expect(screen.getByText('0/100')).toBeInTheDocument();
    
    render(<ScoreMeter score={100} label="Reliable" />);
    expect(screen.getByText('100/100')).toBeInTheDocument();
  });

  it('displays appropriate default labels based on score', () => {
    const { rerender } = render(<ScoreMeter score={85} label="" />);
    expect(screen.getByText('Highly Reliable')).toBeInTheDocument();
    
    rerender(<ScoreMeter score={55} label="" />);
    expect(screen.getByText('Mixed Reliability')).toBeInTheDocument();
    
    rerender(<ScoreMeter score={25} label="" />);
    expect(screen.getByText('Potentially Unreliable')).toBeInTheDocument();
  });

  it('shows proper meter fill width based on score', () => {
    render(<ScoreMeter score={60} label="Mixed" />);
    
    const meterFill = document.querySelector('.meter-fill');
    expect(meterFill).toHaveStyle({ width: '60%' });
  });

  it('displays threshold markers correctly', () => {
    render(<ScoreMeter score={50} label="Mixed" />);
    
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
  });
});