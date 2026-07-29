// ScoreMeter component for displaying authenticity scores with color coding
// Based on design specifications from design.md

import React from 'react';
import { ScoreMeterProps } from '../types';

interface ScoreMeterData {
  label: string;
  color: string;
  backgroundColor: string;
  interpretation: string;
}

const ScoreMeter: React.FC<ScoreMeterProps> = ({ score, label, confidence }) => {
  const getScoreMeterData = (score: number): ScoreMeterData => {
    if (score >= 75) {
      return {
        label: label || 'Highly Reliable',
        color: '#22c55e',
        backgroundColor: '#dcfce7',
        interpretation: 'This content appears to be highly reliable based on our analysis.',
      };
    } else if (score >= 40) {
      return {
        label: label || 'Mixed Reliability', 
        color: '#f59e0b',
        backgroundColor: '#fef3c7',
        interpretation: 'This content has mixed reliability indicators. Review carefully.',
      };
    } else {
      return {
        label: label || 'Potentially Unreliable',
        color: '#ef4444',
        backgroundColor: '#fee2e2',
        interpretation: 'This content shows signs of potential unreliability.',
      };
    }
  };

  const meterData = getScoreMeterData(score);
  const percentage = Math.max(0, Math.min(100, score));

  return (
    <div className="score-meter">
      <div className="score-header">
        <h3 className="score-title">Authenticity Score</h3>
        <div className="score-values">
          <div className="score-value" style={{ color: meterData.color }}>
            {score}/100
          </div>
          {confidence !== undefined && (
            <div className="confidence-value">
              Confidence: {Math.round(confidence * 100)}%
            </div>
          )}
        </div>
      </div>
      
      <div className="meter-container">
        <div 
          className="meter-track"
          style={{
            backgroundColor: '#f1f5f9',
            height: '12px',
            borderRadius: '6px',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div 
            className="meter-fill"
            style={{
              width: `${percentage}%`,
              height: '100%',
              backgroundColor: meterData.color,
              borderRadius: '6px',
              transition: 'width 0.5s ease-in-out',
            }}
          />
        </div>
        
        <div className="meter-markers">
          <span className="marker" style={{ left: '40%' }}>40</span>
          <span className="marker" style={{ left: '75%' }}>75</span>
        </div>
      </div>

      <div 
        className="score-label"
        style={{
          backgroundColor: meterData.backgroundColor,
          color: meterData.color,
          padding: '0.5rem 1rem',
          borderRadius: '0.5rem',
          fontWeight: '600',
          textAlign: 'center',
          marginTop: '1rem',
        }}
      >
        {meterData.label}
      </div>

      <p className="score-interpretation">
        {meterData.interpretation}
      </p>

      <style>{`
        .score-meter {
          background: white;
          padding: 1.5rem;
          border-radius: 0.75rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          border: 1px solid #e2e8f0;
        }

        .score-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .score-values {
          text-align: right;
        }

        .score-title {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: #1e293b;
        }

        .score-value {
          font-size: 2rem;
          font-weight: 700;
        }

        .confidence-value {
          font-size: 0.875rem;
          color: #64748b;
          font-weight: 500;
          margin-top: 0.25rem;
        }

        .meter-container {
          position: relative;
          margin-bottom: 0.5rem;
        }

        .meter-markers {
          display: flex;
          justify-content: space-between;
          position: relative;
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #64748b;
        }

        .marker {
          position: absolute;
          transform: translateX(-50%);
          font-weight: 500;
        }

        .score-interpretation {
          margin: 1rem 0 0 0;
          color: #64748b;
          font-size: 0.875rem;
          line-height: 1.5;
          text-align: center;
        }
      `}</style>
    </div>
  );
};

export default ScoreMeter;